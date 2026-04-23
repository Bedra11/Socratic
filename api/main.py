# api/main.py
from dotenv import load_dotenv
load_dotenv()

import json
import os
import httpx
from dotenv import load_dotenv
import os
import pickle
import mlflow
import mlflow.sklearn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import warnings
warnings.filterwarnings("ignore")


# APP INIT

app = FastAPI(title="Socratic API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# MODEL LOADING — from MLflow Registry

MLFLOW_URI          = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME_ETHICS   = os.getenv("MODEL_NAME_ETHICS",  "socratic-ethics-classifier")
MODEL_NAME_FALLACY  = os.getenv("MODEL_NAME_FALLACY", "socratic-fallacy-classifier")

mlflow.set_tracking_uri(MLFLOW_URI)

def load_model_from_registry(name: str):
    try:
        model = mlflow.sklearn.load_model(f"models:/{name}/Staging")
        print(f" Loaded from MLflow Registry: {name}")
        return model
    except Exception as e:
        print(f"  MLflow Registry failed ({e}), loading from local pickle...")
        path = f"models/{name.split('-')[1]}_model.pkl"
        if os.path.exists(path):
            return pickle.load(open(path, "rb"))
        raise RuntimeError(f"Cannot load model: {name}")

ethics_model  = load_model_from_registry(MODEL_NAME_ETHICS)
fallacy_model = load_model_from_registry(MODEL_NAME_FALLACY)

print(" Socratic API ready")


# BOOK RECOMMENDATIONS

BOOK_MAP = {
    "faulty generalization":    {"title": "Thinking, Fast and Slow",         "author": "Daniel Kahneman",   "why": "You jump to broad conclusions — this book reveals why our minds overgeneralize."},
    "false causality":          {"title": "The Book of Why",                  "author": "Judea Pearl",       "why": "You confuse correlation with cause — Pearl teaches rigorous causal thinking."},
    "circular reasoning":       {"title": "Gödel, Escher, Bach",              "author": "Douglas Hofstadter","why": "You argue in loops — this book explores self-reference and paradox beautifully."},
    "ad hominem":               {"title": "How to Win an Argument",           "author": "Arthur Schopenhauer","why": "You attack people, not ideas — Schopenhauer exposes every rhetorical trick."},
    "ad populum":               {"title": "Extraordinary Popular Delusions",  "author": "Charles Mackay",    "why": "You follow the crowd — Mackay documents how majorities are systematically wrong."},
    "appeal to emotion":        {"title": "The Righteous Mind",               "author": "Jonathan Haidt",    "why": "You reason with feeling — Haidt explains why emotions drive moral judgment."},
    "false dilemma":            {"title": "Justice",                          "author": "Michael Sandel",    "why": "You see only two options — Sandel reveals the rich complexity of moral choices."},
    "fallacy of relevance":     {"title": "Critical Thinking",                "author": "Richard Paul",      "why": "You use red herrings — this book trains attention to what actually matters."},
    "fallacy of logic":         {"title": "An Introduction to Logic",         "author": "Irving Copi",       "why": "Your logical structure breaks down — Copi rebuilds it from the ground up."},
    "intentional":              {"title": "Influence",                        "author": "Robert Cialdini",   "why": "You manipulate rather than argue — Cialdini exposes every persuasion trick."},
    "fallacy of extension":     {"title": "The Straw Man Fallacy",            "author": "Scott Aikin",       "why": "You attack exaggerated versions of ideas — this book dissects exactly that."},
    "fallacy of credibility":   {"title": "The Demon-Haunted World",          "author": "Carl Sagan",        "why": "You defer to authority — Sagan teaches how to evaluate evidence yourself."},
    "equivocation":             {"title": "Language in Thought and Action",   "author": "S.I. Hayakawa",     "why": "You exploit ambiguous words — Hayakawa unpacks how language distorts reason."},
}

ETHICS_INSIGHTS = {
    "utilitarianism":  {"name": "The Utilitarian",  "icon": "⚖️",  "text": "You measure morality by outcomes. You seek the greatest good for the greatest number — a noble but sometimes cold calculus."},
    "deontology":      {"name": "The Duty-Bound",   "icon": "📜",  "text": "You follow rules regardless of consequence. Kant would approve — your moral compass points to principle, not result."},
    "virtue ethics":   {"name": "The Virtuous",     "icon": "🏛️",  "text": "You ask what a good person would do. Aristotle's student — character and habit define your moral universe."},
    "care ethics":     {"name": "The Caretaker",    "icon": "🤝",  "text": "You reason through relationships. Empathy and connection guide your decisions — the ethics of interdependence."},
    "egoism":          {"name": "The Realist",      "icon": "🎯",  "text": "You believe self-interest is the honest foundation of action. Nietzsche might nod — at least you are honest about it."},
}


# SCHEMAS

class AnalyzeRequest(BaseModel):
    scenario: str
    decision: str
    reason:   str


# ROUTES

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    return templates.TemplateResponse("result.html", {"request": request})

@app.post("/analyze")
async def analyze(data: AnalyzeRequest):
    # build combined text for ethics model
    ethics_text  = f"{data.scenario} {data.decision} {data.reason}"
    # use reason text for fallacy detection
    fallacy_text = data.reason

    ethics_pred  = ethics_model.predict([ethics_text])[0]
    fallacy_pred = fallacy_model.predict([fallacy_text])[0]

    ethics_info  = ETHICS_INSIGHTS.get(ethics_pred,  {"name": ethics_pred,  "icon": "🧠", "text": ""})
    book         = BOOK_MAP.get(fallacy_pred, {"title": "Meditations", "author": "Marcus Aurelius", "why": "A classic for any thinker."})

    return JSONResponse({
        "ethics_label":   ethics_pred,
        "ethics_name":    ethics_info["name"],
        "ethics_icon":    ethics_info["icon"],
        "ethics_text":    ethics_info["text"],
        "fallacy_label":  fallacy_pred,
        "book_title":     book["title"],
        "book_author":    book["author"],
        "book_why":       book["why"],
    })

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

You must explain:
1. the ethics prediction
2. the fallacy prediction
3. one short personal insight for the user

Context:
- Scenario: {scenario}
- Decision: {decision}
- Reason: {reason}
- Ethics prediction: {ethics_prediction}
- Fallacy prediction: {fallacy_prediction}

Rules:
- Write clearly in the requested language.
- Keep each field concise but useful.
- Do not mention that you are an AI.
- Return ONLY valid JSON.
- The JSON must have exactly these keys:
  ethics_explanation
  fallacy_explanation
  personal_insight
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "max_completion_tokens": 400,
        "messages": [
            {
                "role": "system",
                "content": "You are a multilingual reasoning explainer. Return JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
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

        response_data = response.json()

        content = (
            response_data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:
            return empty_result

        parsed = json.loads(content)

        return {
            "ethics_explanation": str(parsed.get("ethics_explanation", "")).strip(),
            "fallacy_explanation": str(parsed.get("fallacy_explanation", "")).strip(),
            "personal_insight": str(parsed.get("personal_insight", "")).strip()
        }

    except Exception:
        return empty_result
    
    
    
    from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    scenario: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    reason: str = Field(default="")
    language: str = Field(default="english")

    @field_validator("scenario", "decision", "reason", "language")
    @classmethod
    def clean_text_fields(cls, value: str) -> str:
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
    
    
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    ensure_model_loaded(ethics_model, "Ethics model")
    ensure_model_loaded(fallacy_model, "Fallacy model")

    combined_ethics_text = f"{req.scenario} {req.decision} {req.reason}".strip()
    combined_fallacy_text = f"{req.scenario} {req.decision} {req.reason}".strip()

    try:
        ethics_prediction = str(ethics_model.predict([combined_ethics_text])[0])
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Ethics prediction failed: {str(exc)}"
        ) from exc

    try:
        fallacy_prediction = str(fallacy_model.predict([combined_fallacy_text])[0])
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Fallacy prediction failed: {str(exc)}"
        ) from exc

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
        "ethics_explanation": groq_result.get("ethics_explanation", ""),
        "fallacy_explanation": groq_result.get("fallacy_explanation", ""),
        "personal_insight": groq_result.get("personal_insight", "")
    }