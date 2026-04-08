# NLP Image Captioning - Cloud Deployment Guide

## Overview
Deploy your Image Captioning application using:
- **Streamlit** - Frontend UI (free hosting on Streamlit Cloud)
- **Supabase** - Backend database (PostgreSQL)
- **HuggingFace Spaces** - Backend API (optional alternative)

---

## Part 1: Prepare Repository for GitHub

### Step 1: Create GitHub Repository
1. Go to [github.com](https://github.com) and create a new repository named `nlp-image-captioning`
2. Clone it locally:
```bash
git clone https://github.com/your-username/nlp-image-captioning.git
cd nlp-image-captioning
```

### Step 2: Copy Your Project Files
Copy the following from your current project:
```
nlp-image-captioning/
├── Backend/
│   ├── main.py
│   ├── requirements.txt
│   └── model_checkpoints/
│       └── model_2.h5
├── Reserch/
│   └── examples/
│       ├── eg1.jpg
│       ├── eg2.jpg
│       └── ...
├── streamlit_app.py (new - see below)
├── requirements_prod.txt (new - see below)
└── README.md
```

---

## Part 2: Streamlit Frontend Deployment

### Step 1: Create Streamlit App
Create `streamlit_app.py` in the root directory:

```python
import streamlit as st
import requests
from PIL import Image
import io

st.set_page_config(
    page_title="NeuralVision - Image Captioning",
    page_icon="🎨",
    layout="centered"
)

# Production API endpoint (use environment variable)
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.markdown("""
    <style>
    .header { text-align: center; margin-bottom: 2rem; }
    .caption-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
        border-left: 4px solid #0066cc;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="header"><h1>🎨 NeuralVision</h1><p>AI-Powered Image Captioning</p></div>', unsafe_allow_html=True)

# File uploader
uploaded_file = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp"],
    help="Supports JPG, PNG, and WEBP formats"
)

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Uploaded Image")
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
    
    with col2:
        st.subheader("Image Details")
        st.write(f"**Filename:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
        st.write(f"**Type:** {uploaded_file.type}")
    
    if st.button("🚀 Generate Caption", use_container_width=True, type="primary"):
        with st.spinner("Analyzing image..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(f"{API_URL}/caption", files=files, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    caption = data.get("caption", "No caption generated")
                    
                    st.markdown(f"""
                    <div class="caption-box">
                        <h3>✨ AI Analysis Result</h3>
                        <p style="font-size: 1.1em; color: #333;">"{caption}"</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.success("Caption generated successfully!")
                else:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Failed to generate caption")
                    st.error(f"Error: {error_msg}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the backend. Make sure it's running.")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out.")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")

else:
    st.info("👆 Start by uploading an image to generate a caption using AI")

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666;">
    <p>NeuralVision AI Captioning System</p>
    </div>
    """,
    unsafe_allow_html=True
)
```

### Step 2: Create Production Requirements
Create `requirements_prod.txt`:
```
streamlit==1.28.0
requests==2.31.0
pillow==10.1.0
```

### Step 3: Deploy to Streamlit Cloud
1. Push to GitHub:
```bash
git add .
git commit -m "Add Streamlit deployment files"
git push origin main
```

2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" → Select your GitHub repository
4. Set main file path: `streamlit_app.py`
5. Add secrets (click "Advanced settings" → "Secrets"):
```
API_URL="https://your-backend-api.com"
```

---

## Part 3: Backend Deployment Options

### Option A: Render.com (Recommended - Free tier available)

1. Create account at [render.com](https://render.com)
2. Create `render.yaml` in root:
```yaml
services:
  - type: web
    name: nlp-image-captioning-api
    runtime: python311
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn Backend.main:app --host 0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
```

3. Deploy:
```bash
git push origin main
```
4. Connect GitHub to Render and deploy
5. Copy your API URL and add to Streamlit secrets

### Option B: HuggingFace Spaces

1. Create account at [huggingface.co](https://huggingface.co)
2. Create new Space (Docker or Python)
3. Upload your Backend files
4. Create `app.py` (same as main.py)
5. HF Spaces will auto-deploy with public URL

### Option C: Railway.app

1. Go to [railway.app](https://railway.app)
2. Connect GitHub
3. Create new project from repository
4. Set start command: `uvicorn Backend.main:app --host 0.0.0.0`
5. Deploy automatically

---

## Part 4: Database Setup (Optional - with Supabase)

### Step 1: Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Get your `PROJECT_URL` and `API_KEY`

### Step 2: Update Backend for Database
Add to `Backend/main.py`:
```python
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.post("/save-caption")
async def save_caption(image_url: str, caption: str):
    """Save generated caption to database"""
    data = supabase.table("captions").insert({
        "image_url": image_url,
        "caption": caption,
        "created_at": datetime.now().isoformat()
    }).execute()
    return {"status": "saved", "id": data.data[0]["id"]}
```

---

## Production Checklist

- [ ] Update API endpoint in Streamlit secrets
- [ ] Add CORS properly for production domain
- [ ] Set `DEBUG=False` in FastAPI
- [ ] Use environment variables for all secrets
- [ ] Add `.gitignore`:
```
__pycache__/
*.pyc
.env
.venv/
temp_*
```

- [ ] Update README with deployment links
- [ ] Test all endpoints before deploying
- [ ] Monitor logs on hosting platform
- [ ] Set up error tracking (Sentry optional)

---

## Quick Deployment Summary

1. **Frontend:** Push to GitHub → Connect to Streamlit Cloud
2. **Backend:** Push to GitHub → Connect to Render/Railway/HF Spaces
3. **Database:** (Optional) Set up Supabase and add credentials
4. **Environment Variables:** Configure in hosting platform settings

---

## Troubleshooting

**Streamlit can't reach backend:**
- Check API_URL in Streamlit secrets
- Verify CORS settings in FastAPI
- Check backend logs on hosting platform

**Model loading errors:**
- Ensure model files are in git or uploaded separately
- Check file paths in production environment

**Slow performance:**
- Consider caching model in memory
- Use smaller model or GPU hosting (paid options)

---

## Support & Resources

- Streamlit Docs: https://docs.streamlit.io
- FastAPI Docs: https://fastapi.tiangolo.com
- Render Docs: https://render.com/docs
- Supabase Docs: https://supabase.com/docs
