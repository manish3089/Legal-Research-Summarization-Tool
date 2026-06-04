import threading
import time
import os
import uuid
import logging
import re

from flask import Flask, request as flask_request, jsonify
from flask_cors import CORS
import spacy
import fitz

from nlp_module.text_preprocessing import extract_entities, preprocess_text
from nlp_module.abstractive_summarization import AbstractiveSummarizer
from nlp_module.extractive_summarization import summarize as extractive_summarizer
from rag_module.rag_engine import LegalRAG


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

flask_app = Flask(__name__)
CORS(flask_app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

nlp = spacy.load('en_core_web_sm')
rag_engine = LegalRAG()

_abstractive_model = None
_analyzer_instance = None


def get_abstractive_model():
    global _abstractive_model
    if _abstractive_model is None:
        logger.info("Loading abstractive model (LexT5)...")
        _abstractive_model = AbstractiveSummarizer()
        logger.info("Abstractive model loaded.")
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
        words = text.split()
        if len(words) < 10:
            return False
        if sum(1 for w in words if len(w) == 1 and w.isalpha()) > len(words) * 0.3:
            return True
        consecutive = sum(1 for i in range(len(words) - 1) if words[i] == words[i + 1])
        if consecutive > len(words) * 0.2:
            return True
        if ' re re re re ' in text.lower() or ' a a a a ' in text.lower():
            return True
        return False

    def clean_text_for_abstractive(self, text):
        text = re.sub(r'<[^>]+>', '', text)
        replacements = {
            '&amp;': 'and', '&lt;': 'less than', '&gt;': 'greater than',
            '&quot;': '"'  , '&apos;': "'", '\xa0': ' ', '\u200b': '',
            '\t': ' ', '\n': ' '
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r'[<>{}[\]\\|]', '', text)
        return re.sub(r'\s+', ' ', text).strip()

    def extract_text_from_pdf(self, pdf_path):
        try:
            with fitz.open(pdf_path) as doc:
                text = ''.join([page.get_text() for page in doc])
            text = self._clean_extracted_text(text)
            logger.info(f"Extracted {len(text)} characters from PDF.")
            return text
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return ""

    def _clean_extracted_text(self, text):
        text = re.sub(r'\.{3,}', ' ', text)
        text = re.sub(r'-{2,}', ' ', text)
        text = re.sub(r'_{2,}', ' ', text)
        text = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])([A-Z])', r'\1 \2', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) < 10:
                continue
            alphanum_count = sum(c.isalnum() or c.isspace() for c in line)
            if alphanum_count / len(line) > 0.6:
                cleaned_lines.append(line)
        return '\n'.join(cleaned_lines).strip()

    def extract_metadata(self, text):
        try:
            entities = extract_entities(text)
            dates     = entities.get('DATE', [])
            case_ids  = entities.get('CASE_ID', [])
            people    = entities.get('PERSON', [])
            orgs      = entities.get('ORG', [])
            locations = entities.get('GPE', [])
            return {
                'dates':         dates[:3]    if dates    else [],
                'case_number':   case_ids[0]  if case_ids else 'Unknown',
                'people':        people[:5]   if people   else [],
                'organizations': orgs[:3]     if orgs     else [],
                'locations':     locations[:3] if locations else []
            }
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {'dates': [], 'case_number': 'Unknown', 'people': [],
                    'organizations': [], 'locations': [], 'error': str(e)}

    def extract_forensic_findings(self, text):
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

    def analyze_document(self, file_path, summary_length=6, extraction_ratio=0.5, mode='extractive'):
        try:
            text = self.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "No text extracted from PDF."}
            if self.is_corrupted(text):
                return {"error": "PDF extraction failed - file may be scanned or corrupted."}

            preprocess_text(text)
            metadata = self.extract_metadata(text)

            extractive_summary = extractive_summarizer(
                text, method='hybrid', compression_ratio=extraction_ratio
            )
            final_summary = extractive_summary
            abstractive_summary = None

            if mode == 'hybrid':
                try:
                    logger.info("Starting abstractive refinement...")
                    cleaned_text = self.clean_text_for_abstractive(extractive_summary)
                    abstractive_model = get_abstractive_model()
                    words = cleaned_text.split()
                    if len(words) > 500:
                        cleaned_text = ' '.join(words[:500])
                    abstractive_summary = abstractive_model.abstractive_summarize(
                        cleaned_text, num_sentences=summary_length, compression_ratio=0.6
                    )
                    final_summary = abstractive_summary
                    logger.info("Abstractive refinement complete.")
                except Exception as e:
                    logger.error(f"Abstractive summarization failed: {e}")

            findings = self.extract_forensic_findings(text)
            doc = nlp(text)
            stats = {
                'word_count':            len([t for t in doc if not t.is_punct and not t.is_space]),
                'sentence_count':        len(list(doc.sents)),
                'final_summary_length':  len(final_summary.split()),
                'compression_ratio':     f"{(len(final_summary.split()) / len(text.split())) * 100:.1f}%"
            }

            logger.info("Adding document to RAG index...")
            try:
                success = rag_engine.add_document(text, filename=os.path.basename(file_path))
                if not success:
                    logger.error("Failed to add document to RAG index.")
            except Exception as rag_err:
                logger.error(f"RAG indexing error: {rag_err}")

            return {
                'metadata':           metadata,
                'summary':            final_summary,
                'extractive_summary': extractive_summary,
                'abstractive_summary':abstractive_summary,
                'key_findings':       findings,
                'statistics':         stats,
                'mode':               mode
            }
        except Exception as e:
            logger.error(f"Document analysis error: {e}")
            return {"error": str(e)}


