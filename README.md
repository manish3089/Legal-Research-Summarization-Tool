# ⚖️ Legal Research & Summarization Tool

A legal document analysis system that combines summarization, entity extraction, and Retrieval-Augmented Generation (RAG) for Indian legal documents.

## Features

* Document Summarization (Extractive + Hybrid)
* RAG-based Question Answering
* Indian Law Knowledge Base
* Entity Extraction (Names, Dates, Sections, Case Numbers)
* Key Findings Extraction
* Semantic Search using FAISS
* Local Deployment

## Tech Stack

* Flask
* Streamlit
* spaCy, NLTK
* TextRank, Tfidf
* FAISS
* Sentence Transformers
* FLAN-T5
* PyMuPDF

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/Legal-Research-Summarization-Tool.git

cd Legal-Research-Summarization-Tool

pip install -r requirements_updated.txt

# Windows
.\run_both.bat

# Linux/Mac
./run_both.sh
```

Open:

```text
http://localhost:8502
```

## Usage

1. Upload a legal PDF.
2. Generate a summary.
3. Extract entities and key findings.
4. Ask questions about the document or Indian laws.

## Project Structure

```text
Legal-Research-Summarization-Tool/
├── backend/
├── frontend/
├── data/
├── uploads/
├── vector_store/
├── requirements_updated.txt
└── README.md
```

## Key Components

* **Summarization:** TextRank + LexT5
* **RAG Engine:** FAISS + Sentence Transformers
* **Question Answering:** FLAN-T5
* **Entity Extraction:** spaCy
* **Document Processing:** PyMuPDF

## Applications

* Legal document summarization
* Legal research assistance
* Indian law question answering
* Case document analysis
* Information retrieval from legal texts
