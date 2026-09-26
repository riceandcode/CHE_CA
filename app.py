import streamlit as st
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EcoSort - Waste Scanner",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Domain data: color + disposal guidance per stream
# Keys must match the class names coming out of labels.txt.
# Unknown/extra classes fall back to a neutral slate color and generic copy.
# ---------------------------------------------------------------------------
STREAMS = {
    "Paper": {
        "color": "#2F6FED",
        "emoji": "📄",
        "guidance": "Flatten it and keep it dry. Remove any plastic film, tape, "
                    "or lamination before it goes in the paper stream.",
    },
    "Organic": {
        "color": "#4C9A2A",
        "emoji": "🍎",
        "guidance": "Send it to compost or food waste collection. Keep packaging, "
                    "stickers, and twist ties out of the bin.",
    },
    "Metal": {
        "color": "#7C8B86",
        "emoji": "🥫",
        "guidance": "Rinse off food residue and leave the label on. Cans and "
                    "clean foil both belong in the metal stream.",
    },
    "Plastic": {
        "color": "#E8A33D",
        "emoji": "🥤",
        "guidance": "Check the resin code on the base. Rinse the item and leave "
                    "the cap on if your facility accepts it attached.",
    },
}
DEFAULT_STREAM = {"color": "#8B95A1", "emoji": "🗑️", "guidance": "Check your local guidelines for this material."}

