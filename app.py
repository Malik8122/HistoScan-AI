import streamlit as st
import numpy as np
from PIL import Image
import tensorflow as tf
import os
import threading
from prometheus_client import Counter, Histogram, start_http_server
import time

# -------------------------------
# Prometheus Metrics — init once
# -------------------------------
@st.cache_resource
def init_metrics():
    pred_counter = Counter(
        'histoscan_predictions_total',
        'Total predictions made',
        ['result']
    )
    pred_latency = Histogram(
        'histoscan_prediction_latency_seconds',
        'Prediction latency in seconds'
    )
    upload_counter = Counter(
        'histoscan_uploads_total',
        'Total images uploaded'
    )
    return pred_counter, pred_latency, upload_counter


@st.cache_resource
def init_metrics_server():
    try:
        start_http_server(8000)
    except Exception:
        pass
    return True


init_metrics_server()
PRED_COUNTER, PRED_LATENCY, UPLOAD_COUNTER = init_metrics()


def start_metrics_server():
    try:
        start_http_server(8000)
    except Exception:
        pass


threading.Thread(target=start_metrics_server, daemon=True).start()

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="HistoScan AI: Breast Cancer Detection",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------
# Custom CSS — Dark Medical Luxury
# -------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500&display=swap');

    :root {
        --bg-primary: #040b14;
        --bg-secondary: #071020;
        --bg-card: #0a1628;
        --accent-cyan: #00d4ff;
        --accent-green: #00ff88;
        --accent-red: #ff3b6b;
        --accent-amber: #ffb800;
        --text-primary: #e8f4fd;
        --text-muted: #5a7a9a;
        --border: rgba(0, 212, 255, 0.12);
        --border-hover: rgba(0, 212, 255, 0.35);
        --glow-cyan: 0 0 30px rgba(0, 212, 255, 0.15);
        --glow-green: 0 0 30px rgba(0, 255, 136, 0.15);
        --glow-red: 0 0 30px rgba(255, 59, 107, 0.2);
    }

    /* ---- BASE ---- */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: var(--bg-primary);
        color: var(--text-primary);
    }

    .stApp {
        background: var(--bg-primary);
        background-image:
            radial-gradient(ellipse 80% 50% at 50% -20%, rgba(0, 212, 255, 0.06) 0%, transparent 60%),
            radial-gradient(ellipse 40% 30% at 85% 80%, rgba(0, 255, 136, 0.04) 0%, transparent 50%);
    }

    /* ---- SIDEBAR ---- */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    section[data-testid="stSidebar"] .stMarkdown p {
        color: var(--text-muted) !important;
        font-size: 0.82rem;
    }

    /* ---- MAIN CONTENT ---- */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1400px;
    }

    /* ---- TYPOGRAPHY ---- */
    h1 {
        font-family:'Inria Serif', serif !important;
        font-weight: 800 !important;
        font-size: 3rem !important;
        letter-spacing: -0.02em !important;
        color: var(--text-primary) !important;
        line-height: 1.1 !important;
    }

    h2, h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text-primary) !important;
    }

    /* ---- BUTTON ---- */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%) !important;
        color: #040b14 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2.5rem !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.05em !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
        text-transform: uppercase !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 35px rgba(0, 212, 255, 0.5) !important;
    }

    .stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ---- FILE UPLOADER ---- */
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 1.5px dashed var(--border-hover) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        transition: border-color 0.3s ease !important;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-cyan) !important;
        box-shadow: var(--glow-cyan) !important;
    }

    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
    }

    /* ---- METRICS ---- */
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 1rem 1.2rem !important;
    }

    [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-family: 'Space Mono', monospace !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 1.6rem !important;
    }

    /* ---- PROGRESS BAR ---- */
    [data-testid="stProgressBar"] > div {
        background: rgba(0, 212, 255, 0.15) !important;
        border-radius: 999px !important;
    }

    [data-testid="stProgressBar"] > div > div {
        background: linear-gradient(90deg, #00d4ff, #00ff88) !important;
        border-radius: 999px !important;
        box-shadow: 0 0 12px rgba(0, 212, 255, 0.5) !important;
    }

    /* ---- ALERTS ---- */
    .stSuccess {
        background: rgba(0, 255, 136, 0.08) !important;
        border: 1px solid rgba(0, 255, 136, 0.3) !important;
        border-radius: 10px !important;
        color: #00ff88 !important;
    }

    .stError {
        background: rgba(255, 59, 107, 0.08) !important;
        border: 1px solid rgba(255, 59, 107, 0.3) !important;
        border-radius: 10px !important;
        color: #ff3b6b !important;
    }

    .stWarning {
        background: rgba(255, 184, 0, 0.08) !important;
        border: 1px solid rgba(255, 184, 0, 0.25) !important;
        border-radius: 10px !important;
    }

    .stInfo {
        background: rgba(0, 212, 255, 0.06) !important;
        border: 1px solid rgba(0, 212, 255, 0.2) !important;
        border-radius: 10px !important;
        color: var(--text-muted) !important;
    }

    /* ---- DIVIDER ---- */
    hr {
        border-color: var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ---- SPINNER ---- */
    [data-testid="stSpinner"] {
        color: var(--accent-cyan) !important;
    }

    /* ---- IMAGE ---- */
    [data-testid="stImage"] img {
        border-radius: 12px !important;
        border: 1px solid var(--border) !important;
    }

    /* ---- CUSTOM COMPONENTS ---- */
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(0, 212, 255, 0.08);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 999px;
        padding: 4px 14px;
        font-family: 'Space Mono', monospace;
        font-size: 0.72rem;
        color: var(--accent-cyan);
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .hero-badge .dot {
        width: 6px;
        height: 6px;
        background: var(--accent-green);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }

    .stat-row {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .stat-item {
        flex: 1;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }

    .stat-item .stat-val {
        font-family: 'Space Mono', monospace;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--accent-cyan);
    }

    .stat-item .stat-label {
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 2px;
    }

    .section-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .section-label::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    .result-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 1.75rem;
        margin-top: 1rem;
    }

    .result-card.malignant {
        border-color: rgba(255, 59, 107, 0.35);
        background: rgba(255, 59, 107, 0.04);
        box-shadow: var(--glow-red);
    }

    .result-card.benign {
        border-color: rgba(0, 255, 136, 0.35);
        background: rgba(0, 255, 136, 0.03);
        box-shadow: var(--glow-green);
    }

    .result-label {
        font-family: 'Syne', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.01em;
    }

    .result-label.malignant { color: var(--accent-red); }
    .result-label.benign { color: var(--accent-green); }

    .result-sublabel {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-top: 4px;
        font-family: 'Space Mono', monospace;
    }

    .sidebar-logo {
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--accent-cyan) !important;
        letter-spacing: -0.01em;
    }

    .sidebar-section {
        margin: 1.2rem 0;
        padding: 1rem;
        background: rgba(0, 212, 255, 0.04);
        border: 1px solid var(--border);
        border-radius: 8px;
    }

    .sidebar-section p {
        font-size: 0.78rem !important;
        line-height: 1.6 !important;
        color: #5a7a9a !important;
    }

    .mono-tag {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        color: var(--accent-cyan);
        background: rgba(0, 212, 255, 0.08);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid rgba(0, 212, 255, 0.15);
    }

    /* Hide Streamlit default elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

</style>
""", unsafe_allow_html=True)


# -------------------------------
# Load Model
# -------------------------------
@st.cache_resource
def load_model():
    model_path = os.path.join(os.getcwd(), "breakhis_model.h5")
    try:
        model = tf.keras.models.load_model(model_path, compile=False)
        return model
    except Exception as e:
        st.error(f"Model loading failed: {e}")
        st.stop()


model = load_model()


# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🧬 HistoScan AI</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div class="sidebar-section">
        <p>Deep learning pipeline for histopathological slide analysis. Trained on the BreakHis dataset for breast carcinoma classification.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin: 1rem 0;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
            <div style="width:8px;height:8px;background:#00ff88;border-radius:50%;"></div>
            <span style="font-family:'Space Mono',monospace;font-size:0.75rem;color:#00ff88;">SYSTEM ONLINE</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:10px;">
            <div style="width:8px;height:8px;background:#00d4ff;border-radius:50%;"></div>
            <span style="font-family:'Space Mono',monospace;font-size:0.75rem;color:#5a7a9a;">MODEL LOADED</span>
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
            <div style="width:8px;height:8px;background:#00d4ff;border-radius:50%;"></div>
            <span style="font-family:'Space Mono',monospace;font-size:0.75rem;color:#5a7a9a;">METRICS :8000</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="background:rgba(255,184,0,0.08);border:1px solid rgba(255,184,0,0.25);border-radius:8px;padding:10px 12px;">
        <span style="font-size:0.75rem;color:#ffb800;">⚠ Educational use only.<br>Not for clinical diagnosis.</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#2a4a6a;line-height:2;">
        MODEL &nbsp;→ &nbsp;BreakHis CNN<br>
        INPUT &nbsp;&nbsp;→ &nbsp;224 × 224 px<br>
        OUTPUT → &nbsp;Binary Class
    </div>
    """, unsafe_allow_html=True)


# -------------------------------
# Hero Header
# -------------------------------
st.markdown("""
<div class="hero-badge">
    <div class="dot"></div>
    Breast Cancer Detection System
</div>
""", unsafe_allow_html=True)

st.markdown("# HistoScan AI")
st.markdown("""
<p style="color:#5a7a9a;font-size:1.05rem;margin-top:-0.5rem;margin-bottom:1.5rem;max-width:600px;line-height:1.7;">
    Upload a histopathological slide image and receive an instant AI-powered malignancy assessment using deep learning.
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# -------------------------------
# Main Layout
# -------------------------------
col1, spacer, col2 = st.columns([1.1, 0.08, 1])

# ---- LEFT: Upload ----
with col1:
    st.markdown('<div class="section-label">01 &nbsp; Image Input</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop histopathology image here",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        UPLOAD_COUNTER.inc()
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption=f"📁 {uploaded_file.name}", use_container_width=True)

        # Image metadata
        w, h = image.size
        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-top:0.75rem;">
            <span class="mono-tag">W: {w}px</span>
            <span class="mono-tag">H: {h}px</span>
            <span class="mono-tag">RGB</span>
            <span class="mono-tag">{uploaded_file.type.split('/')[-1].upper()}</span>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="
            border: 1.5px dashed rgba(0,212,255,0.2);
            border-radius: 12px;
            padding: 3rem 2rem;
            text-align: center;
            background: rgba(0,212,255,0.02);
        ">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;">🔬</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.8rem;color:#2a4a6a;">
                AWAITING IMAGE INPUT
            </div>
            <div style="font-size:0.78rem;color:#2a4a6a;margin-top:8px;">
                Supports JPG, JPEG, PNG
            </div>
        </div>
        """, unsafe_allow_html=True)


# ---- RIGHT: Analysis ----
with col2:
    st.markdown('<div class="section-label">02 &nbsp; Diagnostic Analysis</div>', unsafe_allow_html=True)

    if uploaded_file is not None:

        def preprocess(img):
            img = img.resize((224, 224))
            img_arr = np.array(img)
            if len(img_arr.shape) == 2:
                img_arr = np.stack((img_arr,) * 3, axis=-1)
            img_arr = np.expand_dims(img_arr, axis=0)
            return img_arr

        if st.button("⚡  Run Analysis"):
            with st.spinner("Processing image through neural network..."):
                try:
                    start = time.time()
                    processed_img = preprocess(image)
                    prediction = model.predict(processed_img)[0][0]
                    latency = time.time() - start

                    is_malignant = prediction > 0.5
                    confidence = prediction if is_malignant else (1 - prediction)
                    label = "Malignant" if is_malignant else "Benign"
                    card_class = "malignant" if is_malignant else "benign"
                    icon = "⚠" if is_malignant else "✓"

                    PRED_COUNTER.labels(result=label.lower()).inc()
                    PRED_LATENCY.observe(latency)

                    # Result Card
                    st.markdown(f"""
                    <div class="result-card {card_class}">
                        <div style="display:flex;align-items:flex-start;justify-content:space-between;">
                            <div>
                                <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#5a7a9a;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;">Classification Result</div>
                                <div class="result-label {card_class}">{icon} &nbsp;{label}</div>
                                <div class="result-sublabel">CONFIDENCE: {confidence * 100:.1f}%</div>
                            </div>
                            <div style="font-size:2.5rem;opacity:0.6;">{"🔴" if is_malignant else "🟢"}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Confidence Bar
                    st.markdown("<div style='margin-top:1rem;margin-bottom:0.4rem;font-family:Space Mono,monospace;font-size:0.68rem;color:#5a7a9a;letter-spacing:0.08em;'>CONFIDENCE SCORE</div>", unsafe_allow_html=True)
                    st.progress(float(confidence))

                    # Stats Row
                    st.markdown(f"""
                    <div class="stat-row">
                        <div class="stat-item">
                            <div class="stat-val">{confidence * 100:.1f}%</div>
                            <div class="stat-label">Confidence</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-val">{latency * 1000:.0f}ms</div>
                            <div class="stat-label">Latency</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-val">224²</div>
                            <div class="stat-label">Input Res.</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Raw score
                    st.markdown(f"""
                    <div style="background:var(--bg-card,#0a1628);border:1px solid rgba(0,212,255,0.1);border-radius:8px;padding:12px 16px;margin-top:0.5rem;">
                        <span style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#5a7a9a;">RAW SCORE &nbsp;</span>
                        <span style="font-family:'Space Mono',monospace;font-size:0.82rem;color:#00d4ff;">{prediction:.6f}</span>
                        <span style="font-family:'Space Mono',monospace;font-size:0.68rem;color:#2a4a6a;float:right;">THRESHOLD: 0.500000</span>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    else:
        st.markdown("""
        <div style="
            border: 1px solid rgba(0,212,255,0.1);
            border-radius: 12px;
            padding: 3rem 2rem;
            text-align: center;
            background: rgba(0,212,255,0.02);
        ">
            <div style="font-size:2.5rem;margin-bottom:0.75rem;opacity:0.4;">📊</div>
            <div style="font-family:'Space Mono',monospace;font-size:0.8rem;color:#2a4a6a;">
                AWAITING INPUT
            </div>
            <div style="font-size:0.78rem;color:#2a4a6a;margin-top:8px;">
                Upload an image to begin analysis
            </div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------
# Footer
# -------------------------------
st.markdown("---")
st.markdown("""
<div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0;">
    <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#2a4a6a;">
        HistoScan AI &nbsp;·&nbsp; BreakHis Model &nbsp;·&nbsp; v2.0
    </div>
    <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#2a4a6a;">
        NOT FOR CLINICAL USE &nbsp;·&nbsp; EDUCATIONAL ONLY
    </div>
</div>
""", unsafe_allow_html=True)