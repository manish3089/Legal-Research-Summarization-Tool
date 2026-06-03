# ⚖️ Legal Research & Summarization Tool

> AI-Powered Legal Document Analysis with RAG (Retrieval-Augmented Generation) and Indian Law Knowledge Base

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)

## 🌟 Features

- 📄 **Document Summarization**: Extractive + Abstractive (using LexT5)
- 🔍 **RAG-based Q&A**: Ask questions about uploaded documents or general Indian law
- 🇮🇳 **Pre-trained on Indian Laws**: IPC, CrPC, and more
- 🎯 **Entity Extraction**: Automatically extract names, dates, case numbers
- 📊 **Key Findings Analysis**: Identify important legal conclusions
- 💾 **Vector Store**: FAISS-based semantic search
- 🚀 **Easy Setup**: One-command deployment

## 🚀 Quick Start


### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/Legal-Research-Summarization-Tool.git
cd Legal-Research-Summarization-Tool
```

2. **Install dependencies**
```bash
pip install -r requirements_updated.txt
```

3. **Run the application**
```bash
# Windows
.\run_both.bat

# Linux/Mac
chmod +x run_both.sh
./run_both.sh
```

4. **Open in browser**
Navigate to: http://localhost:8502

## 📖 Usage

### Document Analysis
1. Upload a PDF legal document
2. Choose summarization mode (Extractive/Hybrid)
3. View summary, metadata, and key findings

### RAG Question Answering

**Without uploading documents** (uses pre-loaded Indian law):
```
❓ "What is the punishment for murder under IPC?"
✅ "Section 302 IPC: Punishment with death or life imprisonment..."

❓ "Explain IPC Section 420"
✅ "Section 420 deals with cheating - imprisonment up to 7 years..."
```

**With uploaded documents**:
1. Upload a legal document
2. Ask specific questions about it
3. Get contextual answers with source citations

## 🇮🇳 Pre-loaded Indian Law Knowledge

The system comes pre-trained with key IPC sections:
- Section 302 (Murder)
- Section 304 (Culpable Homicide)
- Section 323 (Voluntarily Causing Hurt)
- Section 376 (Rape)
- Section 379 (Theft)
- Section 406 (Criminal Breach of Trust)
- Section 420 (Cheating)
- Section 498A (Cruelty to Women)

## 📚 Expanding the Knowledge Base

### Adding More Legal Documents

1. Download legal texts from [IndiaCode.nic.in](https://www.indiacode.nic.in/)
2. Place files in appropriate folders:
```
data/indian_laws/
├── criminal_law/     # IPC, CrPC, Evidence Act
├── civil_law/        # Contract Act, CPC
├── constitutional_law/  # Constitution
└── special_acts/     # IT Act, POCSO, etc.
```

3. Load into system:
```bash
cd backend
python load_indian_laws.py
```

4. Restart the application

See [INDIAN_LAW_TRAINING_GUIDE.md](INDIAN_LAW_TRAINING_GUIDE.md) for detailed instructions.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Streamlit Frontend                │
│         (User Interface)                    │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│            Flask Backend API                │
├─────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────────┐    │
│  │ Summarizer   │  │   RAG Engine     │    │
│  │  - TextRank  │  │  - FAISS Vector  │    │
│  │  - LexT5     │  │  - Sentence-T5   │    │
│  └──────────────┘  │  - FLAN-T5-Base  │    │
│                    └──────────────────┘    │
│  ┌──────────────┐  ┌──────────────────┐    │
│  │   NLP/NER    │  │  Document Parser │    │
│  │   (spaCy)    │  │    (PyMuPDF)     │    │
│  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: Flask
- **Frontend**: Streamlit
- **NLP**: spaCy, NLTK
- **Summarization**: LexT5, TextRank, BERT
- **RAG**: FAISS, Sentence-Transformers
- **Generation**: FLAN-T5-Base
- **PDF Processing**: PyMuPDF

## 📁 Project Structure

```
Legal-Research-Summarization-Tool/
├── backend/
│   ├── app.py                    # Flask API server
│   ├── load_indian_laws.py       # Legal document loader
│   ├── download_laws.py          # Download helper
│   ├── nlp_module/               # NLP processing
│   └── rag_module/               # RAG engine
├── frontend/
│   └── streamlit_app.py          # UI interface
├── data/
│   └── indian_laws/              # Legal documents storage
├── uploads/                       # Temporary uploads
├── vector_store/                  # FAISS index
├── requirements_updated.txt       # Dependencies
├── run_both.bat                   # Windows launcher
└── README.md                      # This file
```

## 🐛 Troubleshooting

### Common Issues

**Port already in use**
```bash
# Windows
taskkill /F /IM python.exe

# Linux/Mac
pkill python
```

**Out of memory**
- Use "Extractive" mode instead of "Hybrid"
- Close other applications
- Increase system swap space

**Model download fails**
- Check internet connection
- Retry - models auto-download on first use
- Manually download from HuggingFace if needed

See [SETUP_FOR_TEAM.md](SETUP_FOR_TEAM.md) for more troubleshooting tips.

## 📖 Documentation

- [Setup Guide for Teams](SETUP_FOR_TEAM.md)
- [Indian Law Training Guide](INDIAN_LAW_TRAINING_GUIDE.md)
- [Quick Start Reference](QUICK_START_TRAINING.md)
- [Setup Complete Overview](SETUP_COMPLETE.md)

## 🎯 Use Cases

### For Legal Professionals
- Quick case law summarization
- Multi-document search and analysis
- Instant legal query responses

### For Law Students
- Study IPC/CrPC sections
- Understand legal concepts
- Research case studies

### For Courts & Analysts
- Process large document volumes
- Extract metadata and key facts
- Build custom legal knowledge bases

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
