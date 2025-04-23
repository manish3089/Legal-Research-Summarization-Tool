# backend/app.py
import os
import uuid
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import spacy
from heapq import nlargest
import numpy as np
import re
from nlp_module.extractive_summarization import summarize  # <<-- Your hybrid summarization module

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)
CORS(app)

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
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''.join(page.extract_text() for page in reader.pages)
        return text

    def extract_metadata(self, text):
        metadata = {}
        date_pattern = r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|...|Dec)[a-z]* \d{1,2},? \d{4})\b'
        metadata['dates'] = re.findall(date_pattern, text)[:3]

        case_pattern = r'\b(?:Case|Reference|File)(?:\s+(?:No|Number|#|\s))?\s*:?\s*([A-Z0-9][-A-Z0-9]+)\b'
        match = re.findall(case_pattern, text, re.IGNORECASE)
        if match:
            metadata['case_number'] = match[0]

        doc = nlp(text[:10000])
        metadata['people'] = list({ent.text for ent in doc.ents if ent.label_ == 'PERSON' and len(ent.text) > 3})[:5]
        metadata['organizations'] = list({ent.text for ent in doc.ents if ent.label_ == 'ORG'})[:3]
        metadata['locations'] = list({ent.text for ent in doc.ents if ent.label_ in {'GPE', 'LOC'}})[:3]

        return metadata

    def sentence_similarity(self, sent1, sent2):
        doc1 = nlp(sent1)
        doc2 = nlp(sent2)
        tokens1 = [t.text.lower() for t in doc1 if not t.is_stop and not t.is_punct]
        tokens2 = [t.text.lower() for t in doc2 if not t.is_stop and not t.is_punct]
        all_words = list(set(tokens1 + tokens2))
        if not all_words:
            return 0
        vec1 = [tokens1.count(w) for w in all_words]
        vec2 = [tokens2.count(w) for w in all_words]
        dot = sum(x * y for x, y in zip(vec1, vec2))
        norm1 = sum(x**2 for x in vec1)**0.5
        norm2 = sum(x**2 for x in vec2)**0.5
        return dot / (norm1 * norm2) if norm1 and norm2 else 0

    def build_similarity_matrix(self, sentences):
        n = len(sentences)
        sim_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    sim_matrix[i][j] = self.sentence_similarity(sentences[i], sentences[j])
        return sim_matrix

    def extract_forensic_findings(self, text):
        findings = []
        sentences = [sent.text for sent in nlp(text).sents]
        keywords = ['conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
                    'match', 'consistent with', 'evidence indicates', 'analysis shows',
                    'examination revealed', 'tested positive', 'comparison', 'probability']
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                findings.append(sentence)
        return findings[:5]

    def analyze_document(self, file_path, summary_length=5):
        text = self.extract_text_from_pdf(file_path)
        metadata = self.extract_metadata(text)
        summary = summarize(text, method=self.summary_method, top_n=summary_length)
        findings = self.extract_forensic_findings(text)
        word_count = len([t for t in nlp(text) if not t.is_punct and not t.is_space])
        sentence_count = len(list(nlp(text).sents))
        return {
            'metadata': metadata,
            'summary': summary,
            'key_findings': findings,
            'statistics': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'summary_length': len(nlp(summary))
            }
        }

analyzer = ForensicDocumentAnalyzer()

@app.route('/api/analyze', methods=['POST'])
def analyze_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.pdf'):
        filename = str(uuid.uuid4()) + '.pdf'
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        summary_length = int(request.form.get('summary_length', 5))
        summary_method = request.form.get('summary_method', 'hybrid')
        analyzer.summary_method = summary_method

        try:
            result = analyzer.analyze_document(file_path, summary_length)
            result['document'] = {
                'filename': file.filename,
                'analyzed_at': datetime.datetime.now().isoformat(),
                'id': filename.split('.')[0]
            }
            os.remove(file_path)
            return jsonify(result)
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'File must be a PDF'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
