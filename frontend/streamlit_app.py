import streamlit as st
import requests
from streamlit_lottie import st_lottie
import json

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title=" Easy Edicts",
    page_icon="⚖️",
    layout="wide",
)

# -----------------------------------
# CUSTOM CSS + BACKGROUND
# -----------------------------------
page_bg_img = """
<style>
body {
    background-image: url("https://images.unsplash.com/photo-1505666287802-931dc83948e0?auto=format&fit=crop&w=1950&q=80");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    color: #ffffff;
    font-family: 'Poppins', sans-serif;
}

.main {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 25px;
    padding: 40px;
    backdrop-filter: blur(25px);
    box-shadow: 0px 10px 40px rgba(0,0,0,0.5);
}

h1, h2, h3 {
    text-align: center;
    color: #ffffff;
    text-shadow: 0px 0px 15px rgba(255,255,255,0.5);
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
    box-shadow: 0px 0px 20px rgba(0,183,255,0.8);
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

.stSelectbox, .stTextInput {
    background: rgba(255,255,255,0.2);
    color: white;
    border-radius: 10px;
}

.data-card {
    background: rgba(255,255,255,0.1);
    border-left: 5px solid #00bfff;
    border-radius: 10px;
    padding: 15px 20px;
    margin-bottom: 10px;
    color: white;
}

hr {
    border: 0.5px solid rgba(255,255,255,0.3);
}

footer {
    text-align: center;
    color: rgba(255,255,255,0.7);
    font-size: 0.9rem;
    margin-top: 40px;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

# -----------------------------------
# LOTTIE ANIMATION
# -----------------------------------
def load_lottieurl(url: str):
    import requests
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

try:
    from streamlit_lottie import st_lottie
    lottie_ai = load_lottieurl("https://lottie.host/06b4e889-7f68-4ec3-9a54-c4b190c6c382/LuUk3ovOEN.json")
except:
    lottie_ai = None

if lottie_ai:
    st_lottie(lottie_ai, height=180, key="ai_header")

# -----------------------------------
# HEADER
# -----------------------------------
st.markdown("<h1>⚖️ Easy Edicts</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#ddd;'>AI-Powered Analysis of Legal Documents</p>", unsafe_allow_html=True)
st.write("")

# -----------------------------------
# TAB NAVIGATION
# -----------------------------------
tab = st.radio(
    "Navigation",
    ["📄 Document Summarization", "🔍 Search (Coming Soon)"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown('<div class="main">', unsafe_allow_html=True)

# -----------------------------------
# DOCUMENT SUMMARIZATION TAB
# -----------------------------------
if tab == "📄 Document Summarization":
    st.subheader("📁 Upload Your Legal Document")

    uploaded_file = st.file_uploader("Select a PDF File", type=["pdf"])
    summary_detail = st.selectbox(
        "Select Summary Type",
        ["standard", "brief", "detailed", "comprehensive"]
    )

    if uploaded_file is not None:
        if st.button("🧠 Analyze Document"):
            with st.spinner("Analyzing document... Please wait ⏳"):
                try:
                    response = requests.post(
                        "http://127.0.0.1:5000/api/analyze",
                        files={"file": uploaded_file},
                        data={"summary_detail": summary_detail}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Analysis Complete")

                        # ------------------ SUMMARY ------------------
                        st.markdown("### 📝 Document Summary")
                        st.markdown(
                            f"<div class='data-card'>{result.get('summary', 'No summary available.')}</div>",
                            unsafe_allow_html=True
                        )

                        # ------------------ METADATA ------------------
                        st.markdown("### 📂 Extracted Metadata")
                        metadata = result.get("metadata", {})
                        if metadata:
                            for key, value in metadata.items():
                                display_value = ", ".join(value) if isinstance(value, list) else value
                                st.markdown(f"<div class='data-card'><strong>{key.title()}:</strong> {display_value or 'N/A'}</div>", unsafe_allow_html=True)

                        # ------------------ STATISTICS ------------------
                        st.markdown("### 📊 Document Statistics")
                        stats = result.get("statistics", {})
                        if stats:
                            st.markdown(f"<div class='data-card'><strong>Word Count:</strong> {stats.get('word_count', 'N/A')}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='data-card'><strong>Sentence Count:</strong> {stats.get('sentence_count', 'N/A')}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='data-card'><strong>Summary Length:</strong> {stats.get('summary_length', 'N/A')}</div>", unsafe_allow_html=True)

                        # ------------------ KEY FINDINGS ------------------
                        st.markdown("### 🔍 Key Forensic Findings")
                        findings = result.get("key_findings", [])
                        if findings:
                            for finding in findings:
                                st.markdown(f"<div class='data-card'>{finding}</div>", unsafe_allow_html=True)
                        else:
                            st.info("No key findings detected.")

                    else:
                        st.error(f"Server Error: {response.status_code}")
                except Exception as e:
                    st.error(f"⚠️ Could not connect to backend: {e}")

else:
    st.info("🔎 Search functionality will be added soon.")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("""
<footer>
<hr>
<p>© 2025 Forensic Legal Summarization Tool | Designed with ⚖️ and ❤️ by AI</p>
</footer>
""", unsafe_allow_html=True)