def get_analyzer():
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ForensicDocumentAnalyzer()
    return _analyzer_instance


# ── Routes ────────────────────────────────────────────────────────────────────

@flask_app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({'status': 'API running', 'version': '3.1',
                    'features': ['summarization', 'RAG query']})


@flask_app.route('/api/analyze', methods=['POST'])
def analyze_document_endpoint():
    if 'file' not in flask_request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = flask_request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400
    filename  = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    import datetime as _dt
    try:
        file.save(file_path)
        analyzer = get_analyzer()
        result   = analyzer.analyze_document(
            file_path,
            mode=flask_request.form.get('mode', 'hybrid'),
            extraction_ratio=float(flask_request.form.get('extraction_ratio', 0.5))
        )
        result['document'] = {
            'filename':    file.filename,
            'id':          filename.split('.')[0],
            'analyzed_at': _dt.datetime.now().isoformat()
        }
        return jsonify(result)
    except Exception as e:
        logger.exception("Error in /api/analyze:")
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@flask_app.route('/api/query', methods=['POST'])
def query_document():
    data  = flask_request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'Query text is required'}), 400
    try:
        results = rag_engine.search(query)
        answer  = rag_engine.generate_answer(query, results)
        return jsonify({'query': query, 'answer': answer,
                        'context': [r['content'] for r in results]})
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return jsonify({'error': str(e)}), 500


# ── Background thread launcher ────────────────────────────────────────────────

def _run_flask():
    logger.info("Flask API starting on http://127.0.0.1:5000")
    flask_app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


def _start_flask_once():
    """
    Launch Flask in a daemon thread the first time this module loads.
    Uses a /tmp flag file so Streamlit's rerun loop does not spawn duplicate threads.
    """
    flag = '/tmp/_lexai_flask_started'
    if not os.path.exists(flag):
        try:
            open(flag, 'w').close()
        except Exception:
            pass
        t = threading.Thread(target=_run_flask, daemon=True, name='flask-backend')
        t.start()
        time.sleep(1.5)   # allow Flask to bind before Streamlit renders


_start_flask_once()

import streamlit as st
import requests
import datetime

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title="LexAI — Legal Document Intelligence",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------
# CUSTOM CSS — Editorial Legal Dark Theme
# Typefaces: Playfair Display (headings) + IBM Plex Mono (data) + DM Sans (body)
# Palette: Near-black canvas, aged parchment accents, deep amber highlight
# -----------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,800;1,600&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

/* === RESET & BASE === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .stApp {
    background-color: #0e0d0b !important;
    color: #d9cfc0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* === MASTHEAD === */
.lex-masthead {
    border-bottom: 1px solid #2a2620;
    padding: 28px 56px 24px;
    display: flex;
    align-items: baseline;
    gap: 20px;
    background: #0e0d0b;
}
.lex-wordmark {
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #e8ddc8;
    line-height: 1;
}
.lex-wordmark span {
    color: #c8922a;
}
.lex-tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #5a5040;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-left: 2px solid #2a2620;
    padding-left: 16px;
    line-height: 1.6;
}
.lex-date {
    margin-left: auto;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    color: #3d3628;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* === LAYOUT SHELL === */
.lex-shell {
    display: grid;
    grid-template-columns: 260px 1fr;
    min-height: calc(100vh - 77px);
}

/* === SIDEBAR === */
.lex-sidebar {
    background: #0b0a08;
    border-right: 1px solid #1e1c18;
    padding: 40px 28px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.sidebar-section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    color: #3d3628;
    text-transform: uppercase;
    margin-bottom: 12px;
    margin-top: 24px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e1c18;
}
.sidebar-section-label:first-child { margin-top: 0; }

/* === MAIN CONTENT === */
.lex-main {
    padding: 48px 56px;
    background: #0e0d0b;
}

/* === SECTION HEADERS === */
.section-rule {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 28px;
}
.section-rule-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: #e8ddc8;
    white-space: nowrap;
}
.section-rule-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, #2a2620, transparent);
}

