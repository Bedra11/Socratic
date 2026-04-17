from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import pickle
import os
import yaml
import mlflow
import mlflow.sklearn
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

params      = yaml.safe_load(open("params.yaml"))
eth_params  = params["train_ethics"]
fal_params  = params["train_fallacy"]

MLFLOW_URI  = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

mlflow.set_tracking_uri(MLFLOW_URI)
print(f" MLflow tracking: {MLFLOW_URI}")

os.makedirs("models", exist_ok=True)


# HELPER — Generic train function

def train_model(
    experiment_name,
    train_path,
    model_path,
    p,
    class_weight=None
):
    print(f"\n{'═'*50}")
    print(f" Training: {experiment_name}")
    print(f"{'═'*50}")

    # Load data
    df = pd.read_csv(train_path)
    df = df.dropna(subset=["text", "label"])
    X  = df["text"].astype(str)
    y  = df["label"].astype(str)

    print(f" Training samples : {len(df)}")
    print(f" Classes          : {sorted(y.unique())}")

    # Build pipeline
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features = p["max_features"],
            ngram_range  = (p["ngram_min"], p["ngram_max"]),
            sublinear_tf = True,        # log scaling — helps with imbalance
            strip_accents = "unicode",
            analyzer      = "word",
            min_df        = 2           # ignore very rare terms
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

    # MLflow run
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run():
        # Log params
        mlflow.log_param("max_features",  p["max_features"])
        mlflow.log_param("ngram_range",   f"{p['ngram_min']},{p['ngram_max']}")
        mlflow.log_param("C",             p["C"])
        mlflow.log_param("class_weight",  str(class_weight))
        mlflow.log_param("train_samples", len(df))

        # Train
        pipeline.fit(X, y)
        print(" Training complete")

        # Evaluate on train set 
        y_pred = pipeline.predict(X)
        f1     = f1_score(y, y_pred, average="weighted")
        acc    = accuracy_score(y, y_pred)

        mlflow.log_metric("train_f1_weighted", round(f1, 4))
        mlflow.log_metric("train_accuracy",    round(acc, 4))

        print(f"\n Train F1 (weighted): {f1:.4f}")
        print(f" Train Accuracy     : {acc:.4f}")
        print(f"\n{classification_report(y, y_pred)}")

        # Save model locally
        pickle.dump(pipeline, open(model_path, "wb"))
        print(f" Model saved -> {model_path}")

        # Log model artifact to MLflow
        mlflow.sklearn.log_model(
            pipeline,
            artifact_path    = "model",
            registered_model_name = experiment_name
        )
        print(f" Model logged to MLflow: {experiment_name}")

    return pipeline