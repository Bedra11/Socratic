# src/evaluate.py
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
eval_p     = params["evaluate"]
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)
os.makedirs("metrics", exist_ok=True)

 
# HELPER
 
def evaluate_model(experiment_name, test_path, model_path):
    print(f"\n{'═'*50}")
    print(f"  Evaluating: {experiment_name}")
    print(f"{'═'*50}")

    df     = pd.read_csv(test_path)
    df     = df.dropna(subset=["text", "label"])
    X_test = df["text"].astype(str)
    y_true = df["label"].astype(str)

    print(f"  Test samples: {len(df)}")

    model  = pickle.load(open(model_path, "rb"))
    y_pred = model.predict(X_test)

    f1   = f1_score(y_true, y_pred, average="weighted")
    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec  = recall_score(y_true, y_pred, average="weighted", zero_division=0)

    print(f"\n  F1  (weighted) : {f1:.4f}")
    print(f"  Accuracy       : {acc:.4f}")
    print(f"  Precision      : {prec:.4f}")
    print(f"  Recall         : {rec:.4f}")
    print(f"\n{classification_report(y_true, y_pred, zero_division=0)}")

    metrics = {
        "f1_weighted" : round(f1,   4),
        "accuracy"    : round(acc,  4),
        "precision"   : round(prec, 4),
        "recall"      : round(rec,  4)
    }

    # ─── Log test metrics to MLflow — NO model logging ───
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name="evaluation"):
        for name, value in metrics.items():
            mlflow.log_metric(f"test_{name}", value)
        print(f"  Test metrics logged to MLflow")
        print(f"   Model NOT sent to MLflow Registry (register.py handles this)")

    return metrics

 
# EVALUATE BOTH MODELS
 
ethics_metrics = evaluate_model(
    experiment_name = "ethics-reasoning-classifier",
    test_path       = eval_p["ethics_test"],
    model_path      = eval_p["ethics_model"]
)

fallacy_metrics = evaluate_model(
    experiment_name = "fallacy-detector",
    test_path       = eval_p["fallacy_test"],
    model_path      = eval_p["fallacy_model"]
)

 
# SAVE METRICS JSON — DVC reads this
 
all_metrics = {
    "ethics":  ethics_metrics,
    "fallacy": fallacy_metrics
}

with open(eval_p["metrics_output"], "w") as f:
    json.dump(all_metrics, f, indent=2)

print(f"\n  Metrics saved → {eval_p['metrics_output']}")

 
# THRESHOLD CHECK
 
threshold = eval_p["threshold"]

print(f"\n{'═'*50}")
print(f"  THRESHOLD CHECK (min F1 = {threshold})")
print(f"{'═'*50}")

for name, metrics in all_metrics.items():
    f1     = metrics["f1_weighted"]
    status = "  PASS — will be registered" if f1 >= threshold \
             else "  FAIL — will NOT be registered"
    print(f"   {name.upper():10} → F1={f1:.4f}  {status}")

print(f"\n  Evaluation complete!")
print(f"      Run register.py next")