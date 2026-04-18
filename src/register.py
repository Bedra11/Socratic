# src/register.py
from dotenv import load_dotenv
load_dotenv()

import os
import json
import yaml
import mlflow
import mlflow.sklearn
import pickle
import warnings
warnings.filterwarnings("ignore")


# CONFIG

params     = yaml.safe_load(open("params.yaml"))
reg_p      = params["register"]
eval_p     = params["evaluate"]
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)
print(f" MLflow tracking: {MLFLOW_URI}")


# STEP 1 — LOAD METRICS FROM JSON
# produced by evaluate.py

metrics_path = eval_p["metrics_output"]

if not os.path.exists(metrics_path):
    raise FileNotFoundError(
        f"  Metrics file not found: {metrics_path}\n"
        f"   Run evaluate.py first."
    )

with open(metrics_path, "r") as f:
    all_metrics = json.load(f)

threshold = eval_p["threshold"]

print(f"\n Loaded metrics from {metrics_path}")
print(f" Registration threshold : F1 >= {threshold}")
print(f"\n{'═'*50}")


# STEP 2 — CHECK THRESHOLD FOR EACH MODEL

ethics_f1  = all_metrics["ethics"]["f1_weighted"]
fallacy_f1 = all_metrics["fallacy"]["f1_weighted"]

print(f"   ETHICS  → F1 = {ethics_f1:.4f}  "
      f"{' PASS' if ethics_f1  >= threshold else '❌ FAIL'}")
print(f"   FALLACY → F1 = {fallacy_f1:.4f}  "
      f"{' PASS' if fallacy_f1 >= threshold else '❌ FAIL'}")
print(f"{'═'*50}")
