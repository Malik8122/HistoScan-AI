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
        pass  # already started


threading.Thread(target=start_metrics_server, daemon=True).start()

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="HistoScan AI",
    page_icon="🧬",
    layout="wide"
)

# -------------------------------
# Custom CSS — minimal & clean
# -------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background-color: #f8f9fa;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
        color: white;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    .stButton > button {
        background-color: #111827;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 2rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        width: 100%;
        transition: background 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #374151;
        color: white;
    }

    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 20px 24px;
        margin-top: 16px;
    }

    h1 { font-weight: 600; color: #111827; }
    h3 { font-weight: 500; color: #374151; }
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
        st.error(f"❌ Model loading failed: {e}")
        st.stop()


model = load_model()

# -------------------------------
# Sidebar
# -------------------------------
with st.sidebar:
    st.markdown("## 🧬 HistoScan AI")
    st.divider()
    st.markdown("**Status:** 🟢 Operational")
    st.divider()
    st.caption("Analyzes histopathological slides for malignancy detection.")
    st.warning("⚠️ Educational Use Only. Not for medical diagnosis.")
    st.divider()
    st.caption("Metrics available at `:8000/metrics`")

# -------------------------------
# Header
# -------------------------------
st.title("HistoScan AI")
st.markdown("Histopathology image classification for breast cancer detection.")
st.divider()

# -------------------------------
# Layout
# -------------------------------
col1, col2 = st.columns([1, 1], gap="large")

# -------------------------------
# Upload
# -------------------------------
with col1:
    st.markdown("### Upload Image")
    uploaded_file = st.file_uploader(
        "Drop a histopathology image (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        label_visibility="visible"
    )

    if uploaded_file:
        UPLOAD_COUNTER.inc()
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Uploaded Image", use_container_width=True)

# -------------------------------
# Prediction
# -------------------------------
with col2:
    st.markdown("### Diagnostic Result")

    if uploaded_file is not None:

        def preprocess(img):
            img = img.resize((224, 224))
            img_arr = np.array(img)

            if len(img_arr.shape) == 2:
                img_arr = np.stack((img_arr,) * 3, axis=-1)

            img_arr = np.expand_dims(img_arr, axis=0)
            return img_arr

        if st.button("Run Analysis"):
            with st.spinner("Analyzing..."):
                try:
                    start = time.time()

                    processed_img = preprocess(image)
                    prediction = model.predict(processed_img)[0][0]

                    latency = time.time() - start

                    is_malignant = prediction > 0.5
                    confidence = prediction if is_malignant else (1 - prediction)
                    label = "Malignant" if is_malignant else "Benign"

                    # Track metrics
                    PRED_COUNTER.labels(result=label.lower()).inc()
                    PRED_LATENCY.observe(latency)

                    st.divider()

                    if is_malignant:
                        st.error(f"### ⚠️ {label}")
                    else:
                        st.success(f"### ✅ {label}")

                    st.metric("Confidence", f"{confidence * 100:.2f}%")
                    st.metric("Latency", f"{latency * 1000:.0f} ms")
                    st.progress(float(confidence))

                except Exception as e:
                    st.error(f"❌ Prediction failed: {e}")
    else:
        st.info("Upload an image on the left to begin.")