/* === UPLOAD ZONE === */
.upload-zone {
    border: 1px solid #2a2620;
    border-radius: 4px;
    padding: 40px;
    text-align: center;
    background: #0b0a08;
    transition: border-color 0.2s;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
}
.upload-zone::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(to right, transparent, #c8922a40, transparent);
}

/* === CONTROLS ROW === */
.controls-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
}

/* === STREAMLIT WIDGET OVERRIDES === */
div[data-testid="stFileUploader"] {
    background: #0b0a08 !important;
    border: 1px dashed #2e2b24 !important;
    border-radius: 4px !important;
    padding: 32px !important;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #c8922a !important;
}
div[data-testid="stFileUploader"] label {
    color: #7a6e5e !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
}
div[data-testid="stFileUploader"] button {
    background: transparent !important;
    border: 1px solid #2e2b24 !important;
    color: #8a7e6e !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    border-radius: 3px !important;
    transition: all 0.2s !important;
}
div[data-testid="stFileUploader"] button:hover {
    border-color: #c8922a !important;
    color: #c8922a !important;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background: #0b0a08 !important;
    border: 1px solid #2a2620 !important;
    border-radius: 3px !important;
    color: #c5b99a !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}
div[data-baseweb="select"] > div:hover,
div[data-baseweb="select"] > div:focus-within {
    border-color: #c8922a !important;
    box-shadow: none !important;
}

/* Slider */
div[data-testid="stSlider"] > div > div > div > div {
    background: #c8922a !important;
}
div[data-testid="stSlider"] > div > div > div {
    background: #2a2620 !important;
}

/* Text Input */
div[data-testid="stTextInput"] input {
    background: #0b0a08 !important;
    border: 1px solid #2a2620 !important;
    border-radius: 3px !important;
    color: #c5b99a !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 12px 16px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #c8922a !important;
    box-shadow: 0 0 0 2px #c8922a1a !important;
}

/* Labels */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextInput"] label {
    color: #7a6e5e !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
}

/* Primary button */
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button {
    background: #c8922a !important;
    border: none !important;
    color: #0e0d0b !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    padding: 14px 28px !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #d9a23d !important;
    box-shadow: 0 4px 24px #c8922a30 !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0) !important;
}

/* Radio navigation */
div[data-testid="stRadio"] {
    margin-bottom: 0 !important;
}
div[data-testid="stRadio"] > div {
    display: flex !important;
    gap: 0 !important;
    background: #0b0a08 !important;
    border: 1px solid #1e1c18 !important;
    border-radius: 3px !important;
    padding: 3px !important;
}
div[data-testid="stRadio"] label {
    flex: 1 !important;
    text-align: center !important;
    padding: 10px 16px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #5a5040 !important;
    border-radius: 2px !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #1e1c18 !important;
    color: #e8ddc8 !important;
}

/* Spinner */
div[data-testid="stSpinner"] p {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    color: #c8922a !important;
    letter-spacing: 0.08em !important;
}

/* Alert boxes */
div[data-testid="stAlert"] {
    border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem !important;
}
div[data-testid="stAlert"][data-type="success"] {
    background: #0d1a0f !important;
    border: 1px solid #1f4025 !important;
    color: #6abf7b !important;
}
div[data-testid="stAlert"][data-type="error"] {
    background: #1a0d0d !important;
    border: 1px solid #401f1f !important;
    color: #bf6a6a !important;
}

/* === RESULT CARDS === */
.lex-card {
    border: 1px solid #1e1c18;
    border-radius: 3px;
    padding: 24px 28px;
    margin-bottom: 16px;
    background: #0b0a08;
    position: relative;
}
.lex-card-accent {
    border-left: 3px solid #c8922a;
}
.lex-card-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    color: #c8922a;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.lex-card-body {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    line-height: 1.75;
    color: #c5b99a;
}

