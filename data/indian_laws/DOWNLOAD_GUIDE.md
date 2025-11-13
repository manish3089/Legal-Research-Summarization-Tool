# 📥 Download Guide for Indian Legal Documents

## 🎯 Quick Links to Official Sources

### 1️⃣ **Indian Penal Code (IPC)**
**Source**: IndiaCode.nic.in
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2263?sam_handle=123456789/1362

**What to download**:
- Complete IPC with all 511 sections
- Save as: `criminal_law/IPC_Full.txt`

**Alternative**: https://legislative.gov.in/sites/default/files/A1860-45.pdf

---

### 2️⃣ **Code of Criminal Procedure (CrPC) - 1973**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2279?sam_handle=123456789/1362

**Save as**: `criminal_law/CrPC_1973.txt`

---

### 3️⃣ **Indian Evidence Act - 1872**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2188?sam_handle=123456789/1362

**Save as**: `criminal_law/Evidence_Act_1872.txt`

---

### 4️⃣ **Constitution of India**
**Source**: Legislative Department
**Direct Link**: https://legislative.gov.in/constitution-of-india/

**What to download**:
- Full Constitution with all Parts and Articles
- All Amendments (1st to latest)
- Save as: `constitutional_law/Constitution_of_India.txt`

---

### 5️⃣ **Code of Civil Procedure (CPC) - 1908**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2191?sam_handle=123456789/1362

**Save as**: `civil_law/CPC_1908.txt`

---

### 6️⃣ **Indian Contract Act - 1872**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2187?sam_handle=123456789/1362

**Save as**: `civil_law/Contract_Act_1872.txt`

---

### 7️⃣ **Information Technology Act - 2000**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/1999?sam_handle=123456789/1362

**Save as**: `special_acts/IT_Act_2000.txt`

---

### 8️⃣ **Protection of Children from Sexual Offences (POCSO) Act - 2012**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2079?sam_handle=123456789/1362

**Save as**: `special_acts/POCSO_Act_2012.txt`

---

### 9️⃣ **Domestic Violence Act - 2005**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2045?sam_handle=123456789/1362

**Save as**: `special_acts/Domestic_Violence_Act_2005.txt`

---

### 🔟 **Companies Act - 2013**
**Direct Link**: https://www.indiacode.nic.in/handle/123456789/2114?sam_handle=123456789/1362

**Save as**: `civil_law/Companies_Act_2013.txt`

---

## 📋 How to Download

### Method 1: Manual Download (Recommended)
1. Click each link above
2. Download PDF or copy text
3. If PDF, convert to text using online tools or save as PDF
4. Place in the appropriate folder

### Method 2: Using IndiaCode Website
1. Go to https://www.indiacode.nic.in/
2. Use search to find acts by name
3. Download in PDF format
4. Save to appropriate folders

---

## 🔄 Converting PDFs to Text

### Option 1: Keep as PDF
Our loader supports PDFs directly - just place them in the folders.

### Option 2: Convert to TXT (Better accuracy)
**Online Tools**:
- https://www.ilovepdf.com/pdf_to_text
- https://www.adobe.com/acrobat/online/pdf-to-text.html

**Command Line** (if you have pdftotext):
```powershell
pdftotext input.pdf output.txt
```

---

## 📂 Final Folder Structure

After downloading, your structure should look like:

```
data/indian_laws/
├── criminal_law/
│   ├── IPC_Full.txt (or .pdf)
│   ├── CrPC_1973.txt
│   └── Evidence_Act_1872.txt
├── civil_law/
│   ├── CPC_1908.txt
│   ├── Contract_Act_1872.txt
│   └── Companies_Act_2013.txt
├── constitutional_law/
│   └── Constitution_of_India.txt
├── special_acts/
│   ├── IT_Act_2000.txt
│   ├── POCSO_Act_2012.txt
│   └── Domestic_Violence_Act_2005.txt
└── case_law/ (optional)
    └── [landmark judgments]
```

---

## 🚀 After Downloading

Once you've added files, load them:

```powershell
cd backend
python load_indian_laws.py
```

This will:
- Scan all subdirectories in `data/indian_laws/`
- Load all .txt and .pdf files
- Add them to the RAG knowledge base
- Show you a summary of what was loaded

---

## ⚡ Quick Start (Minimal Setup)

**If you want to start small**, download just these 3:

1. **IPC** (Indian Penal Code) - Criminal law basics
2. **Constitution** - Fundamental rights and structure
3. **CrPC** - Criminal procedure

This covers the most common legal queries.

---

## 📖 Alternative: Use Existing Compilations

If manual downloading is tedious, you can:

1. **Buy legal compilations** from:
   - Universal Law Publishing
   - Eastern Book Company
   - Lexis Nexis

2. **University Resources**: Many law schools provide free access to digital legal texts

3. **Public Libraries**: National Law University libraries often have digital collections

---

## 🆘 Troubleshooting

**Problem**: Links don't work
**Solution**: Go to https://www.indiacode.nic.in/ and search manually

**Problem**: PDFs have poor quality (scanned)
**Solution**: Look for newer versions or use OCR tools

**Problem**: Files are too large
**Solution**: Split into smaller sections (e.g., IPC Part 1, IPC Part 2)

---

## ✅ Verification Checklist

Before loading, verify:
- [ ] Files are readable (not corrupted)
- [ ] Text is clean (not full of OCR errors)
- [ ] Section numbers are clearly marked
- [ ] Files are in .txt or .pdf format
- [ ] Files are saved in correct folders

---

**Next Step**: After downloading files, run: `cd backend && python load_indian_laws.py`

**Happy Building! ⚖️**
