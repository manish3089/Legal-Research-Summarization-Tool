# 🕵️‍♂️ AI-Powered Forensic Document Summarization System

This project aims to build a robust NLP-powered tool that extracts key insights and summarizes forensic and legal documents using both extractive and abstractive summarization techniques. Designed with forensic analysts, legal professionals, and investigators in mind, the system simplifies the reading and analysis of complex documents.

---

## 📌 Features

- 📄 **Upload & Parse**: Supports document upload (PDF, DOCX, TXT) and text extraction
- 🧹 **Preprocessing**: Cleans, normalizes, and tokenizes raw legal/forensic text
- 📚 **Extractive Summarization**: Uses TextRank and BERT-based methods
- 📝 **Abstractive Summarization**: Utilizes transformer models like T5 or BART
- 🕵️ **Entity Recognition**: Extracts people, organizations, case IDs, dates using NER
- 📊 **Forensic Intelligence**: Provides keyword, sentiment, and risk-level insights
- 🧠 **Model API**: Modular backend to plug in custom or pre-trained NLP models
- 🧪 **User Dashboard**: Interactive frontend to upload, summarize, and view reports

---

## 🧠 Tech Stack

| Layer            | Technologies |
|------------------|--------------|
| Language         | Python       |
| Backend          | Flask / FastAPI |
| ML/NLP Models    | BERT, T5, BART, TextRank |
| Preprocessing    | SpaCy, NLTK, Regex |
| Database         | MongoDB      |
| Frontend (Optional) | React / Streamlit |
| Hosting (Phase 2)   | Google Cloud / Render |

---

## 🛠️ Installation

```bash
git clone https://github.com/february-king/AI-Powered-Forensic-Document-Summarization-System.git
cd AI-Powered-Forensic-Document-Summarization-System
pip install -r requirements.txt
```
---

## 🚀 Usage
 Run Flask server
```bash
python app.py
```

---

## 🧪 Summarization Approaches
Extractive

- TextRank
- BERT-based Sentence Embedding + Cosine Similarity

Abstractive

- T5 (Text-To-Text Transfer Transformer)
- BART (Bidirectional Auto-Regressive Transformer)

---

## 📚 Use Case Examples
- Legal case report summarization

- Criminal investigation note simplification

- Crime scene documentation analysis

- Forensic evidence narration parsing