/* Summary card */
.lex-summary {
    border: 1px solid #2a2620;
    border-radius: 3px;
    padding: 32px;
    background: #0b0a08;
    margin-bottom: 32px;
    position: relative;
}
.lex-summary::before {
    content: '§';
    position: absolute;
    top: 28px; right: 28px;
    font-family: 'Playfair Display', serif;
    font-size: 2rem;
    color: #1e1c18;
}
.lex-summary-text {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    line-height: 1.85;
    color: #c5b99a;
}

/* Stats grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 32px;
}
.stat-cell {
    border: 1px solid #1e1c18;
    border-radius: 3px;
    padding: 18px 20px;
    background: #0b0a08;
    text-align: center;
}
.stat-value {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    color: #e8ddc8;
    display: block;
    line-height: 1;
    margin-bottom: 6px;
}
.stat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem;
    color: #3d3628;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

/* Findings */
.finding-row {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 16px 0;
    border-bottom: 1px solid #15140f;
}
.finding-row:last-child { border-bottom: none; }
.finding-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    color: #c8922a;
    min-width: 24px;
    padding-top: 3px;
}
.finding-text {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.875rem;
    line-height: 1.7;
    color: #a89e8c;
}

/* Meta grid */
.meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}
.meta-item {
    padding: 16px 20px;
    background: #0b0a08;
    border: 1px solid #1a1810;
    border-radius: 3px;
}
.meta-key {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.58rem;
    color: #3d3628;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 8px;
    display: block;
}
.meta-val {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.85rem;
    color: #9a8e7c;
}

/* Query answer */
.answer-block {
    background: #0b0a08;
    border: 1px solid #2a2620;
    border-top: 2px solid #c8922a;
    border-radius: 0 0 3px 3px;
    padding: 32px;
    margin-bottom: 28px;
}
.answer-text {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    line-height: 1.85;
    color: #c5b99a;
}

.context-item {
    border: 1px solid #1a1810;
    border-radius: 3px;
    padding: 20px 24px;
    margin-bottom: 10px;
    background: #0b0a08;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    line-height: 1.7;
    color: #7a6e5e;
    position: relative;
}
.context-item::before {
    content: '"';
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    color: #1e1c18;
    position: absolute;
    top: 6px; left: 14px;
    line-height: 1;
}
.context-item .ctx-text {
    padding-left: 28px;
}

