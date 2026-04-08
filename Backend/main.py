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

app = FastAPI(title="Image Captioning API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load models and data
print("Loading models...")

BASE_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = BASE_DIR.parent / "Reserch"

# Load ResNet50 for feature extraction
resnet_model = ResNet50(weights='imagenet', input_shape=(224, 224, 3))
feature_model = Model(resnet_model.input, resnet_model.layers[-2].output)

# Load word mappings
with open(RESEARCH_DIR / 'word_to_idx.pkl', 'rb') as f:
    word_to_idx = pickle.load(f)

with open(RESEARCH_DIR / 'idx_to_word.pkl', 'rb') as f:
    idx_to_word = pickle.load(f)

# Load the trained captioning model (using the last checkpoint)
model_path = RESEARCH_DIR / 'model_checkpoints' / 'model_19.h5'
caption_model = load_model(model_path)

VOCAB_SIZE = len(word_to_idx) + 1
max_len = 38  # Updated to match the model's expected shape of 38

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

    try:
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
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Image Captioning API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "description": "Image Captioning API is running smoothly."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)