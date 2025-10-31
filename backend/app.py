import os
import uuid
import datetime
import logging
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
import fitz

from nlp_module.text_preprocessing import extract_entities, preprocess_text
from nlp_module.abstractive_summarization import AbstractiveSummarizer
from nlp_module.extractive_summarization import summarize as extractive_summarizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Global instances for lazy loading
_abstractive_model = None
_analyzer_instance = None

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_abstractive_model():
    """Lazy load abstractive model only when needed (hybrid mode)."""
    global _abstractive_model
    if _abstractive_model is None:
        logger.info("Loading abstractive model (LexT5)...")
        _abstractive_model = AbstractiveSummarizer()
        logger.info("✓ Abstractive model loaded")
    return _abstractive_model


class ForensicDocumentAnalyzer:
    def __init__(self):
        self.stop_words = nlp.Defaults.stop_words
        self.keep_terms = {
            'evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'forensic',
            'examination', 'report', 'case', 'specimen', 'conclusion'
        }
        for term in self.keep_terms:
            self.stop_words.discard(term)

    def is_corrupted(self, text):
        """
        Detect actual corruption, not legal terminology.
        Returns True if text appears to be garbled/corrupted.
        """
        words = text.split()
        if len(words) < 10:
            return False
        
        # Check for excessive single-letter words (a a a a)
        single_letters = sum(1 for w in words if len(w) == 1 and w.isalpha())
        if single_letters > len(words) * 0.3:
            logger.warning(f"Corruption detected: {single_letters}/{len(words)} single-letter words")
            return True
        
        # Check for same word repeated many times consecutively
        consecutive_repeats = 0
        for i in range(len(words) - 1):
            if words[i] == words[i+1] and len(words[i]) > 1:
                consecutive_repeats += 1
        if consecutive_repeats > len(words) * 0.2:
            logger.warning(f"Corruption detected: {consecutive_repeats} consecutive repeats")
            return True
        
        # Check for nonsense patterns like "re re re re"
        if ' re re re re ' in text.lower():
            logger.warning("Corruption detected: 're re re re' pattern")
            return True
        
        # Check for "a a a a" pattern
        if ' a a a a ' in text.lower():
            logger.warning("Corruption detected: 'a a a a' pattern")
            return True
            
        return False

    def clean_text_for_abstractive(self, text):
        """
        🆕 NEW: Clean text to prevent LexT5 hallucination on special symbols.
        Removes XML-like tags and problematic characters that confuse the model.
        """
        # Remove XML-like tags (e.g., <PV>, <LG>, <IS>, <HD>)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace HTML entities
        replacements = {
            '&amp;': 'and',
            '&lt;': 'less than',
            '&gt;': 'greater than',
            '&quot;': '"',
            '&apos;': "'",
            '\xa0': ' ',       # Non-breaking space
            '\u200b': '',      # Zero-width space
            '\t': ' ',         # Tab
            '\n': ' ',         # Newline
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove other problematic symbols that cause hallucination
        text = re.sub(r'[<>{}[\]\\|]', '', text)
        
        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        logger.info(f"Text cleaned: {len(text)} chars")
        return text

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF using PyMuPDF (better for legal docs)."""
        try:
            doc = fitz.open(pdf_path)
            text = ''
            for page in doc:
                text += page.get_text()
            doc.close()
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""

    def extract_metadata(self, text):
        """Extract metadata using entity extraction."""
        try:
            entities = extract_entities(text)
            return {
                'dates': entities.get('DATE', [])[:3],
                'case_number': entities.get('CASE_ID', ['Unknown'])[0] if entities.get('CASE_ID') else None,
                'people': entities.get('PERSON', [])[:5],
                'organizations': entities.get('ORG', [])[:3],
                'locations': entities.get('GPE', [])[:3]
            }
        except Exception as e:
            logger.error(f"Metadata extraction: {e}")
            return {"error": str(e)}

    def extract_forensic_findings(self, text):
        """Extract key forensic findings from the text."""
        try:
            findings = []
            sentences = [sent.text for sent in nlp(text).sents]
            keywords = [
                'conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
                'match', 'consistent with', 'evidence indicates', 'analysis shows',
                'examination revealed', 'tested positive', 'comparison', 'probability',
                'held', 'decided', 'ruled', 'judgment', 'question', 'issue'  # Legal keywords
            ]
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    findings.append(sentence)
                if len(findings) >= 7:  # Increased from 5
                    break
            return findings[:7]
        except Exception as e:
            logger.error(f"Forensic findings extraction: {e}")
            return []

    def analyze_document(self, file_path, summary_length=5, extraction_ratio=0.5, mode='extractive'):
        """
        🆕 UPDATED: Main analysis pipeline with mode selection.
        
        Parameters:
            file_path (str): Path to PDF file
            summary_length (int): Target number of sentences for abstractive
            extraction_ratio (float): Percentage of sentences to extract (0.3-0.7)
            mode (str): 'extractive' (fast, accurate) or 'hybrid' (refined with LexT5)
        """
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "Could not extract text from PDF"}
            
            logger.info(f"RAW PDF TEXT (first 300 chars): {text[:300]}")
            logger.info(f"RAW PDF TEXT (word count): {len(text.split())} words")
            logger.info(f"🔧 Processing mode: {mode.upper()}")

            # Check for corruption in raw PDF text
            if self.is_corrupted(text):
                logger.error("PDF extraction appears corrupted")
                return {"error": "PDF extraction failed - file may be scanned or corrupted"}

            # Minimal preprocessing
            preprocessed_text = preprocess_text(text)
            logger.info(f"PREPROCESSED (word count): {len(preprocessed_text.split())} words")

            # Extract metadata
            metadata = self.extract_metadata(text)
            
            # Step 1: EXTRACTIVE SUMMARIZATION (always performed)
            extractive_summary = extractive_summarizer(
                text, 
                method='hybrid',            # TextRank (60%) + TF-IDF (40%)
                compression_ratio=extraction_ratio, 
                top_n=None
            )

            logger.info(f"EXTRACTIVE SUMMARY (first 300 chars): {extractive_summary[:300]}")
            logger.info(f"✓ Extractive: {len(extractive_summary.split())} words")

            # Check extractive output quality
            if self.is_corrupted(extractive_summary):
                logger.error("Extractive summary quality check failed")
                return {"error": "Text extraction failed - poor quality extractive output"}
            
            # Step 2: ABSTRACTIVE SUMMARIZATION (only if mode='hybrid')
            abstractive_summary = None
            final_summary = extractive_summary  # Default to extractive
            
            if mode == 'hybrid':
                try:
                    logger.info("🔄 Running abstractive refinement...")
                    
                    # 🆕 Clean text before feeding to LexT5
                    cleaned_extractive = self.clean_text_for_abstractive(extractive_summary)
                    
                    # Get abstractive model (lazy loading)
                    abstractive_model = get_abstractive_model()
                    
                    # Generate abstractive summary
                    abstractive_summary = abstractive_model.abstractive_summarize(
                        cleaned_extractive, 
                        num_sentences=summary_length, 
                        compression_ratio=0.6
                    )
                    
                    logger.info(f"✓ Abstractive: {len(abstractive_summary.split())} words")
                    
                    # Use abstractive as final summary
                    final_summary = abstractive_summary
                    
                except Exception as e:
                    logger.error(f"⚠ Abstractive failed: {e}, falling back to extractive")
                    # Fallback to extractive if abstractive fails
                    abstractive_summary = None
                    final_summary = extractive_summary
            else:
                logger.info("📝 Extractive-only mode, skipping abstractive")
            
            # Extract key findings
            findings = self.extract_forensic_findings(text)

            # Calculate statistics
            doc = nlp(text)
            word_count = len([t for t in doc if not t.is_punct and not t.is_space])
            sentence_count = len(list(doc.sents))
            ext_summary_word_count = len(extractive_summary.split())
            final_summary_word_count = len(final_summary.split())

            return {
                'metadata': metadata,
                'summary': final_summary,                          # Final summary (extractive or abstractive)
                'extractive_summary': extractive_summary,          # Always available
                'abstractive_summary': abstractive_summary,        # None if mode='extractive'
                'key_findings': findings,
                'mode': mode,                                      # 🆕 Mode used
                'statistics': {
                    'word_count': word_count,
                    'sentence_count': sentence_count,
                    'extractive_summary_length': ext_summary_word_count,
                    'final_summary_length': final_summary_word_count,
                    'abstractive_summary_length': len(abstractive_summary.split()) if abstractive_summary else 0,
                    'extraction_ratio': extraction_ratio,
                    'compression_ratio': f"{(final_summary_word_count/word_count)*100:.1f}%"
                }
            }
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {"error": str(e)}


def get_analyzer():
    """Lazy singleton to load analyzer only once."""
    global _analyzer_instance
    if _analyzer_instance is None:
        logger.info("Initializing ForensicDocumentAnalyzer...")
        _analyzer_instance = ForensicDocumentAnalyzer()
        logger.info("✓ Analyzer ready")
    return _analyzer_instance


@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple endpoint to test if API is working."""
    return jsonify({
        'status': 'API is working',
        'version': '2.0',
        'modes': ['extractive', 'hybrid']
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_document_endpoint():
    """🆕 UPDATED: Analyze document with mode selection."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        file.save(file_path)
        logger.info(f"📄 File saved: {file.filename}")

        # Get parameters
        summary_detail = request.form.get('summary_detail', 'standard')
        summary_length = {
            'brief': 4,
            'standard': 6,
            'detailed': 8,
            'comprehensive': 10
        }.get(summary_detail, 6)
        
        extraction_ratio = float(request.form.get('extraction_ratio', 0.5))
        extraction_ratio = max(0.3, min(0.7, extraction_ratio))
        
        # 🆕 NEW: Get mode parameter
        mode = request.form.get('mode', 'extractive')  # Default to extractive
        
        # Validate mode
        if mode not in ['extractive', 'hybrid']:
            mode = 'extractive'
        
        target_language = request.form.get('target_language', 'original')
        
        logger.info(f"⚙️ Config: {file.filename}, Mode: {mode}, Detail: {summary_detail}, Ratio: {extraction_ratio*100}%")

        # Analyze document
        analyzer = get_analyzer()
        result = analyzer.analyze_document(
            file_path, 
            summary_length, 
            extraction_ratio,
            mode=mode  # 🆕 Pass mode
        )

        if 'error' in result:
            logger.error(f"❌ Analysis error: {result['error']}")
            return jsonify(result), 500

        # Add document info
        result['document'] = {
            'filename': file.filename,
            'analyzed_at': datetime.datetime.now().isoformat(),
            'id': filename.split('.')[0]
        }

        logger.info(f"✅ Completed: Mode={mode}, Final={result['statistics']['final_summary_length']}w")
        return jsonify(result)
        
    except Exception as e:
        logger.exception(f"💥 Exception: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info("🗑️ Temp file removed")
            except Exception as e:
                logger.error(f"Error removing file: {e}")


if __name__ == '__main__':
    logger.info("🚀 Starting Legal Document Summarization API...")
    logger.info("📝 Modes: extractive (TextRank+TF-IDF) | hybrid (+ LexT5)")
    app.run(debug=True, port=5000, use_reloader=False)
