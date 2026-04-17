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