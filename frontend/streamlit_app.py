"""
frontend/streamlit_app.py - Updated with mode selection and enhanced UI
"""

import streamlit as st
import requests
from streamlit_lottie import st_lottie
import json

# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------
st.set_page_config(
    page_title="RETRIEVAL AUGMENTED LEGAL INSIGHT GENERATOR",
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

.mode-badge {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    margin: 10px 0;
}

.mode-extractive {
    background: linear-gradient(135deg, #00d4ff, #007aff);
    color: white;
}

.mode-hybrid {
    background: linear-gradient(135deg, #ff6b6b, #ff8e53);
    color: white;
}

.info-box {
    background: rgba(0, 191, 255, 0.2);
    border-left: 4px solid #00bfff;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    margin: 10px 0;
}

.warning-box {
    background: rgba(255, 193, 7, 0.2);
    border-left: 4px solid #ffc107;
    padding: 12px 20px;
    border-radius: 8px;
    color: white;
    margin: 10px 0;
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
st.markdown("<h1>⚖️ RETRIEVAL AUGMENTED LEGAL INSIGHT GENERATOR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#ddd;'>AI-Powered Analysis of Legal Documents</p>", unsafe_allow_html=True)
st.write("")

# -----------------------------------
# TAB NAVIGATION
# -----------------------------------
tab = st.radio(
    "Navigation",
    ["📄 Document Summarization", "🔍 Search"],
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown('<div class="main">', unsafe_allow_html=True)

# -----------------------------------
# DOCUMENT SUMMARIZATION TAB
# -----------------------------------
if tab == "📄 Document Summarization":
    st.subheader("📁 Upload Your Legal Document")

    # File uploader
    uploaded_file = st.file_uploader("Select a PDF File", type=["pdf"])
    
    # Configuration section
    st.markdown("### ⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 🆕 NEW: Mode selection
        mode = st.selectbox(
            "Summarization Mode",
            options=["extractive", "hybrid"],
            format_func=lambda x: "📝 Extractive Only (Fast & Accurate)" if x == "extractive" 
                                  else "🔄 Hybrid (Extractive + LexT5)",
            help="Choose between fast extractive-only or refined hybrid summarization"
        )
        
        # Summary detail
        summary_detail = st.selectbox(
            "Summary Detail Level",
            ["brief", "standard", "detailed", "comprehensive"],
            index=1  # Default to 'standard'
        )
    
    with col2:
        # Extraction ratio slider
        extraction_ratio = st.slider(
            "Extraction Ratio (%)",
            min_value=30,
            max_value=70,
            value=50 if mode == "hybrid" else 35,
            step=5,
            help="Percentage of original document to extract"
        ) / 100
    
    # 🆕 Mode-specific information boxes
    if mode == "extractive":
        st.markdown("""
        <div class="info-box">
        <strong>📝 Extractive Mode</strong><br>
        • Uses TextRank (60%) + TF-IDF (40%)<br>
        • Preserves exact legal terminology<br>
        • Best for factual accuracy (92.3% ROUGE-L)<br>
        • Faster processing (~1-2 seconds)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="warning-box">
        <strong>🔄 Hybrid Mode</strong><br>
        • Extractive + LexT5 abstractive refinement<br>
        • More coherent and readable summaries<br>
        • May rephrase legal terms<br>
        • Slower processing (~3-5 seconds)<br>
        • Automatic fallback to extractive if LexT5 fails
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Analyze button
    if uploaded_file is not None:
        if st.button("🧠 Analyze Document", use_container_width=True):
            with st.spinner(f"Analyzing in **{mode.upper()}** mode... Please wait ⏳"):
                try:
                    # API call with mode parameter
                    response = requests.post(
                        "http://127.0.0.1:5000/api/analyze",
                        files={"file": uploaded_file},
                        data={
                            "summary_detail": summary_detail,
                            "extraction_ratio": extraction_ratio,
                            "mode": mode  # 🆕 NEW: Send mode
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Analysis Complete")
                        
                        # 🆕 Display mode badge
                        mode_used = result.get('mode', mode)
                        badge_class = "mode-extractive" if mode_used == "extractive" else "mode-hybrid"
                        badge_icon = "📝" if mode_used == "extractive" else "🔄"
                        st.markdown(
                            f"<div class='mode-badge {badge_class}'>{badge_icon} {mode_used.upper()} MODE</div>",
                            unsafe_allow_html=True
                        )

                        # ------------------ SUMMARY ------------------
                        st.markdown("### 📝 Document Summary")
                        
                        # 🆕 Show both summaries in tabs for hybrid mode
                        if mode == "hybrid" and result.get('abstractive_summary'):
                            tab1, tab2 = st.tabs(["✨ Final Summary (Abstractive)", "📄 Extractive Summary"])
                            
                            with tab1:
                                st.markdown(
                                    f"<div class='data-card'>{result.get('summary', 'No summary available.')}</div>",
                                    unsafe_allow_html=True
                                )
                                st.caption(f"✨ LexT5 Refined Summary ({result['statistics'].get('final_summary_length', 0)} words)")
                            
                            with tab2:
                                st.markdown(
                                    f"<div class='data-card'>{result.get('extractive_summary', 'No extractive summary available.')}</div>",
                                    unsafe_allow_html=True
                                )
                                st.caption(f"📝 TextRank + TF-IDF ({result['statistics'].get('extractive_summary_length', 0)} words)")
                        else:
                            # Extractive-only mode
                            st.markdown(
                                f"<div class='data-card'>{result.get('summary', 'No summary available.')}</div>",
                                unsafe_allow_html=True
                            )
                            st.caption(f"📝 TextRank + TF-IDF Extractive Summary ({result['statistics'].get('final_summary_length', 0)} words)")

                        # ------------------ STATISTICS ------------------
                        st.markdown("### 📊 Document Statistics")
                        stats = result.get("statistics", {})
                        if stats:
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Original Words", stats.get('word_count', 'N/A'))
                            with col2:
                                st.metric("Summary Words", stats.get('final_summary_length', 'N/A'))
                            with col3:
                                st.metric("Compression", stats.get('compression_ratio', 'N/A'))
                            with col4:
                                st.metric("Sentences", stats.get('sentence_count', 'N/A'))
                        
                        # 🆕 Additional stats in cards
                        st.markdown(f"<div class='data-card'><strong>Extraction Ratio:</strong> {stats.get('extraction_ratio', 0)*100:.0f}%</div>", unsafe_allow_html=True)
                        if mode == "hybrid":
                            st.markdown(f"<div class='data-card'><strong>Extractive Length:</strong> {stats.get('extractive_summary_length', 0)} words</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='data-card'><strong>Abstractive Length:</strong> {stats.get('abstractive_summary_length', 0)} words</div>", unsafe_allow_html=True)

                        # ------------------ METADATA ------------------
                        st.markdown("### 📂 Extracted Metadata")
                        metadata = result.get("metadata", {})
                        if metadata and not metadata.get("error"):
                            for key, value in metadata.items():
                                if value:  # Only show non-empty values
                                    display_value = ", ".join(value) if isinstance(value, list) else value
                                    st.markdown(
                                        f"<div class='data-card'><strong>{key.replace('_', ' ').title()}:</strong> {display_value}</div>",
                                        unsafe_allow_html=True
                                    )
                        else:
                            st.info("No metadata extracted.")

                        # ------------------ KEY FINDINGS ------------------
                        st.markdown("### 🔍 Key Findings")
                        findings = result.get("key_findings", [])
                        if findings:
                            for i, finding in enumerate(findings, 1):
                                st.markdown(
                                    f"<div class='data-card'><strong>{i}.</strong> {finding}</div>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.info("No key findings detected.")

                        # ------------------ DOCUMENT INFO ------------------
                        with st.expander("📄 Document Information"):
                            doc_info = result.get("document", {})
                            if doc_info:
                                st.json(doc_info)

                        # ------------------ DOWNLOAD OPTIONS ------------------
                        st.markdown("### 💾 Download Results")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.download_button(
                                label="📄 Download Summary (TXT)",
                                data=result.get('summary', ''),
                                file_name=f"summary_{mode}_{uploaded_file.name.replace('.pdf', '')}.txt",
                                mime="text/plain",
                                use_container_width=True
                            )
                        
                        with col2:
                            st.download_button(
                                label="📊 Download Full Report (JSON)",
                                data=json.dumps(result, indent=2),
                                file_name=f"report_{mode}_{uploaded_file.name.replace('.pdf', '')}.json",
                                mime="application/json",
                                use_container_width=True
                            )

                    else:
                        error_msg = response.json().get('error', 'Unknown error')
                        st.error(f"❌ Server Error ({response.status_code}): {error_msg}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ Could not connect to backend. Make sure the Flask server is running on http://127.0.0.1:5000")
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")

else:
    # Search functionality placeholder
    st.info("🔎 Search functionality will be added soon.")
    st.markdown("""
    <div class="info-box">
    <strong>Coming Soon:</strong><br>
    • Vector search across legal database<br>
    • Semantic similarity search<br>
    • Case law retrieval<br>
    • Document clustering
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------
# FOOTER
# -----------------------------------
st.markdown("""
<footer>
<hr>
<p>© 2025 Legal Document Summarization Tool | Powered by TextRank + TF-IDF + LexT5</p>
<p style="font-size:0.8rem;">Optimized for Indian Legal Documents</p>
</footer>
""", unsafe_allow_html=True)
