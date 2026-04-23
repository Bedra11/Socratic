from dotenv import load_dotenv
load_dotenv()

import json
import os
import pickle
import warnings
from collections import Counter
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

app = FastAPI(title="Socratic API", version="2.1.0")

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
            with open(path, "rb") as file:
                return pickle.load(file)
        raise RuntimeError(f"Cannot load model: {name}")


ethics_model = load_model_from_registry(MODEL_NAME_ETHICS)
fallacy_model = load_model_from_registry(MODEL_NAME_FALLACY)

print("Socratic API ready")

# =========================
# STATIC MAPS FOR UI
# =========================

ETHICS_INFO_MAP = {
    "utilitarianism": {
        "ethics_name": "The Utilitarian",
        "ethics_icon": "⚖️",
        "ethics_text": "You tend to judge actions by their outcomes and by the overall good they produce."
    },
    "deontology": {
        "ethics_name": "The Duty-Bound",
        "ethics_icon": "📜",
        "ethics_text": "You tend to focus on rules, duties, and moral principles regardless of consequences."
    },
    "virtue ethics": {
        "ethics_name": "The Virtuous",
        "ethics_icon": "🏛️",
        "ethics_text": "You tend to evaluate choices by the character traits and virtues they reflect."
    },
    "care ethics": {
        "ethics_name": "The Caretaker",
        "ethics_icon": "🤝",
        "ethics_text": "You tend to reason through empathy, relationships, and responsibility toward others."
    },
    "egoism": {
        "ethics_name": "The Realist",
        "ethics_icon": "🎯",
        "ethics_text": "You tend to emphasize self-interest and personal benefit in moral decision making."
    }
}

BOOK_MAP = {
    "faulty generalization": {
        "book_title": "Thinking, Fast and Slow",
        "book_author": "Daniel Kahneman",
        "book_why": "Useful for understanding how quick judgments can lead to broad conclusions."
    },
    "false causality": {
        "book_title": "The Book of Why",
        "book_author": "Judea Pearl",
        "book_why": "Useful for learning the difference between correlation and causation."
    },
    "circular reasoning": {
        "book_title": "Gödel, Escher, Bach",
        "book_author": "Douglas Hofstadter",
        "book_why": "A strong choice for exploring self-reference and circular structures in reasoning."
    },
    "ad hominem": {
        "book_title": "How to Win an Argument",
        "book_author": "Arthur Schopenhauer",
        "book_why": "Helpful for understanding when arguments attack people instead of ideas."
    },
    "ad populum": {
        "book_title": "Extraordinary Popular Delusions",
        "book_author": "Charles Mackay",
        "book_why": "Useful for seeing why popularity is not the same thing as truth."
    },
    "appeal to emotion": {
        "book_title": "The Righteous Mind",
        "book_author": "Jonathan Haidt",
        "book_why": "Helpful for understanding how emotions shape moral reasoning."
    },
    "false dilemma": {
        "book_title": "Justice",
        "book_author": "Michael Sandel",
        "book_why": "Useful for exploring moral situations that are more complex than two simple options."
    },
    "fallacy of relevance": {
        "book_title": "Critical Thinking",
        "book_author": "Richard Paul",
        "book_why": "Good for learning how to stay focused on relevant arguments."
    },
    "fallacy of logic": {
        "book_title": "An Introduction to Logic",
        "book_author": "Irving Copi",
        "book_why": "Helpful for strengthening formal reasoning and logical structure."
    },
    "intentional": {
        "book_title": "Influence",
        "book_author": "Robert Cialdini",
        "book_why": "Useful for understanding persuasion and manipulation strategies."
    },
    "fallacy of extension": {
        "book_title": "The Straw Man Fallacy",
        "book_author": "Scott Aikin",
        "book_why": "Helpful for recognizing distorted versions of opposing arguments."
    },
    "fallacy of credibility": {
        "book_title": "The Demon-Haunted World",
        "book_author": "Carl Sagan",
        "book_why": "Useful for learning how to evaluate claims with evidence."
    },
    "equivocation": {
        "book_title": "Language in Thought and Action",
        "book_author": "S.I. Hayakawa",
        "book_why": "Helpful for understanding how ambiguous language can distort reasoning."
    }
}

DEFAULT_ETHICS_INFO = {
    "ethics_name": "Undefined",
    "ethics_icon": "🧠",
    "ethics_text": ""
}

