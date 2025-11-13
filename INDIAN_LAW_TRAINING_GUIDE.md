# 🇮🇳 Indian Law Knowledge Base Training Guide

## Overview
This guide explains how to train your RAG system on Indian laws so it can answer general legal questions beyond just analyzing uploaded documents.

---

## 🎯 Goal
Build a comprehensive Indian legal knowledge base that allows your RAG system to:
- Answer questions about IPC sections
- Explain legal provisions from various acts
- Provide context about constitutional provisions
- Reference landmark judgments
- Answer general Indian law queries

---

## 📚 Step 1: Collect Legal Documents

### Essential Documents to Collect:

#### **1. Core Criminal Law**
- Indian Penal Code (IPC) - All 511 sections
- Code of Criminal Procedure (CrPC) - 1973
- Indian Evidence Act - 1872

#### **2. Constitutional Law**
- Constitution of India (Full text)
- All Amendments
- Schedules

#### **3. Civil Law**
- Code of Civil Procedure (CPC) - 1908
- Indian Contract Act - 1872
- Transfer of Property Act - 1882
- Specific Relief Act - 1963

#### **4. Corporate & Business Law**
- Companies Act - 2013
- Indian Partnership Act - 1932
- Negotiable Instruments Act - 1881

#### **5. Special Acts**
- IT Act - 2000 (Cyber Law)
- GST Acts
- Motor Vehicles Act - 1988
- Consumer Protection Act - 2019
- POCSO Act - 2012
- Domestic Violence Act - 2005

#### **6. Case Law** (Optional but valuable)
- Supreme Court landmark judgments
- High Court important decisions

### 📥 Where to Find These Documents:

