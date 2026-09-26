import streamlit as st
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf

# Configure Streamlit page layout
st.set_page_config(
    page_title="EcoAI - Waste Classifier",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI Enhancement
st.markdown("""
<style>
    /* Dark Eco Theme Palette */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Header Card */
    .header-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        margin-bottom: 24px;
    }
    
    .badge {
        background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin-top: 10px;
        background: linear-gradient(90deg, #34d399, #10b981, #6ee7b7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .sub-text {
        color: #94a3b8;
        font-size: 1.05rem;
    }

    /* Result Metric Card */
    .prediction-card {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid #10b981;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-top: 15px;
    }

    .prediction-title {
        color: #34d399;
        font-size: 1.8rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .confidence-score {
        color: #cbd5e1;
        font-size: 1.1rem;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Patch for Keras DepthwiseConv2D compatibility
try:
    from tensorflow.keras.layers import DepthwiseConv2D
    _original_init = DepthwiseConv2D.__init__
    def _patched_init(self, *args, **kwargs):
        kwargs.pop('groups', None)
        _original_init(self, *args, **kwargs)
    DepthwiseConv2D.__init__ = _patched_init
except Exception as e:
    pass

@st.cache_resource
def load_keras_model():
    # Update filename if your model file has a different name
    return tf.keras.models.load_model("keras_model.h5")

def load_labels():
    labels = {}
    try:
        with open("labels.txt", "r") as f:
            for line in f.readlines():
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    labels[int(parts[0])] = parts[1]
                else:
                    labels[len(labels)] = line.strip()
    except FileNotFoundError:
        labels = {0: "Plastic", 1: "Paper", 2: "Metal", 3: "Organic"}
    return labels

def process_and_predict(image, model, labels):
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    data = np.ndim(normalized_image_array)
    data = np.expand_dims(normalized_image_array, axis=0)
    
    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = labels.get(index, f"Class {index}")
    confidence_score = float(prediction[0][index])
    return class_name, confidence_score, prediction[0]

# --- UI HEADER ---
st.markdown("""
<div class="header-card">
    <span class="badge">ECO AI ASSISTANT</span>
    <h1 class="main-title">♻️ Waste Classification System</h1>
    <p class="sub-text">Upload or capture an image to identify recyclables and receive instant sorting recommendations.</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR INFO ---
with st.sidebar:
    st.header("📋 System Info")
    st.info("This AI application processes images locally using deep learning to segregate waste types efficiently.")
    st.markdown("---")
    st.markdown("**Supported Classes:**")
    st.markdown("- 🥤 Plastic\n- 📄 Paper\n- 🥫 Metal\n- 🍎 Organic")

# Load AI assets
try:
    model = load_keras_model()
    labels = load_labels()
except Exception as e:
    st.error(f"Error loading model or labels: {e}")
    st.stop()

# --- MAIN CONTENT LAYOUT ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📸 Step 1: Input Image")
    tab1, tab2 = st.tabs(["📁 Upload Image", "📷 Use Webcam"])
    
    img_input = None
    with tab1:
        uploaded_file = st.file_uploader("Select a JPG or PNG file", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            img_input = Image.open(uploaded_file).convert("RGB")
            
    with tab2:
        camera_file = st.camera_input("Take a clear picture of the item")
        if camera_file is not None:
            img_input = Image.open(camera_file).convert("RGB")

    if img_input is not None:
        st.image(img_input, caption="Input Preview", use_container_width=True)

with col2:
    st.subheader("📊 Step 2: Prediction Results")
    
    if img_input is not None:
        with st.spinner("Analyzing waste sample..."):
            class_name, confidence, all_scores = process_and_predict(img_input, model, labels)
            
        st.markdown(f"""
        <div class="prediction-card">
            <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">DETECTED CATEGORY</p>
            <div class="prediction-title">{class_name}</div>
            <div class="confidence-score">Confidence: <strong>{confidence * 100:.2f}%</strong></div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Class Probabilities")
        for idx, score in enumerate(all_scores):
            label_name = labels.get(idx, f"Class {idx}")
            st.write(f"**{label_name}**")
            st.progress(float(score))
    else:
        st.info("👈 Upload or capture an image on the left to display classification details.")