# src/train.py
from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import pickle
import os
import yaml
import mlflow
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    f1_score,
    accuracy_score
)
import warnings
warnings.filterwarnings("ignore")

 
# CONFIG
 
params     = yaml.safe_load(open("params.yaml"))
eth_params = params["train_ethics"]
fal_params = params["train_fallacy"]
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)
print(f"  MLflow tracking: {MLFLOW_URI}")

os.makedirs("models", exist_ok=True)

 
# HELPER
 
def train_model(experiment_name, train_path, model_path, p, class_weight=None):
    print(f"\n{'═'*50}")
    print(f"  Training: {experiment_name}")
    print(f"{'═'*50}")

    df = pd.read_csv(train_path)
    df = df.dropna(subset=["text", "label"])
    X  = df["text"].astype(str)
    y  = df["label"].astype(str)

    print(f"  Training samples : {len(df)}")
    print(f"  Classes          : {sorted(y.unique())}")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features  = p["max_features"],
            ngram_range   = (p["ngram_min"], p["ngram_max"]),
            sublinear_tf  = True,
            strip_accents = "unicode",
            analyzer      = "word",
            min_df        = 2
        )),
        ("clf", LogisticRegression(
            C            = p["C"],
            solver       = p["solver"],
            max_iter     = p["max_iter"],
            random_state = p["random_state"],
            class_weight = class_weight,
            multi_class  = "multinomial"
        ))
    ])

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="training"):
        # ─── Log params only ───
        mlflow.log_param("max_features",  p["max_features"])
        mlflow.log_param("ngram_range",   f"{p['ngram_min']},{p['ngram_max']}")
        mlflow.log_param("C",             p["C"])
        mlflow.log_param("solver",        p["solver"])
        mlflow.log_param("max_iter",      p["max_iter"])
        mlflow.log_param("class_weight",  str(class_weight))
        mlflow.log_param("train_samples", len(df))

        # ─── Train ───
        pipeline.fit(X, y)
        print("  Training complete")

        # ─── Log train metrics only ───
        y_pred = pipeline.predict(X)
        f1     = f1_score(y, y_pred, average="weighted")
        acc    = accuracy_score(y, y_pred)

        mlflow.log_metric("train_f1_weighted", round(f1, 4))
        mlflow.log_metric("train_accuracy",    round(acc, 4))

        print(f"\n  Train F1 (weighted): {f1:.4f}")
        print(f"  Train Accuracy     : {acc:.4f}")
        print(f"\n{classification_report(y, y_pred)}")

        # ─── Save locally ONLY — no MLflow model logging here ───
        pickle.dump(pipeline, open(model_path, "wb"))
        print(f"  Model saved locally → {model_path}")
        print(f"   Model NOT sent to MLflow Registry (register.py will handle this)")

    return pipeline


# TRAIN BOTH MODELS

ethics_model = train_model(
    experiment_name = "ethics-reasoning-classifier",
    train_path      = eth_params["train_data"],
    model_path      = eth_params["model_path"],
    p               = eth_params,
    class_weight    = None
)

fallacy_model = train_model(
    experiment_name = "fallacy-detector",
    train_path      = fal_params["train_data"],
    model_path      = fal_params["model_path"],
    p               = fal_params,
    class_weight    = fal_params["class_weight"]
)

print("\n\n  Both models trained and saved locally!")
print(f"   Ethics  model → {eth_params['model_path']}")
print(f"   Fallacy model → {fal_params['model_path']}")
print(f"    Run evaluate.py next")