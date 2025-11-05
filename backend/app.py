"""
app.py — Legal Document Summarization + Retrieval-Augmented Generation (RAG)
Version: 3.1 | Polished & Optimized
"""

import os
import uuid
import datetime
import logging
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import spacy
import fitz

# -------------------- NLP Modules --------------------
from nlp_module.text_preprocessing import extract_entities, preprocess_text
from nlp_module.abstractive_summarization import AbstractiveSummarizer
from nlp_module.extractive_summarization import summarize as extractive_summarizer

# -------------------- RAG Engine --------------------
from rag_module.rag_engine import LegalRAG

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# -------------------- Initialize Models --------------------
nlp = spacy.load('en_core_web_sm')
rag_engine = LegalRAG()  # Global RAG engine instance
_abstractive_model = None
_analyzer_instance = None

# -------------------- Flask App Setup --------------------
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
#                  Utility & Lazy Load Functions
# ============================================================

def get_abstractive_model():
    """Lazy-load abstractive LexT5 model only when required."""
    global _abstractive_model
    if _abstractive_model is None:
        logger.info("Loading abstractive model (LexT5)...")
        _abstractive_model = AbstractiveSummarizer()
        logger.info("✓ Abstractive model loaded successfully.")
    return _abstractive_model


# ============================================================
#                     Core Analyzer Class
# ============================================================

class ForensicDocumentAnalyzer:
    def __init__(self):
        """Initialize analyzer with custom stopword set."""
        self.stop_words = nlp.Defaults.stop_words
        self.keep_terms = {
            'evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'forensic',
            'examination', 'report', 'case', 'specimen', 'conclusion'
        }
        for term in self.keep_terms:
            self.stop_words.discard(term)

    # --------------------------------------------------------
    #                   Utility Methods
    # --------------------------------------------------------

    def is_corrupted(self, text):
        """Detect text corruption or scanned PDFs."""
        words = text.split()
        if len(words) < 10:
            return False

        # Many single letters
        if sum(1 for w in words if len(w) == 1 and w.isalpha()) > len(words) * 0.3:
            return True

        # Consecutive repeats
        consecutive = sum(1 for i in range(len(words) - 1) if words[i] == words[i + 1])
        if consecutive > len(words) * 0.2:
            return True

        # Repetitive noise patterns
        if ' re re re re ' in text.lower() or ' a a a a ' in text.lower():
            return True

        return False

    def clean_text_for_abstractive(self, text):
        """Clean special characters before LexT5 input."""
        text = re.sub(r'<[^>]+>', '', text)
        replacements = {
            '&amp;': 'and', '&lt;': 'less than', '&gt;': 'greater than',
            '&quot;': '"', '&apos;': "'", '\xa0': ' ', '\u200b': '', '\t': ' ', '\n': ' '
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r'[<>{}[\]\\|]', '', text)
        return re.sub(r'\s+', ' ', text).strip()

    # --------------------------------------------------------
    #                 Document Analysis Pipeline
    # --------------------------------------------------------

    def extract_text_from_pdf(self, pdf_path):
        """Extract plain text from a PDF file."""
        try:
            with fitz.open(pdf_path) as doc:
                text = ''.join([page.get_text() for page in doc])
            logger.info(f"Extracted {len(text)} characters from PDF.")
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""

    def extract_metadata(self, text):
        """Extract metadata using spaCy entity recognition."""
        try:
            entities = extract_entities(text)
            return {
                'dates': entities.get('DATE', [])[:3],
                'case_number': entities.get('CASE_ID', ['Unknown'])[0],
                'people': entities.get('PERSON', [])[:5],
                'organizations': entities.get('ORG', [])[:3],
                'locations': entities.get('GPE', [])[:3]
            }
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {"error": str(e)}

    def extract_forensic_findings(self, text):
        """Extract key legal or forensic findings."""
        findings, keywords = [], [
            'conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
            'match', 'consistent with', 'evidence indicates', 'analysis shows',
            'examination revealed', 'tested positive', 'comparison', 'probability',
            'held', 'decided', 'ruled', 'judgment', 'issue'
        ]
        for sent in nlp(text).sents:
            if any(k in sent.text.lower() for k in keywords):
                findings.append(sent.text)
            if len(findings) >= 7:
                break
        return findings

    # --------------------------------------------------------
    #                    Main Analyzer
    # --------------------------------------------------------

    def analyze_document(self, file_path, summary_length=6, extraction_ratio=0.5, mode='extractive'):
        try:
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "No text extracted from PDF."}

            if self.is_corrupted(text):
                return {"error": "PDF extraction failed - file may be scanned or corrupted."}

            preprocessed_text = preprocess_text(text)
            metadata = self.extract_metadata(text)

            # Step 1: Extractive summary
            extractive_summary = extractive_summarizer(
                text, method='hybrid', compression_ratio=extraction_ratio
            )
            final_summary = extractive_summary
            abstractive_summary = None

            # Step 2: Optional abstractive refinement
            if mode == 'hybrid':
                try:
                    cleaned_text = self.clean_text_for_abstractive(extractive_summary)
                    abstractive_model = get_abstractive_model()
                    abstractive_summary = abstractive_model.abstractive_summarize(
                        cleaned_text, num_sentences=summary_length, compression_ratio=0.6
                    )
                    final_summary = abstractive_summary
                except Exception as e:
                    logger.error(f"⚠️ Abstractive summarization failed: {e}")

            # Step 3: Extract findings & stats
            findings = self.extract_forensic_findings(text)
            doc = nlp(text)
            stats = {
                'word_count': len([t for t in doc if not t.is_punct and not t.is_space]),
                'sentence_count': len(list(doc.sents)),
                'final_summary_length': len(final_summary.split()),
                'compression_ratio': f"{(len(final_summary.split()) / len(text.split())) * 100:.1f}%"
            }

            # Step 4: Add to RAG Index
            logger.info("📘 Adding document to RAG index...")
            rag_engine.add_document(text, filename=os.path.basename(file_path))

            # Step 5: Return response
            return {
                'metadata': metadata,
                'summary': final_summary,
                'extractive_summary': extractive_summary,
                'abstractive_summary': abstractive_summary,
                'key_findings': findings,
                'statistics': stats,
                'mode': mode
            }

        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {"error": str(e)}


# ============================================================
#                       API Routes
# ============================================================

@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple test route."""
    return jsonify({
        'status': 'API running ✅',
        'version': '3.1',
        'features': ['summarization', 'RAG query']
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_document_endpoint():
    """Handle PDF upload and trigger analysis."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    try:
        file.save(file_path)
        analyzer = get_analyzer()
        result = analyzer.analyze_document(file_path, mode=request.form.get('mode', 'hybrid'))
        result['document'] = {
            'filename': file.filename,
            'id': filename.split('.')[0],
            'analyzed_at': datetime.datetime.now().isoformat()
        }
        return jsonify(result)
    except Exception as e:
        logger.exception("Error in /api/analyze:")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.route('/api/query', methods=['POST'])
def query_document():
    """Perform semantic retrieval from indexed legal documents."""
    data = request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query text is required'}), 400

    try:
        results = rag_engine.search(query)
        answer = rag_engine.generate_answer(query, results)
        return jsonify({
            'query': query,
            'answer': answer,
            'context': [r['content'] for r in results]
        })
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
#                        Entry Point
# ============================================================

def get_analyzer():
    """Singleton pattern for analyzer."""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ForensicDocumentAnalyzer()
    return _analyzer_instance


if __name__ == '__main__':
    logger.info("🚀 Starting Legal Summarization + RAG API Server...")
    app.run(debug=True, port=5000, use_reloader=False)
