# ⚡ Quick Start: Train Your RAG on Indian Laws

## 🎯 What This Does
Enables your RAG system to answer general Indian law questions WITHOUT needing to upload documents each time.

---

## 🚀 Quick Test (2 minutes)

### Load Sample IPC Sections:
```powershell
cd backend
python load_indian_laws.py --sample
```

### Test It:
1. Start app: `cd .. ; .\run_both.bat`
2. Go to RAG Query tab
3. Ask: **"What is the punishment for murder under IPC?"**
4. You should get an answer about IPC Section 302!

---

## 📚 Full Setup (For Production Use)

### Step 1: Get Legal Documents
Download from [IndiaCode.nic.in](https://www.indiacode.nic.in/):
- Indian Penal Code (IPC)
- CrPC, Evidence Act, Constitution, etc.

### Step 2: Organize Files
```
data/indian_laws/
├── IPC_sections.txt
├── CrPC_sections.txt
├── Constitution_of_India.txt
└── ... more laws
```

### Step 3: Load Into System
```powershell
cd backend
python load_indian_laws.py
```

### Step 4: Verify
```powershell
# Check if loaded successfully
ls ..\vector_store\
```

You should see:
- `legal_faiss.index`
- `legal_metadata.json`

---

## 🧪 Test Questions

Try these after loading:

### IPC Questions:
- "What is IPC Section 302?"
- "Explain punishment for theft"
- "What is Section 420 IPC about?"

### General Law:
- "What is culpable homicide?"
- "Explain criminal breach of trust"

---

## 🎓 Tips

### ✅ DO:
- Start with sample data to test
- Download official legal texts
- Keep files organized by topic
- Test after each major addition

### ❌ DON'T:
- Don't load random/unverified legal content
- Don't mix different jurisdictions
- Don't skip testing

---

## 🔧 Useful Commands

### Load sample data:
```powershell
python load_indian_laws.py --sample
```

### Load full corpus:
```powershell
python load_indian_laws.py
```

### Clear and start fresh:
```powershell
rm -r ..\vector_store\
python load_indian_laws.py --sample
```

### Check what's loaded:
```powershell
cat ..\vector_store\legal_metadata.json
```

---

## 📊 What Success Looks Like

### Before Training:
Query: "What is IPC 302?"
Response: ❌ "No relevant information found"

### After Training:
Query: "What is IPC 302?"
Response: ✅ "Section 302 of the Indian Penal Code deals with Punishment for Murder. Whoever commits murder shall be punished with death or imprisonment for life..."

---

## 🆘 Troubleshooting

**Problem**: Script not found
**Fix**: Make sure you're in the `backend` folder

**Problem**: No documents found
**Fix**: Check `data/indian_laws/` exists and has files

**Problem**: Out of memory
**Fix**: Load smaller batches, close other applications

---

## 📖 Need More Help?

Read the full guide: `INDIAN_LAW_TRAINING_GUIDE.md`

---

**Made with ⚖️ for Legal AI**
