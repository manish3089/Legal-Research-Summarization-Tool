# backend/app.py
import os
import uuid
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np
from heapq import nlargest
import re

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

app = Flask(_name_)
CORS(app)  # Enable CORS for frontend integration

# Create upload directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class ForensicDocumentAnalyzer:
    def _init_(self):
        self.stop_words = set(stopwords.words('english'))
        # Forensic-specific terms that should not be filtered out as stopwords
        self.keep_terms = {'evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'forensic', 
                          'examination', 'report', 'case', 'specimen', 'conclusion'}
        for term in self.keep_terms:
            if term in self.stop_words:
                self.stop_words.remove(term)

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
        return text

    def extract_metadata(self, text):
        """Extract key metadata from the document"""
        metadata = {}
        
        # Look for dates
        date_pattern = r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b'
        dates = re.findall(date_pattern, text)
        if dates:
            metadata['dates'] = dates[:3]  # Limit to first 3 dates
            
        # Look for case numbers
        case_pattern = r'\b(?:Case|Reference|File)(?:\s+(?:No|Number|#|\s))?\s*:?\s*([A-Z0-9][-A-Z0-9]+)\b'
        case_matches = re.findall(case_pattern, text, re.IGNORECASE)
        if case_matches:
            metadata['case_number'] = case_matches[0]
            
        # Extract entities using spaCy
        doc = nlp(text[:10000])  # Limit to first 10000 chars for performance
        
        people = set()
        organizations = set()
        locations = set()
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON' and len(ent.text) > 3:
                people.add(ent.text)
            elif ent.label_ == 'ORG':
                organizations.add(ent.text)
            elif ent.label_ == 'GPE' or ent.label_ == 'LOC':
                locations.add(ent.text)
                
        if people:
            metadata['people'] = list(people)[:5]  # Limit to 5 people
        if organizations:
            metadata['organizations'] = list(organizations)[:3]
        if locations:
            metadata['locations'] = list(locations)[:3]
            
        return metadata

    def sentence_similarity(self, sent1, sent2):
        """Calculate similarity between two sentences"""
        sent1 = [word.lower() for word in word_tokenize(sent1) if word.lower() not in self.stop_words]
        sent2 = [word.lower() for word in word_tokenize(sent2) if word.lower() not in self.stop_words]
        
        all_words = list(set(sent1 + sent2))
        
        if not all_words:  # If no significant words remain
            return 0
        
        vector1 = [0] * len(all_words)
        vector2 = [0] * len(all_words)
        
        for w in sent1:
            vector1[all_words.index(w)] += 1
        
        for w in sent2:
            vector2[all_words.index(w)] += 1
        
        # Calculate cosine similarity
        sum_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
        magnitude1 = sum(v ** 2 for v in vector1) ** 0.5
        magnitude2 = sum(v ** 2 for v in vector2) ** 0.5
        
        if magnitude1 * magnitude2 == 0:
            return 0
        
        return sum_product / (magnitude1 * magnitude2)

    def build_similarity_matrix(self, sentences):
        """Create similarity matrix among all sentences"""
        n = len(sentences)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    similarity_matrix[i][j] = self.sentence_similarity(sentences[i], sentences[j])
        
        return similarity_matrix

    def extract_forensic_findings(self, text):
        """Extract sentences that likely contain forensic findings"""
        findings = []
        sentences = sent_tokenize(text)
        
        # Keywords related to forensic findings
        finding_keywords = ['conclude', 'conclusion', 'finding', 'results', 'determine', 'identified',
                           'match', 'consistent with', 'evidence indicates', 'analysis shows',
                           'examination revealed', 'tested positive', 'comparison', 'probability']
        
        for sentence in sentences:
            lowercase_sent = sentence.lower()
            if any(keyword in lowercase_sent for keyword in finding_keywords):
                findings.append(sentence)
                
        return findings[:5]  # Return top 5 findings

    def generate_summary(self, text, num_sentences=5):
        """Generate summary using TextRank algorithm with forensic focus"""
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        # Handle case where there are fewer sentences than requested
        if len(sentences) <= num_sentences:
            return ' '.join(sentences)
        
        # Build similarity matrix
        similarity_matrix = self.build_similarity_matrix(sentences)
        
        # Calculate sentence scores
        scores = np.array(similarity_matrix.sum(axis=1))
        
        # Boost score for sentences with forensic terminology
        forensic_terms = ['evidence', 'analysis', 'sample', 'dna', 'fingerprint', 'examination', 
                         'forensic', 'match', 'conclude', 'finding', 'results']
                         
        for i, sentence in enumerate(sentences):
            lowercase_sent = sentence.lower()
            
            # Boost score for sentences containing forensic terms
            for term in forensic_terms:
                if term in lowercase_sent:
                    scores[i] *= 1.2
            
            # Boost score for sentences appearing in introduction or conclusion sections
            if i < len(sentences) * 0.2 or i > len(sentences) * 0.8:
                scores[i] *= 1.1
                
        # Get top ranked sentences
        top_indices = nlargest(num_sentences, range(len(scores)), scores._getitem_)
        top_indices.sort()  # Maintain original order
        
        summary = ' '.join([sentences[i] for i in top_indices])
        return summary

    def analyze_document(self, file_path, summary_length=5):
        """Main method to analyze forensic document"""
        text = self.extract_text_from_pdf(file_path)
        metadata = self.extract_metadata(text)
        summary = self.generate_summary(text, summary_length)
        findings = self.extract_forensic_findings(text)
        
        word_count = len(word_tokenize(text))
        sentence_count = len(sent_tokenize(text))
        
        return {
            'metadata': metadata,
            'summary': summary,
            'key_findings': findings,
            'statistics': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'summary_length': len(word_tokenize(summary))
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
        # Create unique filename
        filename = str(uuid.uuid4()) + '.pdf'
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Get summary length from request or use default
        summary_length = int(request.form.get('summary_length', 5))
        
        try:
            # Analyze document
            result = analyzer.analyze_document(file_path, summary_length)
            
            # Add timestamp and document info
            result['document'] = {
                'filename': file.filename,
                'analyzed_at': datetime.datetime.now().isoformat(),
                'id': filename.split('.')[0]
            }
            
            # Clean up file
            os.remove(file_path)
            
            return jsonify(result)
        except Exception as e:
            # Clean up file if error occurs
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File must be a PDF'}), 400

if _name_ == '_main_':
    app.run(debug=True, port=5000)
