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
      f"{' PASS' if ethics_f1  >= threshold else ' FAIL'}")
print(f"   FALLACY → F1 = {fallacy_f1:.4f}  "
      f"{' PASS' if fallacy_f1 >= threshold else ' FAIL'}")
print(f"{'═'*50}")



# HELPER — Register one model

def register_model(
    model_name,
    model_path,
    encoder_path,
    metrics,
    stage
):
    print(f"\n Registering: {model_name}")

    # Load model from pickle
    if not os.path.exists(model_path):
        print(f"    Model file not found: {model_path}")
        return False

    model = pickle.load(open(model_path, "rb"))

    # Start MLflow run
    mlflow.set_experiment(model_name)

    with mlflow.start_run(run_name="registration"):

        # Log all metrics
        for metric_name, value in metrics.items():
            mlflow.log_metric(f"test_{metric_name}", value)

        # Log model params
        mlflow.log_param("model_path",   model_path)
        mlflow.log_param("stage",        stage)

        # Register model in MLflow Registry
        result = mlflow.sklearn.log_model(
            sk_model              = model,
            artifact_path         = "model",
            registered_model_name = model_name   
        )

        print(f"    Registered as    : {model_name}")
        print(f"    Stage target     : {stage}")
        print(f"    F1 (weighted)    : {metrics['f1_weighted']}")
        print(f"    Accuracy         : {metrics['accuracy']}")
        print(f"    Run ID           : {result.run_id}")


    # Transition model to target stage
    # Staging or Production

    client = mlflow.tracking.MlflowClient()

    # Get latest version
    latest = client.get_latest_versions(model_name)
    if latest:
        version = latest[-1].version
        client.transition_model_version_stage(
            name    = model_name,
            version = version,
            stage   = stage
        )
        print(f"    Transitioned     : version {version} → {stage}")

    return True



# REGISTER ETHICS MODEL

if ethics_f1 >= threshold:
    register_model(
        model_name   = reg_p["ethics_model_name"],
        model_path   = eval_p["ethics_model"],
        encoder_path = eval_p["ethics_encoder"],
        metrics      = all_metrics["ethics"],
        stage        = reg_p["stage"]
    )
else:
    print(f"\n  ETHICS model NOT registered")
    print(f"   F1={ethics_f1:.4f} is below threshold={threshold}")
    print(f"   Fix the model and re-run the pipeline.")


# REGISTER FALLACY MODEL

if fallacy_f1 >= threshold:
    register_model(
        model_name   = reg_p["fallacy_model_name"],
        model_path   = eval_p["fallacy_model"],
        encoder_path = eval_p["fallacy_encoder"],
        metrics      = all_metrics["fallacy"],
        stage        = reg_p["stage"]
    )
else:
    print(f"\n  FALLACY model NOT registered")
    print(f"   F1={fallacy_f1:.4f} is below threshold={threshold}")
    print(f"   Fix the model and re-run the pipeline.")


# SUMMARY

print(f"\n{'═'*50}")
print(f" Registration complete!")
print(f"   Check MLflow Registry → {MLFLOW_URI}/#/models")
print(f"{'═'*50}")