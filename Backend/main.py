from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import pickle
import os
from pathlib import Path
from threading import Lock

app = FastAPI(title="Image Captioning API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = BASE_DIR.parent / "Reserch"

# Models are loaded lazily on first /caption call so /health stays fast on cold starts.
resnet_model = None
feature_model = None
word_to_idx = None
idx_to_word = None
caption_model = None
VOCAB_SIZE = None
max_len = 38  # Updated to match the model's expected shape of 38

models_loaded = False
model_load_error = None
model_lock = Lock()


def load_models_once():
    global resnet_model, feature_model, word_to_idx, idx_to_word
    global caption_model, VOCAB_SIZE, models_loaded, model_load_error

    if models_loaded:
        return

    with model_lock:
        if models_loaded:
            return

        print("Loading models...")

        required_files = [
            RESEARCH_DIR / 'word_to_idx.pkl',
            RESEARCH_DIR / 'idx_to_word.pkl',
            RESEARCH_DIR / 'model_checkpoints' / 'model_19.h5',
        ]
        missing_files = [str(path) for path in required_files if not path.exists()]
        if missing_files:
            model_load_error = f"Missing required model files: {missing_files}"
            raise FileNotFoundError(model_load_error)

        try:
            resnet_model = ResNet50(weights='imagenet', input_shape=(224, 224, 3))
            feature_model = Model(resnet_model.input, resnet_model.layers[-2].output)

            with open(RESEARCH_DIR / 'word_to_idx.pkl', 'rb') as f:
                word_to_idx = pickle.load(f)

            with open(RESEARCH_DIR / 'idx_to_word.pkl', 'rb') as f:
                idx_to_word = pickle.load(f)

            model_path = RESEARCH_DIR / 'model_checkpoints' / 'model_19.h5'
            caption_model = load_model(model_path)

            VOCAB_SIZE = len(word_to_idx) + 1
            models_loaded = True
            model_load_error = None
        except Exception as exc:
            model_load_error = str(exc)
            raise

def preprocess_image(img_path):
    """Preprocess image for ResNet50"""
    img = image.load_img(img_path, target_size=(224, 224))
    img = image.img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = preprocess_input(img)
    return img

def encode_image(img_path):
    """Extract features from image"""
    img = preprocess_image(img_path)
    feature_vector = feature_model.predict(img, verbose=0)
    return feature_vector.reshape((-1,))

def predict_caption(photo):
    """Generate caption for the image"""
    in_text = 'startseq'
    for i in range(max_len):
        sequence = [word_to_idx[w] for w in in_text.split() if w in word_to_idx]
        sequence = tf.keras.preprocessing.sequence.pad_sequences([sequence], maxlen=max_len, padding='post')
        
        yhat = caption_model.predict([photo, sequence], verbose=0)
        yhat = np.argmax(yhat)
        
        word = idx_to_word.get(yhat, '')
        if word is None:
            break
        in_text += ' ' + word
        if word == 'endseq':
            break
    final = in_text.split()
    final = final[1:-1]  # Remove 'startseq' and 'endseq'
    final = ' '.join(final)
    return final

@app.post("/caption")
async def generate_caption(file: UploadFile = File(...)):
    """Endpoint to generate caption for uploaded image"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    temp_path = None
    try:
        load_models_once()

        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract features
        photo = encode_image(temp_path)
        photo = photo.reshape((1, 2048))
        
        # Generate caption
        caption = predict_caption(photo)
        
        # Clean up
        os.remove(temp_path)
        
        return {"caption": caption}
    
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Image Captioning API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "description": "Image Captioning API is running smoothly.",
        "models_loaded": models_loaded,
        "model_load_error": model_load_error,
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)