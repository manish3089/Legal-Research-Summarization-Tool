# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AI-Powered Legal Document Summarization System using NLP, RAG (Retrieval-Augmented Generation), and transformer models (BERT, T5, BART, LexT5) for forensic and legal document analysis.

## Common Commands

### Backend

**Install Dependencies:**
```powershell
cd backend
pip install -r requirements.txt
```

**Download Required Models:**
```powershell
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('stopwords')"
```

**Run Flask API Server:**
```powershell
cd backend
python app.py
```
Server runs on `http://127.0.0.1:5000`

**Test NLP Pipeline:**
```powershell
cd backend
python test_nlp_pipeline.py
```

### Frontend

**Run Streamlit UI:**
```powershell
cd frontend
streamlit run streamlit_app.py
```

**Note:** Both backend (Flask on port 5000) and frontend (Streamlit) must run simultaneously for full functionality.

## Architecture Overview

### Backend Structure

**`backend/app.py`** — Main Flask API server
- `ForensicDocumentAnalyzer` class: Core document analysis orchestrator
- Lazy-loads heavy models (LexT5) to optimize startup time
- **Key endpoints:**
  - `/api/test` - Health check
  - `/api/analyze` - PDF upload & summarization (extractive/hybrid modes)
  - `/api/query` - RAG-based semantic search and answer generation

**`backend/nlp_module/`** — NLP Processing Pipeline
- `text_preprocessing.py` - SpaCy-based entity extraction (PERSON, ORG, DATE, GPE, CASE_ID) + custom legal patterns
- `extractive_summarization.py` - Hybrid TextRank + TF-IDF with legal document boosting (handles long legal sentences)
- `abstractive_summarization.py` - LexT5 (Legal T5) for refinement with chunking strategy
- `sentiment_risk_analyzer.py` - Forensic intelligence extraction
- `model_wrapper.py` - Model abstraction layer

**`backend/rag_module/`** — RAG Engine
- `rag_engine.py` - FAISS-based vector store with `sentence-transformers/all-MiniLM-L6-v2` embeddings
- Uses `pszemraj/led-large-book-summary` for answer generation
- Persists index to `vector_store/legal_faiss.index` and `vector_store/legal_metadata.json`

### Frontend Structure

**`frontend/streamlit_app.py`** — Glassmorphic web interface
- Two-tab design: Document Analysis and RAG Query
- Communicates with Flask backend via HTTP POST
- Custom CSS with glassmorphism and animations

### Data Flow

1. **Document Upload** → PDF extracted with PyMuPDF (`fitz`)
2. **Text Preprocessing** → SpaCy sentence splitting + entity recognition
3. **Extractive Summarization** → Hybrid scoring (TextRank + TF-IDF)
4. **Optional Abstractive Refinement** → LexT5 model compresses extractive output
5. **RAG Indexing** → Document chunks embedded and stored in FAISS
6. **Query Processing** → Semantic search → Context retrieval → LED model generates answer

### Key Design Patterns

**Lazy Model Loading:**
- `get_abstractive_model()` function defers LexT5 loading until hybrid mode is requested
- Reduces memory footprint for extractive-only workflows

**Singleton Pattern:**
- `get_analyzer()` ensures single `ForensicDocumentAnalyzer` instance
- `rag_engine` instantiated as global in `app.py`

**Legal Text Handling:**
- Custom sentence splitting for long legal sentences (40-50 words/sentence)
- Legal markers (`<HD>`, `Section`, `held that`) receive 20% score boost in extractive summarization
- Corruption detection for scanned PDFs (single-letter patterns, repetition)

**Chunking Strategy:**
- Extractive summary fed to abstractive model to prevent context loss
- LexT5 uses 512-token chunks with sentence boundary preservation
- Compression ratio maintained at 50-70% to preserve legal detail

## Data Directory

`data/` contains 85 legal case files (LNIND_1951_CAL_*.txt) from 1951 Calcutta High Court - used for testing and RAG indexing.

## Model Information

**Extractive Models:**
- SpaCy: `en_core_web_sm`
- TextRank via NetworkX PageRank
- TF-IDF via scikit-learn

**Abstractive Models:**
- Primary: `santoshtyss/lt5-small` (LexT5 - Legal T5)
- RAG Generator: `pszemraj/led-large-book-summary` (LED model)

**Embedding Models:**
- `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors)

## Testing Approach

Use `backend/test_nlp_pipeline.py` to test individual NLP modules with sample legal text. No formal test framework detected - tests are manual via sample inputs.

## Important Notes

- **Windows Environment:** This project uses PowerShell commands (adjust for Unix if needed)
- **GPU Acceleration:** Models auto-detect CUDA; CPU fallback available
- **PDF Requirements:** Only accepts `.pdf` files; scanned PDFs are detected and rejected
- **FAISS Persistence:** Vector store automatically saves after each document addition
- **File Cleanup:** Uploaded PDFs are deleted after analysis (see `finally` block in `/api/analyze`)
- **CORS:** Backend enables CORS for all origins on `/api/*` routes

## Requirements

Key dependencies:
- Flask + flask-cors
- spacy + en_core_web_sm model
- nltk
- transformers + torch
- sentence-transformers
- scikit-learn
- faiss-cpu or faiss-gpu
- pymupdf (fitz)
- streamlit + streamlit-lottie
