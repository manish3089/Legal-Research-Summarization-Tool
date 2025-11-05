"""
frontend/streamlit_app.py
⚖️ Retrieval-Augmented Legal Insight Generator
✨ Polished, Professional, Glassmorphic, AI-Powered Legal Interface
"""

import streamlit as st
import requests
from streamlit_lottie import st_lottie
import json

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title="RAG Legal Insight Generator",
    page_icon="⚖️",
    layout="wide",
)

# -----------------------------------
# CUSTOM CSS (Enhanced Glassmorphism + Animations)
# -----------------------------------
custom_css = """
<style>
body {
    background: linear-gradient(135deg, #0b0c10, #1f2833, #0b0c10);
    background-attachment: fixed;
    color: #ffffff;
    font-family: 'Poppins', sans-serif;
}
.main {
    background: rgba(255, 255, 255, 0.07);
    border-radius: 25px;
    padding: 40px;
    backdrop-filter: blur(25px);
    box-shadow: 0px 10px 50px rgba(0,0,0,0.6);
}
h1, h2, h3 {
    text-align: center;
    color: #00d4ff;
    text-shadow: 0px 0px 15px rgba(0, 191, 255, 0.6);
    font-weight: 700;
}
.stButton>button {
    background: linear-gradient(135deg, #0072ff, #00c6ff);
    border: none;
    color: white;
    font-weight: 600;
    border-radius: 12px;
    padding: 12px 30px;
    transition: all 0.3s ease;
    box-shadow: 0px 4px 15px rgba(0,183,255,0.4);
}
.stButton>button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 25px rgba(0,183,255,0.8);
}
.stFileUploader label {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 15px;
    padding: 15px;
    border: 2px dashed #00bfff;
    color: #ffffff;
    font-weight: 500;
    transition: all 0.3s ease-in-out;
}
.stFileUploader label:hover {
    background: rgba(0, 191, 255, 0.2);
    border-color: #66d9ff;
}
.data-card {
    background: rgba(255,255,255,0.08);
    border-left: 5px solid #00bfff;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 12px;
    color: white;
    line-height: 1.6;
}
.summary-card {
    background: rgba(0, 123, 255, 0.15);
    border-radius: 12px;
    border: 1px solid rgba(0, 191, 255, 0.3);
    padding: 20px;
    margin-top: 10px;
    color: #e3f6ff;
}
hr {
    border: 0.5px solid rgba(255,255,255,0.2);
}
footer {
    text-align: center;
    color: rgba(255,255,255,0.7);
    font-size: 0.9rem;
    margin-top: 40px;
}
.metric-box {
    display: flex;
    justify-content: space-between;
    background: rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 10px 15px;
    margin: 5px 0;
}
.metric-label {
    color: #a9d6ff;
}
.metric-value {
    color: #fff;
    font-weight: 600;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -----------------------------------
# LOTTIE ANIMATION
# -----------------------------------
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_ai = load_lottieurl("https://lottie.host/06b4e889-7f68-4ec3-9a54-c4b190c6c382/LuUk3ovOEN.json")
if lottie_ai:
    st_lottie(lottie_ai, height=180, key="ai_header")

# -----------------------------------
# HEADER
# -----------------------------------
st.markdown("<h1>⚖️ RETRIEVAL-AUGMENTED LEGAL INSIGHT GENERATOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#ddd;'>AI-Powered Analysis of Legal Documents</p>", unsafe_allow_html=True)
st.write("")

# -----------------------------------
# TAB NAVIGATION
# -----------------------------------
tab = st.radio(
    "Navigation",
    ["📄 Document Analysis", "🔍 Ask Questions (RAG)"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown('<div class="main">', unsafe_allow_html=True)

# -----------------------------------
# DOCUMENT SUMMARIZATION TAB
# -----------------------------------
if tab == "📄 Document Analysis":
    st.subheader("📁 Upload Legal Document")
    uploaded_file = st.file_uploader("Select a PDF File", type=["pdf"])

    col1, col2 = st.columns(2)
    with col1:
        mode = st.selectbox(
            "Summarization Mode",
            options=["extractive", "hybrid"],
            format_func=lambda x: "📝 Extractive (Fast)" if x == "extractive" else "🔄 Hybrid (LexT5 Refined)",
        )
    with col2:
        extraction_ratio = st.slider("Extraction Ratio (%)", 30, 70, 50, 5) / 100

    if st.button("🧠 Analyze Document", use_container_width=True) and uploaded_file:
        with st.spinner(f"Analyzing your document using {mode.upper()} mode..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/api/analyze",
                    files={"file": uploaded_file},
                    data={"mode": mode, "extraction_ratio": extraction_ratio},
                )

                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Analysis Complete!")

                    # ✅ Summary
                    st.markdown("### 🧾 Summary")
                    st.markdown(f"<div class='summary-card'>{result.get('summary', 'No summary generated.')}</div>", unsafe_allow_html=True)

                    # ✅ Metadata
                    metadata = result.get("metadata", {})
                    if metadata:
                        st.markdown("### 📘 Metadata Extracted")
                        for k, v in metadata.items():
                            st.markdown(f"<div class='data-card'><b>{k.title()}:</b> {v}</div>", unsafe_allow_html=True)

                    # ✅ Key Findings
                    findings = result.get("key_findings", [])
                    if findings:
                        st.markdown("### ⚖️ Key Findings")
                        for f in findings:
                            st.markdown(f"<div class='data-card'>• {f}</div>", unsafe_allow_html=True)

                    # ✅ Stats
                    stats = result.get("statistics", {})
                    st.markdown("### 📊 Document Statistics")
                    for key, value in stats.items():
                        st.markdown(
                            f"<div class='metric-box'><span class='metric-label'>{key.replace('_',' ').title()}</span>"
                            f"<span class='metric-value'>{value}</span></div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.error(f"❌ {response.status_code}: {response.text}")
            except Exception as e:
                st.error(f"⚠️ Connection error: {e}")

# -----------------------------------
# RAG QUERY TAB
# -----------------------------------
elif tab == "🔍 Ask Questions (RAG)":
    st.subheader("💬 Ask Questions About Your Uploaded Documents")
    query = st.text_input("Enter your legal question below:")

    if st.button("Ask ⚖️", use_container_width=True) and query:
        with st.spinner("Retrieving contextual legal insights..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/api/query",
                    json={"query": query},
                    timeout=120,
                )
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ Response Generated")

                    st.markdown("### 🧠 Answer")
                    st.markdown(f"<div class='summary-card'>{result.get('answer', 'No answer found.')}</div>", unsafe_allow_html=True)

                    if result.get("context"):
                        st.markdown("### 📚 Context Used")
                        for c in result["context"]:
                            st.markdown(f"<div class='data-card'>{c}</div>", unsafe_allow_html=True)
                else:
                    st.error(f"❌ Error: {response.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("⚠️ Could not connect to backend. Make sure Flask is running.")
            except Exception as e:
                st.error(f"⚠️ {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("""
<footer>
<hr>
<p>© 2025 Legal AI | Powered by RAG + LexT5 + TextRank</p>
<p style="font-size:0.85rem; color:#aaa;">Smart Legal Document Intelligence | Designed for Courts & Legal Analysts</p>
</footer>
""", unsafe_allow_html=True)
