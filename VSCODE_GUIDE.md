# Running Legal Research Tool in VS Code

## ✅ VS Code Setup Complete!

Your project is now configured for easy running in VS Code with pre-configured launch configurations and tasks.

---

## 🚀 Quick Start (3 Methods)

### **Method 1: Using Debug Panel (Easiest)** ⭐ RECOMMENDED

1. **Open VS Code** (already opened)
2. Click **Run and Debug** icon in left sidebar (▶️ icon)
3. Select **"Full App (Backend + Frontend)"** from dropdown
4. Click **green play button** (▶️)

✅ This will start both backend and frontend automatically!

### **Method 2: Using Tasks**

1. Press `Ctrl+Shift+P` (Command Palette)
2. Type: `Tasks: Run Task`
3. Select: **"Run Full App"**

### **Method 3: Using Terminal** (Manual)

**Open 2 terminals in VS Code** (`Ctrl+Shift+`` to open terminal):

**Terminal 1 - Backend:**
```bash
python backend/app.py
```

**Terminal 2 - Frontend:**
```bash
streamlit run frontend/streamlit_app.py
```

---

## 🎯 Available Configurations

In the **Run and Debug** panel, you have:

### 1. **Full App (Backend + Frontend)** ⭐
- Runs both servers together
- Best for normal use
- Automatically opens both terminals

### 2. **Backend (Flask)**
- Runs only the Flask API
- Port: 5000
- For backend development

### 3. **Frontend (Streamlit)**
- Runs only the Streamlit UI
- Port: 8501
- For frontend development

### 4. **Test Evaluation**
- Runs quality evaluation tests
- Shows ROUGE scores, accuracy, etc.

---

## 📋 Available Tasks

Press `Ctrl+Shift+P` → `Tasks: Run Task`:

| Task | Description |
|------|-------------|
| **Run Full App** | Start both backend + frontend |
| **Run Backend** | Start Flask only |
| **Run Frontend** | Start Streamlit only |
| **Run Tests** | Run evaluation metrics |
| **Install Dependencies** | Install all requirements |

---

## 🔧 Step-by-Step Instructions

### **First Time Setup:**

1. **Open Integrated Terminal** (`Ctrl+Shift+``)

2. **Install Dependencies** (one-time):
   ```bash
   pip install -r requirements_updated.txt
   python -m spacy download en_core_web_sm
   ```

3. **Run the Application**:
   - Click **Run and Debug** (Ctrl+Shift+D)
   - Select **"Full App (Backend + Frontend)"**
   - Click ▶️ **Start Debugging**

4. **Access the App**:
   - Frontend: http://localhost:8501 (opens automatically)
   - Backend: http://localhost:5000

---

## 💡 VS Code Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+D` | Open Run and Debug panel |
| `F5` | Start debugging (run selected config) |
| `Shift+F5` | Stop debugging |
| `Ctrl+Shift+`` | Open new terminal |
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+P` | Quick file open |
| `Ctrl+B` | Toggle sidebar |

---

## 📁 VS Code Folder Structure

```
.vscode/
├── launch.json    # Debug configurations (what you see in Run & Debug)
├── settings.json  # VS Code Python settings
└── tasks.json     # Quick tasks (Run Task menu)
```

---

## 🐛 Debugging Tips

### **To Debug Backend:**
1. Set breakpoints in `backend/app.py` (click left of line number)
2. Select **"Backend (Flask)"** configuration
3. Press F5
4. Make requests from frontend - will pause at breakpoints

### **To Debug Frontend:**
1. Set breakpoints in `frontend/streamlit_app.py`
2. Select **"Frontend (Streamlit)"** configuration
3. Press F5
4. Interact with UI - will pause at breakpoints

### **To See Output:**
- Terminal output appears in **TERMINAL** tab (bottom panel)
- Debug output in **DEBUG CONSOLE** tab

---

## 🎨 Recommended VS Code Extensions

Install these for better experience:

1. **Python** (Microsoft) - Already required
2. **Pylance** (Microsoft) - Python language server
3. **autoDocstring** - Generate docstrings
4. **Better Comments** - Highlight TODO, FIXME, etc.
5. **Error Lens** - Inline error messages
6. **GitLens** - Git integration

**Install**: `Ctrl+Shift+X` → Search → Install

---

## 🔥 Quick Commands

### **Run Full App:**
```bash
# In VS Code terminal
python backend/app.py
# Then open new terminal (Ctrl+Shift+`)
streamlit run frontend/streamlit_app.py
```

### **Run Tests:**
```bash
python test_evaluation.py
```

### **Check Dependencies:**
```bash
pip list | Select-String "torch|transformers|streamlit|flask"
```

---

## 📊 What Happens When You Run

### **Backend (Flask) starts:**
```
[INFO] Loading models...
[INFO] ✅ LegalRAG initialized successfully.
[INFO] 🚀 Starting Legal Summarization + RAG API Server...
 * Running on http://127.0.0.1:5000
```
**Wait 20-30 seconds for models to load**

### **Frontend (Streamlit) starts:**
```
You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```
**Opens automatically in browser**

---

## ⚠️ Troubleshooting

### **Issue: "Command not found: streamlit"**
**Solution:**
```bash
pip install streamlit
```

### **Issue: Backend doesn't start**
**Solution:** Check terminal output for errors. Common fixes:
```bash
# Reinstall dependencies
pip install -r requirements_updated.txt

# Check Python version (needs 3.8-3.10)
python --version
```

### **Issue: Port already in use**
**Solution:** Kill existing processes:
```powershell
# Check what's using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID with actual number)
taskkill /PID <PID> /F
```

### **Issue: Module not found**
**Solution:** Make sure you're in the right directory:
```bash
# In VS Code terminal, you should be in:
# C:\Users\SYED SHAHABAZ A\Documents\Legal-Research-Summarization-Tool

# Verify with:
pwd
```

---

## 🎯 Workflow in VS Code

### **Development Workflow:**

1. **Start both servers** (Run & Debug → Full App)
2. **Make code changes** in VS Code editor
3. **Backend auto-reloads** (Flask debug mode)
4. **Frontend**: Refresh browser or click "Rerun" in Streamlit
5. **Check logs** in TERMINAL tab

### **Testing Workflow:**

1. **Make changes** to summarization code
2. **Run tests**: Select "Test Evaluation" config, press F5
3. **Check scores** in terminal output
4. **Iterate** until quality improves

---

## 🚀 You're All Set!

**Next Steps:**

1. ✅ VS Code is already open with your project
2. ✅ Press `Ctrl+Shift+D` to open Run and Debug
3. ✅ Select "Full App (Backend + Frontend)"
4. ✅ Click ▶️ to start
5. ✅ Wait 30 seconds for models to load
6. ✅ Browser opens at http://localhost:8501
7. ✅ Upload a PDF and test!

---

## 📚 Files to Explore in VS Code

**Key Files:**
- `backend/app.py` - Main Flask server
- `frontend/streamlit_app.py` - UI
- `backend/nlp_module/extractive_summarization.py` - Enhanced scoring
- `backend/rag_module/rag_engine.py` - RAG system
- `test_evaluation.py` - Quality tests

**Documentation:**
- `EVALUATION_REPORT.md` - Quality scores
- `IMPROVEMENTS.md` - What changed
- `README_FOR_COLLEAGUES.md` - Setup guide

---

**Happy Coding! 🎉**

Press F5 to get started!
