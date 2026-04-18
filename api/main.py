from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import os

app = FastAPI(title="Socratic API")

# -----------------------------
# Load models (at startup)
# -----------------------------

print("Loading models...")

ethics_model = pickle.load(open("models/ethics_model.pkl", "rb"))
fallacy_model = pickle.load(open("models/fallacy_model.pkl", "rb"))

print("Models loaded successfully")


# -----------------------------
# Request schema
# -----------------------------

class TextRequest(BaseModel):
    text: str


# -----------------------------
# Basic routes
# -----------------------------

@app.get("/")
def root():
    return {"message": "Socratic API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# Prediction endpoints
# -----------------------------

@app.post("/predict/ethics")
def predict_ethics(req: TextRequest):
    pred = ethics_model.predict([req.text])[0]
    return {
        "input": req.text,
        "prediction": pred
    }

@app.post("/predict/fallacy")
def predict_fallacy(req: TextRequest):
    pred = fallacy_model.predict([req.text])[0]
    return {
        "input": req.text,
        "prediction": pred
    }