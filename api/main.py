import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("socratic_ai")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Socratic AI",
    description="Fallacy detection and ethical reasoning powered by ML",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Model registry ────────────────────────────────────────────────────────────
MODELS: dict = {}

MODEL_PATHS = {
    "fallacy": Path("models/fallacy_model.pkl"),
    "ethics":  Path("models/ethics_model.pkl"),
}


def load_model(name: str, path: Path) -> Optional[object]:
    if not path.exists():
        log.warning("Model file not found: %s – predictions will be mocked.", path)
        return None
    try:
        with open(path, "rb") as f:
            model = pickle.load(f)
        log.info("Loaded model '%s' from %s", name, path)
        return model
    except Exception as exc:
        log.error("Failed to load model '%s': %s", name, exc)
        return None


@app.on_event("startup")
def startup_event():
    log.info("Starting Socratic AI …")
    for name, path in MODEL_PATHS.items():
        MODELS[name] = load_model(name, path)
    log.info("Startup complete. Loaded models: %s", [k for k, v in MODELS.items() if v])


# ── Schemas ───────────────────────────────────────────────────────────────────
class TextInput(BaseModel):
    text: str


class PredictionResult(BaseModel):
    prediction: str
    confidence: float


class AnalysisResult(BaseModel):
    fallacy: PredictionResult
    ethics: PredictionResult
    summary: str


# ── Helpers ───────────────────────────────────────────────────────────────────
FALLACY_LABELS = [
    "Ad Hominem", "Appeal to Authority", "False Dichotomy",
    "Bandwagon", "Straw Man", "Slippery Slope",
    "Circular Reasoning", "Hasty Generalization", "No Fallacy Detected",
]

ETHICS_LABELS = [
    "Privacy Violation", "Conflict of Interest", "Discrimination",
    "Deception", "Harm to Others", "Ethical Action",
]


def _predict(model_name: str, text: str) -> PredictionResult:
    model = MODELS.get(model_name)

    if model is not None:
        try:
            proba = model.predict_proba([text])[0]
            idx = int(np.argmax(proba))
            label = model.classes_[idx]
            confidence = round(float(proba[idx]), 4)
            return PredictionResult(prediction=label, confidence=confidence)
        except Exception as exc:
            log.error("Prediction error (%s): %s", model_name, exc)
            raise HTTPException(status_code=500, detail=f"Model error: {exc}") from exc

    # ── Mock fallback when model file is absent ──────────────────────────────
    import random, hashlib
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)

    if model_name == "fallacy":
        label = rng.choice(FALLACY_LABELS)
    else:
        label = rng.choice(ETHICS_LABELS)

    confidence = round(rng.uniform(0.62, 0.97), 4)
    return PredictionResult(prediction=label, confidence=confidence)


def _build_summary(fallacy: PredictionResult, ethics: PredictionResult) -> str:
    parts = []
    if fallacy.prediction != "No Fallacy Detected":
        parts.append(
            f"The argument contains a **{fallacy.prediction}** "
            f"(confidence {fallacy.confidence:.0%})."
        )
    else:
        parts.append("No logical fallacy was detected in the argument.")

    if ethics.prediction != "Ethical Action":
        parts.append(
            f"From an ethical standpoint, the situation raises concerns about "
            f"**{ethics.prediction}** (confidence {ethics.confidence:.0%})."
        )
    else:
        parts.append("The action appears ethically sound based on available context.")

    return " ".join(parts)


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Socratic AI API running"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "models_loaded": {k: (v is not None) for k, v in MODELS.items()},
    }


@app.post("/predict/fallacy", response_model=PredictionResult)
def predict_fallacy(body: TextInput):
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty.")
    log.info("Fallacy request: %.80s…", body.text)
    return _predict("fallacy", body.text)


@app.post("/predict/ethics", response_model=PredictionResult)
def predict_ethics(body: TextInput):
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty.")
    log.info("Ethics request: %.80s…", body.text)
    return _predict("ethics", body.text)


@app.post("/analyze", response_model=AnalysisResult)
def analyze(body: TextInput):
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="Text must not be empty.")
    log.info("Full analysis request: %.80s…", body.text)
    fallacy_result = _predict("fallacy", body.text)
    ethics_result  = _predict("ethics",  body.text)
    summary = _build_summary(fallacy_result, ethics_result)
    return AnalysisResult(fallacy=fallacy_result, ethics=ethics_result, summary=summary)