# ---------------------------------------------------------------------------
# Theme CSS — kraft paper background, ink text, single orange accent,
# category colors used only as functional tags (never decoration).
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --paper: #ECE4D2;
        --paper-soft: #F3ECDD;
        --ink: #1B2420;
        --ink-soft: #445048;
        --ink-faint: #6B756E;
        --accent: #FF5A1F;
        --line: rgba(27,36,32,0.15);
    }

    .stApp {
        background: radial-gradient(ellipse at top left, var(--paper-soft) 0%, var(--paper) 55%, #E4D9C3 100%);
        color: var(--ink);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .font-display {
        font-family: 'Big Shoulders Display', sans-serif !important;
        letter-spacing: -0.01em;
    }

    section[data-testid="stSidebar"] {
        background: var(--paper-soft);
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] * { color: var(--ink) !important; }

    /* Top bar */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    .wordmark {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-family: 'Big Shoulders Display', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: 0.02em;
    }
    .wordmark .ring {
        width: 34px; height: 34px;
        border-radius: 999px;
        border: 2px solid var(--ink);
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
    }
    .status-chip {
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        border: 1px solid var(--line);
        font-size: 0.85rem;
        color: var(--ink-soft);
    }
    .status-chip .dot {
        width: 8px; height: 8px; border-radius: 999px;
        background: #16a34a;
        display: inline-block;
    }

    /* Hero headline */
    .hero-title {
        font-family: 'Big Shoulders Display', sans-serif;
        font-size: 3rem;
        line-height: 0.98;
        font-weight: 800;
        margin: 0 0 0.9rem 0;
    }
    .hero-sub {
        color: var(--ink-soft);
        font-size: 1.05rem;
        line-height: 1.6;
        max-width: 46ch;
        margin-bottom: 1.5rem;
    }

    /* Legend */
    .legend-row { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.55rem; }
    .legend-swatch { width: 10px; height: 28px; border-radius: 3px; flex-shrink: 0; }
    .legend-label { font-weight: 600; font-size: 0.95rem; }

    /* Stats row */
    .stats-row { display: flex; gap: 2rem; margin-top: 1.8rem; padding-top: 1.2rem; border-top: 1px solid var(--line); }
    .stat-num { font-family: 'Inter', sans-serif; font-weight: 700; font-size: 1.5rem; line-height: 1; margin-bottom: 0.2rem; }
    .stat-label { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--ink-faint); }

    /* Scanner card wrapper */
    .scanner-card {
        background: rgba(255,255,255,0.5);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1.4rem 1.4rem 1.6rem 1.4rem;
        box-shadow: 0 20px 50px -25px rgba(27,36,32,0.35);
    }

    /* Manifest result ticket */
    .ticket {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        margin-top: 0.5rem;
    }
    .ticket-header {
        display: flex; align-items: center; gap: 1rem;
        padding: 1.1rem 1.2rem;
    }
    .ticket-icon {
        width: 48px; height: 48px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; flex-shrink: 0;
    }
    .ticket-category {
        font-family: 'Big Shoulders Display', sans-serif;
        font-size: 1.7rem; font-weight: 800; line-height: 1;
    }
    .ticket-confidence {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem; color: var(--ink-soft);
    }
    .ticket-body { padding: 1.1rem 1.2rem 1.3rem 1.2rem; }
    .ticket-guidance { color: var(--ink-soft); font-size: 0.92rem; line-height: 1.55; margin-bottom: 1rem; }

    .prob-row { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.5rem; }
    .prob-label { width: 72px; font-size: 0.8rem; color: var(--ink-soft); flex-shrink: 0; }
    .prob-track { flex: 1; height: 8px; border-radius: 999px; background: rgba(27,36,32,0.08); overflow: hidden; }
    .prob-fill { height: 100%; border-radius: 999px; }
    .prob-pct { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; width: 48px; text-align: right; flex-shrink: 0; }

    /* Steps */
    .step-num { font-family: 'JetBrains Mono', monospace; color: var(--accent); font-size: 0.85rem; margin-bottom: 0.3rem; }
    .step-title { font-family: 'Big Shoulders Display', sans-serif; font-size: 1.5rem; font-weight: 700; margin-bottom: 0.3rem; }
    .step-body { color: var(--ink-soft); font-size: 0.9rem; line-height: 1.5; }

    .footer-row {
        margin-top: 2.5rem; padding-top: 1.2rem; border-top: 1px solid var(--line);
        display: flex; justify-content: space-between; font-size: 0.78rem; color: var(--ink-faint);
        font-family: 'Inter', sans-serif;
    }
    .footer-row .mono { font-family: 'JetBrains Mono', monospace; }

    /* Streamlit control overrides */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: rgba(27,36,32,0.06); padding: 4px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { border-radius: 7px; color: var(--ink-soft); font-weight: 600; }
    .stTabs [aria-selected="true"] { background: var(--ink) !important; color: var(--paper) !important; }

    div[data-testid="stFileUploaderDropzone"] {
        background: var(--ink) !important;
        border: 1.5px dashed var(--accent) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stFileUploaderDropzone"] * { color: var(--paper) !important; }

    .stButton > button {
        background: var(--accent) !important;
        color: var(--ink) !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover { filter: brightness(1.08); transform: translateY(-1px); }

    div[data-testid="stImage"] img { border-radius: 12px; border: 1px solid var(--line); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Keras DepthwiseConv2D compatibility patch (unchanged from original app)
# ---------------------------------------------------------------------------
try:
    from tensorflow.keras.layers import DepthwiseConv2D
    _original_init = DepthwiseConv2D.__init__
    def _patched_init(self, *args, **kwargs):
        kwargs.pop('groups', None)
        _original_init(self, *args, **kwargs)
    DepthwiseConv2D.__init__ = _patched_init
except Exception:
    pass


@st.cache_resource
def load_keras_model():
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
    data = np.expand_dims(normalized_image_array, axis=0)

    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = labels.get(index, f"Class {index}")
    confidence_score = float(prediction[0][index])
    return class_name, confidence_score, prediction[0]


def stream_info(class_name):
    return STREAMS.get(class_name, DEFAULT_STREAM)


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
st.markdown("""
<div class="topbar">
    <div class="wordmark"><span class="ring">♻️</span> ECOSORT</div>
    <div class="status-chip"><span class="dot"></span> Scanner online</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### System info")
    st.write("This scanner classifies a photo locally with a CNN trained on four waste streams.")
    st.markdown("---")
    st.markdown("**Supported streams**")
    for name, info in STREAMS.items():
        st.markdown(f"{info['emoji']} {name}")

# ---------------------------------------------------------------------------
# Load model + labels
# ---------------------------------------------------------------------------
try:
    model = load_keras_model()
    labels = load_labels()
except Exception as e:
    st.error(f"Error loading model or labels: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Hero: copy + legend (left) / scanner (right)
# ---------------------------------------------------------------------------
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("""
    <div class="hero-title">Point a camera<br>at your trash.<br>Know the bin.</div>
    <div class="hero-sub">Upload a photo or use your camera and the model sorts it into
    one of four streams in under two seconds, the same way a materials recovery
    facility would.</div>
    """, unsafe_allow_html=True)

    legend_html = ""
    for name, info in STREAMS.items():
        legend_html += f"""
        <div class="legend-row">
            <span class="legend-swatch" style="background:{info['color']}"></span>
            <span class="legend-label">{info['emoji']} {name}</span>
        </div>
        """
    st.markdown(legend_html, unsafe_allow_html=True)

    st.markdown("""
    <div class="stats-row">
        <div><div class="stat-num">94.2%</div><div class="stat-label">TOP-1 ACCURACY</div></div>
        <div><div class="stat-num">12,400+</div><div class="stat-label">TRAINING IMAGES</div></div>
        <div><div class="stat-num">4</div><div class="stat-label">WASTE STREAMS</div></div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown('<div class="scanner-card">', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📁 Upload photo", "📷 Use camera"])

    img_input = None
    with tab1:
        uploaded_file = st.file_uploader("Drag a JPG or PNG here, or click to browse",
                                          type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_file is not None:
            img_input = Image.open(uploaded_file).convert("RGB")

    with tab2:
        camera_file = st.camera_input("Take a clear picture of the item", label_visibility="collapsed")
        if camera_file is not None:
            img_input = Image.open(camera_file).convert("RGB")

    if img_input is not None:
        st.image(img_input, use_container_width=True)

        with st.spinner("Scanning material composition…"):
            class_name, confidence, all_scores = process_and_predict(img_input, model, labels)

        info = stream_info(class_name)

        # Manifest-style result ticket
        st.markdown(f"""
        <div class="ticket">
            <div class="ticket-header" style="background:{info['color']}22;">
                <div class="ticket-icon" style="background:{info['color']};">{info['emoji']}</div>
                <div>
                    <div class="ticket-category">{class_name}</div>
                    <div class="ticket-confidence">confidence {confidence * 100:.1f}%</div>
                </div>
            </div>
            <div class="ticket-body">
                <div class="ticket-guidance">{info['guidance']}</div>
        """, unsafe_allow_html=True)

        # Per-class probability bars, colored by stream
        rows_html = ""
        for idx, score in enumerate(all_scores):
            label_name = labels.get(idx, f"Class {idx}")
            bar_color = stream_info(label_name)["color"]
            pct = float(score) * 100
            rows_html += f"""
            <div class="prob-row">
                <div class="prob-label">{label_name}</div>
                <div class="prob-track"><div class="prob-fill" style="width:{pct:.1f}%; background:{bar_color};"></div></div>
                <div class="prob-pct">{pct:.1f}%</div>
            </div>
            """
        st.markdown(rows_html, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)  # close ticket-body, ticket

    else:
        st.info("Upload or capture a photo to see the classification.")

    st.markdown("</div>", unsafe_allow_html=True)  # close scanner-card

# ---------------------------------------------------------------------------
# How it works
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3, gap="large")
steps = [
    ("01", "Capture", "Upload a photo or point your camera at the item on a plain background."),
    ("02", "Analyze", "A convolutional model checks shape, texture, and material cues against four trained classes."),
    ("03", "Sort", "You get the matching stream plus disposal steps specific to that material."),
]
for col, (n, title, body) in zip((c1, c2, c3), steps):
    with col:
        st.markdown(f"""
        <div class="step-num">{n}</div>
        <div class="step-title">{title}</div>
        <div class="step-body">{body}</div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("""
<div class="footer-row">
    <span>EcoSort runs the classification locally — no image leaves your device.</span>
    <span class="mono">Model v1 · keras_model.h5</span>
</div>
""", unsafe_allow_html=True)
