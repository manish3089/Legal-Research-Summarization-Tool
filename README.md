# Legal Research & Summarization Tool

A legal document analysis system that combines document summarization, information extraction, and Retrieval-Augmented Generation (RAG) for Indian legal texts.

## Features

* Document summarization (Extractive and Hybrid)
* Question answering using RAG
* Support for Indian legal documents
* Named Entity Recognition (Names, Dates, Case Numbers, Sections)
* Key findings extraction
* Semantic search using FAISS
* Local deployment

## Tech Stack

* **Backend:** Flask
* **Frontend:** Streamlit
* **NLP:** spaCy, NLTK
* **Summarization:** TextRank, Tfidf
* **RAG:** FAISS, Sentence Transformers
* **LLM:** FLAN-T5 Base
* **PDF Processing:** PyMuPDF

---

## Installation

### Prerequisites

* Python 3.8+
* 8 GB RAM minimum
* 2 GB free disk space

### Setup

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/Legal-Research-Summarization-Tool.git
cd Legal-Research-Summarization-Tool
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run streamlit.py
```

---

## Usage

### Document Analysis

1. Upload a legal PDF.
2. Select a summarization mode.
3. View the summary, extracted entities, and key findings.

### Question Answering

The system supports:

* Queries on uploaded documents
* Queries on preloaded Indian legal content

Example:

```text
What is the punishment for murder under IPC?
```

```text
Explain IPC Section 420.
```

---

## Preloaded Legal Knowledge

The default knowledge base includes selected IPC sections:

* Section 302 – Murder
* Section 304 – Culpable Homicide
* Section 323 – Voluntarily Causing Hurt
* Section 376 – Rape
* Section 379 – Theft
* Section 406 – Criminal Breach of Trust
* Section 420 – Cheating
* Section 498A – Cruelty to Women

---

## Expanding the Knowledge Base

Place additional legal documents in:

```text
data/indian_laws/
├── criminal_law/
├── civil_law/
├── constitutional_law/
└── special_acts/
```

Load documents:

```bash
cd backend
python load_indian_laws.py
```

Restart the application after indexing.

---

## Project Structure

```text
Legal-Research-Summarization-Tool/
├── backend/
│   ├── app.py
│   ├── load_indian_laws.py
│   ├── nlp_module/
│   └── rag_module/
│   └── streamlit.py
├── data/
├── uploads/
├── vector_store/
├── requirements.txt
└── README.md
```

---

## Performance

| Task          | Typical Time |
| ------------- | ------------ |
| Summarization | 10–30 sec    |
| RAG Query     | 2–5 sec      |
| Memory Usage  | 2–4 GB RAM   |

---

## Troubleshooting

### Port Already in Use

**Windows**

```bash
taskkill /F /IM python.exe
```

**Linux/macOS**

```bash
pkill python
```

### High Memory Usage

* Use Extractive mode
* Close unnecessary applications
* Increase swap space if required

## Documentation

* SETUP_FOR_TEAM.md
* INDIAN_LAW_TRAINING_GUIDE.md
* QUICK_START_TRAINING.md
* SETUP_COMPLETE.md

---

Built as a Final Year Project for legal document analysis and legal information retrieval.