1. **Government Sources (FREE)**
   - [IndiaCode.nic.in](https://www.indiacode.nic.in/) - Official Government repository
   - [Legislative Department](https://legislative.gov.in/)
   
2. **Legal Databases**
   - [Indian Kanoon](https://indiankanoon.org/) - Free case law
   - [Manupatra](https://www.manupatrafast.com/) - Paid service
   - [SCC Online](https://www.scconline.com/) - Paid service

3. **Public Domain Resources**
   - [Archive.org Legal Texts](https://archive.org/)
   - University law library repositories

---

## 🛠️ Step 2: Prepare Your Documents

### File Format Requirements:
- **Preferred**: Plain text (`.txt`) or PDF (`.pdf`)
- **Encoding**: UTF-8
- **Structure**: Keep sections clearly labeled

### Recommended File Structure:
```
data/
└── indian_laws/
    ├── IPC_sections.txt
    ├── CrPC_sections.txt
    ├── Constitution_of_India.txt
    ├── Indian_Evidence_Act.txt
    ├── Companies_Act_2013.txt
    ├── IT_Act_2000.txt
    └── judgments/
        ├── Kesavananda_Bharati_Case.txt
        ├── Maneka_Gandhi_Case.txt
        └── ... more judgments
```

### Example Format for IPC Sections:
```text
INDIAN PENAL CODE

Section 302: Punishment for Murder
Whoever commits murder shall be punished with death or imprisonment 
for life, and shall also be liable to fine.

Section 304: Punishment for Culpable Homicide Not Amounting to Murder
Whoever commits culpable homicide not amounting to murder shall be 
punished with imprisonment for life...
```

---

## 🚀 Step 3: Load Documents into RAG System

### Method 1: Load Sample Data (Quick Test)
```bash
cd backend
python load_indian_laws.py --sample
```

This loads sample IPC sections for testing.

### Method 2: Load Full Legal Corpus
1. **Create the directory**:
   ```bash
   mkdir -p data/indian_laws
   ```

2. **Add your legal documents** to `data/indian_laws/`

3. **Run the loader**:
   ```bash
   cd backend
python load_indian_laws.py
   ```

### Method 3: Load Documents via API (Programmatic)
You can also add documents programmatically through the existing API by uploading PDFs.

---

## 📊 Step 4: Verify Loading

After loading, check the vector store:
```bash
ls vector_store/
```

You should see:
- `legal_faiss.index` - The vector embeddings
- `legal_metadata.json` - Document metadata

Check the metadata file to see how many chunks were created:
```bash
# On Windows PowerShell:
Get-Content vector_store/legal_metadata.json | ConvertFrom-Json | Measure-Object
```

---

## 🧪 Step 5: Test Your Knowledge Base

### Test Queries to Try:

1. **IPC Questions**:
   - "What is the punishment for murder under IPC?"
   - "Explain IPC Section 420"
   - "What is the difference between Section 302 and 304 IPC?"

2. **General Law Questions**:
   - "What is culpable homicide?"
   - "What are the elements of criminal breach of trust?"
   - "Explain the concept of mens rea"

3. **Constitutional Questions**:
   - "What are fundamental rights under the Indian Constitution?"
   - "Explain Article 21"

### How to Test:
1. Start your application: `.\run_both.bat`
2. Go to the RAG Query tab
3. Ask questions without uploading any document
4. The system should answer from the loaded knowledge base

---

## 🔧 Advanced Configuration

### Adjusting Chunk Size
Edit `backend/rag_module/rag_engine.py` line 120:
```python
if current_len >= 600:  # Change this value
    # 400-500: More granular (better for specific sections)
    # 600-800: Balanced (current default)
    # 1000+: Broader context (better for concepts)
```

### Improving Search Quality
In `rag_engine.py`, adjust hybrid search weight (line 214):
```python
def search(self, query, top_k=3, hybrid_weight=0.7):
    # hybrid_weight: 0.7 = 70% semantic, 30% keyword
    # Increase for more semantic understanding
    # Decrease for more exact keyword matching
```

---

## 📈 Expected Results

### Before Training:
- ❌ "What is IPC Section 302?" → "No relevant information found"

### After Training:
- ✅ "What is IPC Section 302?" → "Section 302 IPC deals with Punishment for Murder. Whoever commits murder shall be punished with death or imprisonment for life..."

---

## 🎓 Best Practices

### 1. **Organize by Topics**
Group related laws together:
```
data/indian_laws/
├── criminal_law/
│   ├── IPC.txt
│   └── CrPC.txt
├── civil_law/
│   ├── CPC.txt
│   └── Contract_Act.txt
└── constitutional_law/
    └── Constitution.txt
```

### 2. **Clean Your Text**
- Remove unnecessary headers/footers
- Fix OCR errors if scanning physical books
- Ensure proper section numbering

### 3. **Incremental Loading**
Start small, test, then expand:
1. Load 10-20 key IPC sections
2. Test queries
3. Add more sections
4. Add other acts

### 4. **Regular Updates**
- Update with new amendments
- Add recent landmark judgments
- Remove outdated provisions

---

## 🔄 Maintenance

### To Clear and Reload:
```bash
# Delete existing vector store
rm -rf vector_store/

# Reload documents
python load_indian_laws.py
```

### To Add New Documents:
Just add files to `data/indian_laws/` and run the loader again. It will append to existing data.

---

## 💡 Pro Tips

1. **Use Official Sources**: Always download from government websites for accuracy

2. **Include Context**: Don't just include bare sections - add explanations, examples, and case references

3. **Test Incrementally**: Load a small dataset first, verify it works, then expand

4. **Monitor Performance**: Large knowledge bases may require more RAM - monitor system resources

5. **Backup Your Data**: Keep backups of:
   - Original legal documents
   - Vector store folder
   - Metadata JSON

---

## 🆘 Troubleshooting

### Issue: "Out of memory" errors
**Solution**: 
- Load documents in smaller batches
- Reduce chunk size
- Consider using a more powerful machine or cloud deployment

### Issue: Poor answer quality
**Solution**:
- Ensure documents are clean and well-formatted
- Adjust `hybrid_weight` parameter
- Increase `top_k` in search to retrieve more context

### Issue: Can't find specific sections
**Solution**:
- Check if documents were loaded (verify `legal_metadata.json`)
- Try rephrasing the query
- Ensure section numbers are clearly marked in source documents

---

## 📞 Next Steps

After setting up your knowledge base:

1. ✅ Test with common legal queries
2. ✅ Gather feedback from legal professionals
3. ✅ Continuously expand with more documents
4. ✅ Consider adding a feedback mechanism to improve answers
5. ✅ Explore fine-tuning the generation model for legal domain

---

## 📖 Example Workflow

```bash
# 1. Download IPC from IndiaCode
# Save as: data/indian_laws/IPC_full.txt

# 2. Create directory
mkdir -p data/indian_laws

# 3. Load into RAG
cd backend
python load_indian_laws.py

# 4. Start application
cd ..
.\run_both.bat

# 5. Test query: "What is Section 302 IPC?"
# Expected: Detailed answer about murder punishment
```

---

## 🎯 Success Metrics

Your RAG system is properly trained when:
- ✅ Answers IPC/CrPC questions without document upload
- ✅ Provides accurate section references
- ✅ Explains legal concepts in context
- ✅ Cites specific provisions correctly
- ✅ Response time < 3 seconds per query

---

**Ready to build your Indian Law knowledge base? Start with Step 1! 🚀**
