# backend/app.py
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
CORS(app, resources={r"/api/*": {"origins": "http://127.0.0.1:5500/frontend/user_interface.html"}})

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class ForensicDocumentAnalyzer:
    def __init__(self):
        self.stop_words = nlp.Defaults.stop_words
        self.keep_terms = {'evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'forensic', 
                          'examination', 'report', 'case', 'specimen', 'conclusion'}
        for term in self.keep_terms:
            self.stop_words.discard(term)
        self.summary_method = 'hybrid'

    def extract_text_from_pdf(self, pdf_path):
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''.join(page.extract_text() for page in reader.pages)
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_metadata(self, text):
        try:
            # Use the improved entity extraction from our module
            entities = extract_entities(text)
            
            metadata = {}
            metadata['dates'] = entities.get('DATE', [])[:3]
            metadata['case_number'] = entities.get('CASE_ID', ['Unknown'])[0] if entities.get('CASE_ID') else None
            metadata['people'] = entities.get('PERSON', [])[:5]
            metadata['organizations'] = entities.get('ORG', [])[:3]
            metadata['locations'] = entities.get('GPE', [])[:3]
            
            return metadata
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {"error": str(e)}

    def extract_forensic_findings(self, text):
        try:
            findings = []
            sentences = [sent.text for sent in nlp(text).sents]
            keywords = ['conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
                        'match', 'consistent with', 'evidence indicates', 'analysis shows',
                        'examination revealed', 'tested positive', 'comparison', 'probability']
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    findings.append(sentence)
            
            return findings[:5]
        except Exception as e:
            print(f"Error extracting findings: {e}")
            return []

    def analyze_document(self, file_path, summary_length=5):
        try:
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "Could not extract text from PDF"}
                
            # Clean text to improve analysis quality
            preprocessed_text = preprocess_text(text)
            
            metadata = self.extract_metadata(text)
            # Use our improved summarization module
            summary = summarize(text, method=self.summary_method, top_n=summary_length)
            findings = self.extract_forensic_findings(text)
            
            # Get statistics
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
            print(f"Error analyzing document: {e}")
            return {"error": str(e)}

analyzer = ForensicDocumentAnalyzer()

@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple endpoint to test if API is working"""
    return jsonify({'status': 'API is working'})

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and file.filename.endswith('.pdf'):
        try:
            filename = str(uuid.uuid4()) + '.pdf'
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            summary_length = int(request.form.get('summary_length', 5))
            target_language = request.form.get('target_language', 'original')
            analyzer.summary_method = request.form.get('summary_method', 'hybrid')

            result = analyzer.analyze_document(file_path, summary_length)
            
            # Check if there was an error in analysis
            if 'error' in result:
                return jsonify(result), 500
                
            result['document'] = {
                'filename': file.filename,
                'analyzed_at': datetime.datetime.now().isoformat(),
                'id': filename.split('.')[0]
            }
            
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return jsonify(result)
            
        except Exception as e:
            # Ensure file cleanup on error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File must be a PDF'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)# backend/app.py
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
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class ForensicDocumentAnalyzer:
    def __init__(self):
        self.stop_words = nlp.Defaults.stop_words
        self.keep_terms = {'evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'forensic', 
                          'examination', 'report', 'case', 'specimen', 'conclusion'}
        for term in self.keep_terms:
            self.stop_words.discard(term)
        self.summary_method = 'hybrid'

    def extract_text_from_pdf(self, pdf_path):
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''.join(page.extract_text() for page in reader.pages)
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""

    def extract_metadata(self, text):
        try:
            # Use the improved entity extraction from our module
            entities = extract_entities(text)
            
            metadata = {}
            metadata['dates'] = entities.get('DATE', [])[:3]
            metadata['case_number'] = entities.get('CASE_ID', ['Unknown'])[0] if entities.get('CASE_ID') else None
            metadata['people'] = entities.get('PERSON', [])[:5]
            metadata['organizations'] = entities.get('ORG', [])[:3]
            metadata['locations'] = entities.get('GPE', [])[:3]
            
            return metadata
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {"error": str(e)}

    def extract_forensic_findings(self, text):
        try:
            findings = []
            sentences = [sent.text for sent in nlp(text).sents]
            keywords = ['conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
                        'match', 'consistent with', 'evidence indicates', 'analysis shows',
                        'examination revealed', 'tested positive', 'comparison', 'probability']
            
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in keywords):
                    findings.append(sentence)
            
            return findings[:5]
        except Exception as e:
            print(f"Error extracting findings: {e}")
            return []

    def analyze_document(self, file_path, summary_length=5):
        try:
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "Could not extract text from PDF"}
                
            # Clean text to improve analysis quality
            preprocessed_text = preprocess_text(text)
            
            metadata = self.extract_metadata(text)
            # Use our improved summarization module
            summary = summarize(text, method=self.summary_method, top_n=summary_length)
            findings = self.extract_forensic_findings(text)
            
            # Get statistics
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
            print(f"Error analyzing document: {e}")
            return {"error": str(e)}

analyzer = ForensicDocumentAnalyzer()

@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple endpoint to test if API is working"""
    return jsonify({'status': 'API is working'})

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and file.filename.endswith('.pdf'):
        try:
            filename = str(uuid.uuid4()) + '.pdf'
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            summary_length = int(request.form.get('summary_length', 5))
            target_language = request.form.get('target_language', 'original')
            analyzer.summary_method = request.form.get('summary_method', 'hybrid')

            result = analyzer.analyze_document(file_path, summary_length)
            
            # Check if there was an error in analysis
            if 'error' in result:
                return jsonify(result), 500
                
            result['document'] = {
                'filename': file.filename,
                'analyzed_at': datetime.datetime.now().isoformat(),
                'id': filename.split('.')[0]
            }
            
            # Clean up the uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return jsonify(result)
            
        except Exception as e:
            # Ensure file cleanup on error
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File must be a PDF'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
