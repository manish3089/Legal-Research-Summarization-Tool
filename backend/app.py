import os
import uuid
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import spacy

from nlp_module.extractive_summarization import summarize
from nlp_module.text_preprocessing import extract_entities, preprocess_text

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class ForensicDocumentAnalyzer:
    def __init__(self):
        self.stop_words = nlp.Defaults.stop_words
        self.keep_terms = {
            'evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'forensic',
            'examination', 'report', 'case', 'specimen', 'conclusion'
        }
        for term in self.keep_terms:
            self.stop_words.discard(term)
        self.summary_method = 'hybrid'

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''.join(page.extract_text() or '' for page in reader.pages)
            return text
        except Exception as e:
            print(f"[ERROR] PDF extraction: {e}")
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
            print(f"[ERROR] Metadata extraction: {e}")
            return {"error": str(e)}

    def extract_forensic_findings(self, text):
        """Extract key forensic findings from the text."""
        try:
            findings = []
            sentences = [sent.text for sent in nlp(text).sents]
            keywords = [
                'conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
                'match', 'consistent with', 'evidence indicates', 'analysis shows',
                'examination revealed', 'tested positive', 'comparison', 'probability'
            ]
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    findings.append(sentence)
            return findings[:5]
        except Exception as e:
            print(f"[ERROR] Forensic findings extraction: {e}")
            return []

    def analyze_document(self, file_path, summary_length=5):
        """Main analysis pipeline for a forensic document."""
        try:
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "Could not extract text from PDF"}

            preprocessed_text = preprocess_text(text)
            metadata = self.extract_metadata(text)
            summary = summarize(text, method=self.summary_method, top_n=summary_length)
            findings = self.extract_forensic_findings(text)

            doc = nlp(text)
            word_count = len([t for t in doc if not t.is_punct and not t.is_space])
            sentence_count = len(list(doc.sents))
            summary_word_count = len(nlp(summary))

            return {
                'metadata': metadata,
                'summary': summary,
                'key_findings': findings,
                'statistics': {
                    'word_count': word_count,
                    'sentence_count': sentence_count,
                    'summary_length': summary_word_count
                }
            }
        except Exception as e:
            print(f"[ERROR] Document analysis: {e}")
            return {"error": str(e)}

analyzer = ForensicDocumentAnalyzer()

@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple endpoint to test if API is working."""
    return jsonify({'status': 'API is working'})

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        print("[ERROR] No file part in request")
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if not file.filename:
        print("[ERROR] No selected file")
        return jsonify({'error': 'No selected file'}), 400

    if not file.filename.lower().endswith('.pdf'):
        print("[ERROR] File must be a PDF")
        return jsonify({'error': 'File must be a PDF'}), 400

    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    try:
        file.save(file_path)
        print(f"[INFO] File saved: {file_path}")

        summary_detail = request.form.get('summary_detail', 'auto')
        summary_length = {
            'brief': 3,
            'standard': 5,
            'detailed': 8,
            'comprehensive': 12
        }.get(summary_detail, 5)

        target_language = request.form.get('target_language', 'original')
        print(f"[INFO] Processing file: {file.filename}")
        print(f"[INFO] Summary detail: {summary_detail}, Length: {summary_length}")
        print(f"[INFO] Target language: {target_language}")

        result = analyzer.analyze_document(file_path, summary_length)

        if 'error' in result:
            print(f"[ERROR] Analysis error: {result['error']}")
            return jsonify(result), 500

        result['document'] = {
            'filename': file.filename,
            'analyzed_at': datetime.datetime.now().isoformat(),
            'id': filename.split('.')[0]
        }

        print(f"[INFO] Analysis completed. Summary length: {result['statistics']['summary_length']} words")
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] Exception in analyze_document: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up the uploaded file
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[INFO] Temporary file removed: {file_path}")
            except Exception as e:
                print(f"[ERROR] Error removing file: {e}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)