/* Dividers */
.lex-divider {
    height: 1px;
    background: linear-gradient(to right, #1e1c18, transparent);
    margin: 36px 0;
}

/* Status badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 2px;
    margin-bottom: 24px;
}
.status-ok {
    background: #0d1a0f;
    color: #4a9a58;
    border: 1px solid #1f4025;
}

/* No-content state */
.empty-state {
    padding: 80px 40px;
    text-align: center;
    border: 1px dashed #1e1c18;
    border-radius: 4px;
}
.empty-state-icon {
    font-size: 2.5rem;
    margin-bottom: 16px;
    opacity: 0.3;
}
.empty-state-text {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #3d3628;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Column labels */
.col-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem;
    color: #5a5040;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


now = datetime.datetime.now().strftime("%d %b %Y  ·  %H:%M")
st.markdown(f"""
<div class="lex-masthead">
    <div class="lex-wordmark">Lex<span>AI</span></div>
    <div class="lex-tagline">Legal Document Intelligence<br>RAG · NLP · Forensic Analysis</div>
    <div class="lex-date">{now}</div>
</div>
""", unsafe_allow_html=True)


left_col, right_col = st.columns([1.1, 3.5], gap="large")

with left_col:
    st.markdown("""
    <div style="padding: 32px 0 8px;">
        <div class="col-label">Module</div>
    </div>
    """, unsafe_allow_html=True)

    tab = st.radio(
        "Module",
        ["Document Analysis", "Ask Questions (RAG)"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="col-label" style="margin-top:32px;margin-bottom:8px;">About</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'DM Sans',sans-serif;font-size:0.78rem;line-height:1.8;color:#4a4034;">
    LexAI processes legal and forensic documents using a Retrieval-Augmented Generation pipeline, extractive summarisation via TextRank, and optional abstractive refinement via LexT5.
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="col-label" style="margin-top:32px;margin-bottom:8px;">Stack</div>', unsafe_allow_html=True)
    for s in ["spaCy NER", "PyMuPDF", "TextRank", "LexT5", "FAISS/RAG"]:
        st.markdown(f"""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.62rem;color:#3d3628;letter-spacing:0.08em;
        padding:6px 10px;background:#0b0a08;border:1px solid #1a1810;border-radius:2px;margin-bottom:5px;">
        {s}
        </div>
        """, unsafe_allow_html=True)


with right_col:

    if tab == "Document Analysis":

        st.markdown("""
        <div class="section-rule">
            <span class="section-rule-title">Document Analysis</span>
            <div class="section-rule-line"></div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            label_visibility="collapsed",
            help="Select a legal or forensic PDF document"
        )

        if uploaded_file:
            st.markdown(f"""
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;color:#6a5e4a;
            letter-spacing:0.08em;padding:8px 12px;background:#0b0a08;border:1px solid #1e1c18;
            border-radius:2px;margin:8px 0 20px;">
            ▸ {uploaded_file.name} &nbsp;·&nbsp; {uploaded_file.size / 1024:.1f} KB
            </div>
            """, unsafe_allow_html=True)

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            mode = st.selectbox(
                "Summarization Mode",
                options=["extractive", "hybrid"],
                format_func=lambda x: "Extractive  (Fast)" if x == "extractive" else "Hybrid  (LexT5 Refined)",
            )
        with c2:
            extraction_ratio = st.slider(
                "Extraction Ratio",
                min_value=30, max_value=70, value=50, step=5,
                format="%d%%"
            ) / 100

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        if st.button("Run Analysis", use_container_width=True):
            if not uploaded_file:
                st.error("Please upload a PDF document before running analysis.")
            else:
                with st.spinner("Extracting and analysing document…"):
                    try:
                        response = requests.post(
                            "http://127.0.0.1:5000/api/analyze",
                            files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                            data={"mode": mode, "extraction_ratio": extraction_ratio},
                            timeout=300,
                        )

                        if response.status_code == 200:
                            result = response.json()

                            # ── Status
                            mode_label = "HYBRID · LexT5" if mode == "hybrid" else "EXTRACTIVE · TextRank"
                            st.markdown(f"""
                            <div class="status-badge status-ok">
                                ● Analysis complete &nbsp;·&nbsp; {mode_label}
                            </div>
                            """, unsafe_allow_html=True)

                            # ── Statistics
                            stats = result.get("statistics", {})
                            if stats:
                                wc  = stats.get("word_count", "—")
                                sc  = stats.get("sentence_count", "—")
                                sl  = stats.get("final_summary_length", "—")
                                cr  = stats.get("compression_ratio", "—")
                                st.markdown(f"""
                                <div class="stats-grid">
                                    <div class="stat-cell">
                                        <span class="stat-value">{wc}</span>
                                        <span class="stat-label">Words</span>
                                    </div>
                                    <div class="stat-cell">
                                        <span class="stat-value">{sc}</span>
                                        <span class="stat-label">Sentences</span>
                                    </div>
                                    <div class="stat-cell">
                                        <span class="stat-value">{sl}</span>
                                        <span class="stat-label">Summary Tokens</span>
                                    </div>
                                    <div class="stat-cell">
                                        <span class="stat-value">{cr}</span>
                                        <span class="stat-label">Compression</span>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

                            # ── Summary
                            summary = result.get("summary", "No summary generated.")
                            st.markdown("""
                            <div class="section-rule" style="margin-bottom:16px;">
                                <span class="section-rule-title" style="font-size:1rem;">Summary</span>
                                <div class="section-rule-line"></div>
                            </div>
                            """, unsafe_allow_html=True)
                            st.markdown(f"""
                            <div class="lex-summary">
                                <div class="lex-summary-text">{summary}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            # ── Key Findings
                            findings = result.get("key_findings", [])
                            if findings:
                                st.markdown("""
                                <div class="section-rule" style="margin-bottom:16px;">
                                    <span class="section-rule-title" style="font-size:1rem;">Key Findings</span>
                                    <div class="section-rule-line"></div>
                                </div>
                                <div class="lex-card">
                                """, unsafe_allow_html=True)
                                rows = ""
                                for i, f in enumerate(findings, 1):
                                    rows += f"""
                                    <div class="finding-row">
                                        <span class="finding-num">{i:02d}</span>
                                        <span class="finding-text">{f}</span>
                                    </div>"""
                                st.markdown(rows + "</div>", unsafe_allow_html=True)

                            # ── Metadata
                            metadata = result.get("metadata", {})
                            if metadata:
                                st.markdown("""
                                <div class="section-rule" style="margin-top:28px;margin-bottom:16px;">
                                    <span class="section-rule-title" style="font-size:1rem;">Extracted Metadata</span>
                                    <div class="section-rule-line"></div>
                                </div>
                                <div class="meta-grid">
                                """, unsafe_allow_html=True)
                                cells = ""
                                for k, v in metadata.items():
                                    if isinstance(v, list):
                                        display = ", ".join(v) if v else "—"
                                    else:
                                        display = str(v) if v else "—"
                                    cells += f"""
                                    <div class="meta-item">
                                        <span class="meta-key">{k.replace('_',' ')}</span>
                                        <span class="meta-val">{display}</span>
                                    </div>"""
                                st.markdown(cells + "</div>", unsafe_allow_html=True)

                        else:
                            try:
                                err_msg = response.json().get("error", response.text)
                            except Exception:
                                err_msg = response.text
                            st.error(f"Server error {response.status_code}: {err_msg}")

                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend. Ensure the Flask server is running on port 5000.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

        else:
            if not uploaded_file:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">⚖</div>
                    <div class="empty-state-text">Upload a PDF to begin analysis</div>
                </div>
                """, unsafe_allow_html=True)

    # ============================
    # TAB 2: RAG QUERY
    # ============================
    elif tab == "Ask Questions (RAG)":

        st.markdown("""
        <div class="section-rule">
            <span class="section-rule-title">Ask Questions (RAG)</span>
            <div class="section-rule-line"></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-family:'DM Sans',sans-serif;font-size:0.82rem;color:#4a4034;
        line-height:1.7;margin-bottom:24px;">
        Query documents that have been indexed during the current session. Analyse a document first to populate the retrieval index.
        </div>
        """, unsafe_allow_html=True)

        query = st.text_input(
            "Legal Question",
            placeholder="e.g. What were the court's findings on the admissibility of evidence?",
            label_visibility="collapsed",
        )

        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

        if st.button("Retrieve Answer", use_container_width=True):
            if not query.strip():
                st.error("Please enter a question.")
            else:
                with st.spinner("Searching index and generating answer…"):
                    try:
                        response = requests.post(
                            "http://127.0.0.1:5000/api/query",
                            json={"query": query},
                            timeout=120,
                        )

                        if response.status_code == 200:
                            result = response.json()

                            st.markdown("""
                            <div class="status-badge status-ok">● Response generated</div>
                            """, unsafe_allow_html=True)

                            # ── Answer
                            answer = result.get("answer", "No answer found.")
                            st.markdown(f"""
                            <div class="lex-card-label" style="margin-bottom:4px;">Answer</div>
                            <div class="answer-block">
                                <div class="answer-text">{answer}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            # ── Context passages
                            ctx_list = result.get("context", [])
                            if ctx_list:
                                st.markdown("""
                                <div class="section-rule" style="margin-bottom:16px;">
                                    <span class="section-rule-title" style="font-size:1rem;">Source Passages</span>
                                    <div class="section-rule-line"></div>
                                </div>
                                """, unsafe_allow_html=True)
                                for passage in ctx_list:
                                    # Truncate very long passages for readability
                                    display = passage[:600] + ("…" if len(passage) > 600 else "")
                                    st.markdown(f"""
                                    <div class="context-item">
                                        <div class="ctx-text">{display}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                        else:
                            try:
                                err_msg = response.json().get("error", response.text)
                            except Exception:
                                err_msg = response.text
                            st.error(f"Server error {response.status_code}: {err_msg}")

                    except requests.exceptions.ConnectionError:
                        st.error("Cannot reach backend. Ensure the Flask server is running on port 5000.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")

        else:
            if not query:
                st.markdown("""
                <div class="empty-state">
                    <div class="empty-state-icon">🔍</div>
                    <div class="empty-state-text">Enter a question to query indexed documents</div>
                </div>
                """, unsafe_allow_html=True)

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("""
<div style="
    margin-top: 60px;
    padding: 24px 56px;
    border-top: 1px solid #1a1810;
    display: flex;
    justify-content: space-between;
    align-items: center;
">
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2e2820;letter-spacing:0.1em;text-transform:uppercase;">
        LexAI © 2025
    </span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2e2820;letter-spacing:0.1em;text-transform:uppercase;">
        Powered by RAG · LexT5 · TextRank · spaCy
    </span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;color:#2e2820;letter-spacing:0.1em;text-transform:uppercase;">
        For Courts & Legal Analysts
    </span>
</div>
""", unsafe_allow_html=True)