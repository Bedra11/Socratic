from dotenv import load_dotenv
load_dotenv()

import json
import os
import pickle
import warnings
import httpx

import mlflow
import mlflow.sklearn

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field, field_validator

warnings.filterwarnings("ignore")

# =========================
# APP INIT
# =========================

app = FastAPI(title="Socratic API", version="2.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# =========================
# MODEL LOADING (MLflow)
# =========================

MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME_ETHICS = os.getenv("MODEL_NAME_ETHICS", "socratic-ethics-classifier")
MODEL_NAME_FALLACY = os.getenv("MODEL_NAME_FALLACY", "socratic-fallacy-classifier")

mlflow.set_tracking_uri(MLFLOW_URI)


def load_model_from_registry(name: str):
    try:
        model = mlflow.sklearn.load_model(f"models:/{name}/Staging")
        print(f"Loaded from MLflow Registry: {name}")
        return model
    except Exception as e:
        print(f"MLflow failed ({e}), loading local pickle...")
        path = f"models/{name.split('-')[1]}_model.pkl"
        if os.path.exists(path):
            return pickle.load(open(path, "rb"))
        raise RuntimeError(f"Cannot load model: {name}")


ethics_model = load_model_from_registry(MODEL_NAME_ETHICS)
fallacy_model = load_model_from_registry(MODEL_NAME_FALLACY)

print("Socratic API ready")

# =========================
# HELPERS
# =========================


def ensure_model_loaded(model, name: str):
    if model is None:
        raise HTTPException(status_code=503, detail=f"{name} not loaded")


# =========================
# SCHEMAS
# =========================

class AnalyzeRequest(BaseModel):
    scenario: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    reason: str = Field(default="")
    language: str = Field(default="english")

    @field_validator("scenario", "decision", "reason", "language")
    @classmethod
    def clean_text_fields(cls, value: str):
        return value.strip() if isinstance(value, str) else value


class AnalyzeResponse(BaseModel):
    scenario: str
    decision: str
    reason: str
    language: str
    ethics_prediction: str
    fallacy_prediction: str
    ethics_explanation: str
    fallacy_explanation: str
    personal_insight: str


# =========================
# GROQ FUNCTION
# =========================

async def get_groq_explanation(
    scenario: str,
    decision: str,
    reason: str,
    ethics_prediction: str,
    fallacy_prediction: str,
    language: str = "english"
) -> dict:

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

    empty_result = {
        "ethics_explanation": "",
        "fallacy_explanation": "",
        "personal_insight": ""
    }

    if not groq_api_key:
        return empty_result

    prompt = f"""
You are an expert reasoning assistant.

The user wants explanations in this language: {language}.

Explain:
1. the ethics prediction
2. the fallacy prediction
3. a short personal insight

Context:
Scenario: {scenario}
Decision: {decision}
Reason: {reason}
Ethics: {ethics_prediction}
Fallacy: {fallacy_prediction}

Return ONLY valid JSON with:
ethics_explanation, fallacy_explanation, personal_insight
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "max_completion_tokens": 400,
        "messages": [
            {"role": "system", "content": "Return JSON only"},
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )

        if response.status_code != 200:
            return empty_result

        content = response.json()["choices"][0]["message"]["content"].strip()
        parsed = json.loads(content)

        return {
            "ethics_explanation": parsed.get("ethics_explanation", ""),
            "fallacy_explanation": parsed.get("fallacy_explanation", ""),
            "personal_insight": parsed.get("personal_insight", "")
        }

    except Exception:
        return empty_result


# =========================
# ROUTES (UI)
# =========================

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})


@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    return templates.TemplateResponse("result.html", {"request": request})


# =========================
# MAIN ANALYZE ENDPOINT
# =========================

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):

    ensure_model_loaded(ethics_model, "Ethics model")
    ensure_model_loaded(fallacy_model, "Fallacy model")

    combined_text = f"{req.scenario} {req.decision} {req.reason}".strip()

    try:
        ethics_prediction = str(ethics_model.predict([combined_text])[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        fallacy_prediction = str(fallacy_model.predict([combined_text])[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    groq_result = await get_groq_explanation(
        scenario=req.scenario,
        decision=req.decision,
        reason=req.reason,
        ethics_prediction=ethics_prediction,
        fallacy_prediction=fallacy_prediction,
        language=req.language
    )

    return {
        "scenario": req.scenario,
        "decision": req.decision,
        "reason": req.reason,
        "language": req.language,
        "ethics_prediction": ethics_prediction,
        "fallacy_prediction": fallacy_prediction,
        "ethics_explanation": groq_result["ethics_explanation"],
        "fallacy_explanation": groq_result["fallacy_explanation"],
        "personal_insight": groq_result["personal_insight"]
    }