DEFAULT_BOOK_INFO = {
    "book_title": "Meditations",
    "book_author": "Marcus Aurelius",
    "book_why": "A classic for any thinker."
}

# =========================
# HELPERS
# =========================

def ensure_model_loaded(model, name: str):
    if model is None:
        raise HTTPException(status_code=503, detail=f"{name} not loaded")


def build_ui_payload(ethics_prediction: str, fallacy_prediction: str) -> dict:
    ethics_info = ETHICS_INFO_MAP.get(ethics_prediction, DEFAULT_ETHICS_INFO)
    book_info = BOOK_MAP.get(fallacy_prediction, DEFAULT_BOOK_INFO)

    return {
        "ethics_label": ethics_prediction,
        "ethics_name": ethics_info["ethics_name"],
        "ethics_icon": ethics_info["ethics_icon"],
        "ethics_text": ethics_info["ethics_text"],
        "fallacy_label": fallacy_prediction,
        "book_title": book_info["book_title"],
        "book_author": book_info["book_author"],
        "book_why": book_info["book_why"]
    }


def predict_single_chapter(scenario: str, decision: str, reason: str) -> tuple[str, str]:
    ensure_model_loaded(ethics_model, "Ethics model")
    ensure_model_loaded(fallacy_model, "Fallacy model")

    combined_text = f"{scenario} {decision} {reason}".strip()

    print("\n--- INPUT MODELE ---")
    print("Type de combined_text:", type(combined_text))
    print("combined_text:", combined_text)
    print("--------------------\n")

    try:
        ethics_prediction = str(ethics_model.predict([combined_text])[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ethics prediction failed: {e}")

    try:
        fallacy_prediction = str(fallacy_model.predict([combined_text])[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallacy prediction failed: {e}")

    return ethics_prediction, fallacy_prediction


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
    ethics_label: str
    ethics_name: str
    ethics_icon: str
    ethics_text: str
    fallacy_label: str
    book_title: str
    book_author: str
    book_why: str
    ethics_explanation: str
    fallacy_explanation: str
    personal_insight: str


class ChapterInput(BaseModel):
    scenario: str = Field(..., min_length=1)
    decision: str = Field(..., min_length=1)
    reason: str = Field(default="")

    @field_validator("scenario", "decision", "reason")
    @classmethod
    def clean_text_fields(cls, value: str):
        return value.strip() if isinstance(value, str) else value


class AnalyzeFinalRequest(BaseModel):
    chapters: list[ChapterInput] = Field(..., min_length=1)
    language: str = Field(default="english")

    @field_validator("language")
    @classmethod
    def clean_language(cls, value: str):
        return value.strip() if isinstance(value, str) else value


class AnalyzeFinalResponse(BaseModel):
    language: str
    ethics_prediction: str
    fallacy_prediction: str
    ethics_label: str
    ethics_name: str
    ethics_icon: str
    ethics_text: str
    fallacy_label: str
    book_title: str
    book_author: str
    book_why: str
    ethics_explanation: str
    fallacy_explanation: str
    personal_insight: str
    chapters_analyzed: int


# =========================
# GROQ FUNCTIONS
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


async def get_groq_final_explanation(
    chapters: list[ChapterInput],
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

    formatted_chapters = "\n".join(
        [
            f"Chapter {i+1}: Scenario={c.scenario} | Decision={c.decision} | Reason={c.reason}"
            for i, c in enumerate(chapters)
        ]
    )

    print("\n--- GROQ INPUT FINAL ---")
    print(formatted_chapters)
    print("------------------------\n")

    prompt = f"""
You are an expert reasoning assistant.

The user wants explanations in this language: {language}.

The final dominant predictions across all chapters are:
Ethics: {ethics_prediction}
Fallacy: {fallacy_prediction}

Here are all chapter answers:
{formatted_chapters}

Explain:
1. the dominant ethics profile across all chapters
2. the dominant fallacy pattern across all chapters
3. a short personal insight about the user's overall reasoning style

Return ONLY valid JSON with:
ethics_explanation, fallacy_explanation, personal_insight
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "temperature": 0.3,
        "max_completion_tokens": 500,
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
# ROUTES
# =========================

@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse(request, "game.html")


@app.get("/result", response_class=HTMLResponse)
async def result(request: Request):
    return templates.TemplateResponse(request, "result.html")


# =========================
# ANALYZE SINGLE CHAPTER
# =========================

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    print("\n========== DEBUG /analyze ==========")
    print("Type de req:", type(req))
    print("Scenario:", req.scenario)
    print("Decision:", req.decision)
    print("Reason:", req.reason)
    print("Language:", req.language)
    print("====================================\n")

    ethics_prediction, fallacy_prediction = predict_single_chapter(
        scenario=req.scenario,
        decision=req.decision,
        reason=req.reason
    )

    groq_result = await get_groq_explanation(
        scenario=req.scenario,
        decision=req.decision,
        reason=req.reason,
        ethics_prediction=ethics_prediction,
        fallacy_prediction=fallacy_prediction,
        language=req.language
    )

    ui_payload = build_ui_payload(
        ethics_prediction=ethics_prediction,
        fallacy_prediction=fallacy_prediction
    )

    return {
        "scenario": req.scenario,
        "decision": req.decision,
        "reason": req.reason,
        "language": req.language,
        "ethics_prediction": ethics_prediction,
        "fallacy_prediction": fallacy_prediction,
        "ethics_label": ui_payload["ethics_label"],
        "ethics_name": ui_payload["ethics_name"],
        "ethics_icon": ui_payload["ethics_icon"],
        "ethics_text": ui_payload["ethics_text"],
        "fallacy_label": ui_payload["fallacy_label"],
        "book_title": ui_payload["book_title"],
        "book_author": ui_payload["book_author"],
        "book_why": ui_payload["book_why"],
        "ethics_explanation": groq_result["ethics_explanation"],
        "fallacy_explanation": groq_result["fallacy_explanation"],
        "personal_insight": groq_result["personal_insight"]
    }


# =========================
# ANALYZE FINAL (ALL CHAPTERS)
# =========================

@app.post("/analyze-final", response_model=AnalyzeFinalResponse)
async def analyze_final(req: AnalyzeFinalRequest):
    print("\n========== DEBUG /analyze-final ==========")
    print("Type de req.chapters:", type(req.chapters))
    print("Nombre de chapitres:", len(req.chapters))
    print("Language:", req.language)

    print("\n--- CONTENU DES CHAPITRES ---")
    for i, ch in enumerate(req.chapters):
        print(f"\nChapitre {i+1}:")
        print("Scenario:", ch.scenario)
        print("Decision:", ch.decision)
        print("Reason:", ch.reason)

    print("\n==========================================\n")

    if not req.chapters:
        raise HTTPException(status_code=400, detail="No chapters provided")

    ethics_predictions = []
    fallacy_predictions = []

    for chapter in req.chapters:
        ethics_prediction, fallacy_prediction = predict_single_chapter(
            scenario=chapter.scenario,
            decision=chapter.decision,
            reason=chapter.reason
        )
        ethics_predictions.append(ethics_prediction)
        fallacy_predictions.append(fallacy_prediction)

    print("\n--- PREDICTIONS PAR CHAPITRE ---")
    print("ethics_predictions:", ethics_predictions)
    print("fallacy_predictions:", fallacy_predictions)
    print("--------------------------------\n")

    dominant_ethics = Counter(ethics_predictions).most_common(1)[0][0]
    dominant_fallacy = Counter(fallacy_predictions).most_common(1)[0][0]

    print("\n--- RESULTAT FINAL DOMINANT ---")
    print("dominant_ethics:", dominant_ethics)
    print("dominant_fallacy:", dominant_fallacy)
    print("-------------------------------\n")

    groq_result = await get_groq_final_explanation(
        chapters=req.chapters,
        ethics_prediction=dominant_ethics,
        fallacy_prediction=dominant_fallacy,
        language=req.language
    )

    ui_payload = build_ui_payload(
        ethics_prediction=dominant_ethics,
        fallacy_prediction=dominant_fallacy
    )

    return {
        "language": req.language,
        "ethics_prediction": dominant_ethics,
        "fallacy_prediction": dominant_fallacy,
        "ethics_label": ui_payload["ethics_label"],
        "ethics_name": ui_payload["ethics_name"],
        "ethics_icon": ui_payload["ethics_icon"],
        "ethics_text": ui_payload["ethics_text"],
        "fallacy_label": ui_payload["fallacy_label"],
        "book_title": ui_payload["book_title"],
        "book_author": ui_payload["book_author"],
        "book_why": ui_payload["book_why"],
        "ethics_explanation": groq_result["ethics_explanation"],
        "fallacy_explanation": groq_result["fallacy_explanation"],
        "personal_insight": groq_result["personal_insight"],
        "chapters_analyzed": len(req.chapters)
    }