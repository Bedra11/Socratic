from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import pickle
import os
import json
import yaml
import mlflow
import warnings
warnings.filterwarnings("ignore")

from sklearn.metrics import (
    f1_score,
    accuracy_score,
    precision_score,
    recall_score,
    classification_report
)

# CONFIG

params     = yaml.safe_load(open("params.yaml"))
eth_p      = params["train_ethics"]
fal_p      = params["train_fallacy"]
eval_p     = params["evaluate"]
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)
os.makedirs("metrics", exist_ok=True)

# HELPER — Evaluate one model

def evaluate_model(experiment_name, test_path, model_path, encoder_path):
    print(f"\n{'═'*50}")
    print(f" Evaluating: {experiment_name}")
    print(f"{'═'*50}")

    # Load test data
    df      = pd.read_csv(test_path)
    df      = df.dropna(subset=["text", "label"])
    X_test  = df["text"].astype(str)
    y_true  = df["label"].astype(str)

    print(f" Test samples : {len(df)}")

    # Load model
    model   = pickle.load(open(model_path, "rb"))
    y_pred  = model.predict(X_test)

    # Compute metrics
    f1      = f1_score(y_true, y_pred, average="weighted")
    acc     = accuracy_score(y_true, y_pred)
    prec    = precision_score(y_true, y_pred, average="weighted",
                              zero_division=0)
    rec     = recall_score(y_true, y_pred, average="weighted",
                           zero_division=0)

    print(f"\ F1  (weighted) : {f1:.4f}")
    print(f" Accuracy       : {acc:.4f}")
    print(f" Precision      : {prec:.4f}")
    print(f" Recall         : {rec:.4f}")
    print(f"\n{classification_report(y_true, y_pred, zero_division=0)}")

    return {
        "f1_weighted" : round(f1,   4),
        "accuracy"    : round(acc,  4),
        "precision"   : round(prec, 4),
        "recall"      : round(rec,  4)
    }

# EVALUATE BOTH MODELS
ethics_metrics  = evaluate_model(
    experiment_name = "ethics-reasoning-classifier",
    test_path       = "data/processed/ethics_test.csv",
    model_path      = eth_p["model_path"],
    encoder_path    = "data/processed/ethics_label_encoder.pkl"
)

fallacy_metrics = evaluate_model(
    experiment_name = "fallacy-detector",
    test_path       = "data/processed/fallacy_test.csv",
    model_path      = fal_p["model_path"],
    encoder_path    = "data/processed/fallacy_label_encoder.pkl"
)
