# preprocess.py
# src/preprocess.py
import pandas as pd
import boto3
import os
import yaml
from io import StringIO


# CONFIG

params = yaml.safe_load(open("params.yaml"))
pre    = params["preprocess"]
aws    = params["aws"]

BUCKET = aws["bucket"]
FILES  = {
    "ethics":   pre["ethics_input"],
    "fallacy":  pre["fallacy_input"],
    "mappings": pre["mappings_input"]
}
PROCESSED_DIR = "data/processed"

# HELPER — Read any CSV from S3

def read_s3_csv(bucket, key):
    print(f" Reading s3://{bucket}/{key}")
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj["Body"].read().decode("utf-8")
    df = pd.read_csv(StringIO(content))
    print(f"   {len(df)} rows loaded")
    return df


# LOAD ALL 3 FILES FROM S3

df_ethics   = read_s3_csv(BUCKET, FILES["ethics"])
df_fallacy  = read_s3_csv(BUCKET, FILES["fallacy"])
df_mappings = read_s3_csv(BUCKET, FILES["mappings"])

print("\n Ethics columns:", df_ethics.columns.tolist())
print(" Fallacy columns:", df_fallacy.columns.tolist())
print(" Mappings columns:", df_mappings.columns.tolist())



# ETHICS PIPELINE

# BUILD ETHICS TEXT COLUMN
# combines scenario + decision + reason
# into one single text input for the model

print("\n\n Processing ETHICS dataset...")

df_eth = df_ethics.copy()

df_eth["text"] = (
    df_eth["scenario"].astype(str) + " " +
    df_eth["decision"].astype(str) + " " +
    df_eth["reason"].astype(str)
)
df_eth["label"] = df_eth["ethics_label"].astype(str)
df_eth = df_eth[["text", "label"]]

print(f" Ethics label distribution:\n{df_eth['label'].value_counts()}")


#CLEAN ETHICS

df_eth = df_eth.dropna(subset=["text", "label"])
df_eth["text"]  = df_eth["text"].str.lower().str.strip()
df_eth["label"] = df_eth["label"].str.lower().str.strip()
df_eth = df_eth[df_eth["text"].str.len() > pre["min_text_length"]]
df_eth = df_eth.drop_duplicates(subset=["text"])

print(f" Ethics after cleaning: {len(df_eth)} rows")