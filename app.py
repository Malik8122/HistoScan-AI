import streamlit as st
import numpy as np
from PIL import Image
import tensorflow as tf
import os

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(
    page_title="HistoScan AI 🚀",
    page_icon="🧬",
    layout="wide"
)

# -------------------------------
# Custom CSS
# -------------------------------
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }

    div.stButton > button:first-child {
        background-color: #007bff;
        color: white;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }

    div.stButton > button:first-child:hover {
        background-color: #0056b3;
        color: white;
        transform: translateY(-2px);
    }

    .result-card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Load Model (FIXED)
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
    st.title("HistoScan AI")
    st.divider()
    st.info("**System Status:** Operational")
    st.caption("This tool analyzes histopathological slides for malignancy detection.")
    st.warning("Educational Use Only. Not for medical diagnosis.")

# -------------------------------
# Main Header
# -------------------------------
st.title("🧬 Breast Cancer Analysis System v2.0")
st.write("Diagnostic assistance tool for histopathology image classification.")

st.info("Upload a histopathology image (RGB). The system will automatically resize and process it.")

# -------------------------------
# Layout
# -------------------------------
col1, col2 = st.columns([1, 1], gap="large")

# -------------------------------
# Upload Section
# -------------------------------
with col1:
    st.subheader("Image Upload")

    uploaded_file = st.file_uploader(
        "Drop histopathology image here",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Current Upload", use_container_width=True)

# -------------------------------
# Prediction Section
# -------------------------------
with col2:
    st.subheader("Analysis")

    if uploaded_file is not None:

        def preprocess(img):
            img = img.resize((224, 224))
            img_arr = np.array(img)

            if len(img_arr.shape) == 2:
                img_arr = np.stack((img_arr,) * 3, axis=-1)

            img_arr = np.expand_dims(img_arr, axis=0)
            return img_arr

        if st.button("Run Diagnostic Analysis"):

            with st.spinner("Processing neural layers..."):

                try:
                    processed_img = preprocess(image)
                    prediction = model.predict(processed_img)[0][0]

                    is_malignant = prediction > 0.5
                    confidence = prediction if is_malignant else (1 - prediction)

                    st.divider()

                    if is_malignant:
                        st.error("### ⚠️ Classification: Malignant")
                        st.progress(float(prediction))
                    else:
                        st.success("### ✅ Classification: Benign")
                        st.progress(float(1 - prediction))

                    st.metric(
                        label="Confidence Level",
                        value=f"{confidence * 100:.2f}%"
                    )

                except Exception as e:
                    st.error(f"❌ Prediction failed: {e}")

    else:
        st.info("Please upload a sample image to begin the analysis.")