# 🚀 Legal Research & Summarization Tool - Setup Guide

## 📦 What is This?

An AI-powered legal document analysis tool with:
- ✅ **Document Summarization** (Extractive + Abstractive using LexT5)
- ✅ **RAG (Retrieval-Augmented Generation)** for Q&A
- ✅ **Indian Law Knowledge Base** (Pre-trained with IPC sections)
- ✅ **Entity Extraction** (Names, dates, case numbers)
- ✅ **Key Findings Analysis**

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Extract the Zip File
Unzip `Legal-Tool.zip` to any location (e.g., `C:\Users\YourName\Documents\`)

### Step 2: Install Python Requirements
Open PowerShell/Command Prompt in the extracted folder:

```powershell
pip install -r requirements_updated.txt
```

**Note**: This may take 5-10 minutes as it downloads AI models.

### Step 3: Run the Application
```powershell
.\run_both.bat
```

This will:
- Start Flask backend on http://127.0.0.1:5000
- Start Streamlit frontend on http://localhost:8502

### Step 4: Open in Browser
Go to: **http://localhost:8502**

---

## 📋 System Requirements

- **Python**: 3.8 or higher
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: 2GB free space
- **OS**: Windows 10/11, Linux, or macOS

---

## 🎓 How to Use

### 1️⃣ Document Analysis
1. Click **"📄 Document Analysis"** tab
2. Upload a PDF legal document
3. Choose summary mode:
   - **Extractive**: Fast, keyword-based
   - **Hybrid**: Extractive + AI refinement (recommended)
4. Click **"Analyze Document"**
5. View summary, metadata, and key findings

### 2️⃣ RAG Question Answering
1. Click **"🔍 Ask Questions (RAG)"** tab
2. **Option A**: Upload a document first, then ask questions
3. **Option B**: Ask general Indian law questions (no upload needed!)
4. Enter your question
5. Click **"Get Answer"**

#### 🧪 Try These Sample Questions (No Upload Needed):
- "What is the punishment for murder under IPC?"
- "Explain IPC Section 420"
- "What is Section 498A about?"
- "What is the punishment for theft?"

---

## 🇮🇳 Pre-loaded Indian Law Knowledge

The system comes with sample IPC sections:
- Section 302 (Murder)
- Section 304 (Culpable Homicide)
- Section 323 (Voluntarily Causing Hurt)
- Section 376 (Rape)
- Section 379 (Theft)
- Section 406 (Criminal Breach of Trust)
- Section 420 (Cheating)
- Section 498A (Cruelty to Women)

---

## 📚 Expanding the Knowledge Base

Want to add more laws? Follow these steps:

### Step 1: Download Legal Documents
- Visit https://www.indiacode.nic.in/
- Download acts in PDF or TXT format
- Recommended: IPC, CrPC, Constitution, Evidence Act

### Step 2: Place Files
Save downloaded files to:
```
data/indian_laws/criminal_law/     (for IPC, CrPC)
data/indian_laws/civil_law/        (for Contract Act, CPC)
data/indian_laws/constitutional_law/ (for Constitution)
data/indian_laws/special_acts/     (for IT Act, POCSO, etc.)
```

### Step 3: Load into System
```powershell
cd backend
python load_indian_laws.py
```

### Step 4: Restart Application
```powershell
.\run_both.bat
```

For detailed instructions, see: `INDIAN_LAW_TRAINING_GUIDE.md`

---

## 🔧 Troubleshooting

### Issue: Port Already in Use
**Solution**: 
```powershell
# Kill existing processes
taskkill /F /IM python.exe
.\run_both.bat
```

### Issue: Module Not Found
**Solution**: 
```powershell
pip install -r requirements_updated.txt --upgrade
```

### Issue: Out of Memory
**Solution**: 
- Close other applications
- Use "Extractive" mode instead of "Hybrid"
- Restart your computer

### Issue: Model Download Fails
**Solution**: 
- Check internet connection
- Try running again (models auto-download on first use)

---

## 📖 Documentation Files

- **SETUP_COMPLETE.md** - Complete setup summary
- **INDIAN_LAW_TRAINING_GUIDE.md** - Detailed training guide
- **QUICK_START_TRAINING.md** - Quick reference
- **IMPROVEMENTS.md** - System improvements log
- **EVALUATION_REPORT.md** - Performance evaluation

---

## 🛠️ Advanced Configuration

### Change Summarization Length
Edit `backend/app.py`, line 216:
```python
summary_length=6  # Change this number (sentences)
```

### Adjust RAG Search Results
Edit `backend/rag_module/rag_engine.py`, line 214:
```python
def search(self, query, top_k=3):  # Change top_k for more results
```

### Change Ports
Edit `run_both.bat`:
- Flask: Change port in `backend/app.py`, line 375
- Streamlit: Add `--server.port 8501` in `run_both.bat`

---

## 🎯 Use Cases

### For Legal Professionals:
- Quick case law summarization
- Extract key facts and findings
- Search through multiple judgments
- Answer legal queries instantly

### For Law Students:
- Study IPC/CrPC sections
- Understand legal concepts
- Analyze case studies
- Research legal topics

### For Courts/Analysts:
- Process large volumes of documents
- Extract metadata (dates, parties, case numbers)
- Generate concise summaries
- Build legal knowledge bases

---

## 🔒 Privacy & Data

- **All processing happens locally** on your machine
- **No data is sent to external servers** (except initial model downloads)
- **Uploaded documents are deleted** after analysis
- **Vector store data is stored locally** in `backend/vector_store/`

---

## 🆘 Getting Help

### Documentation:
1. Read `SETUP_COMPLETE.md` for overview
2. Check `INDIAN_LAW_TRAINING_GUIDE.md` for training
3. See `QUICK_START_TRAINING.md` for quick reference

### Common Commands:
```powershell
# Start application
.\run_both.bat

# Load sample IPC data
cd backend
python load_indian_laws.py --sample

# Check what's in knowledge base
cd backend
python download_laws.py --check

# See download instructions
python download_laws.py
```

---

## 📊 Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: Streamlit
- **NLP**: spaCy, NLTK
- **Summarization**: LexT5, TextRank, BERT
- **RAG**: FAISS, Sentence-Transformers
- **Generation**: FLAN-T5-Base

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Application starts without errors
- [ ] Frontend opens at http://localhost:8502
- [ ] Can upload and analyze a PDF
- [ ] RAG answers "What is IPC Section 302?"
- [ ] Summary generates successfully

---

## 🎉 You're Ready!

The system is fully configured and ready to use. Start by:
1. Testing with the sample IPC questions
2. Uploading a legal document for analysis
3. Adding more legal documents to expand knowledge

**For questions or issues, refer to the documentation files or contact the system administrator.**

---

**Made with ⚖️ for Legal AI | 2025**
