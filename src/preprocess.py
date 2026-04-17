# preprocess.py
# src/preprocess.py
import pandas as pd
import boto3
import os
import yaml
from io import StringIO
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle


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


# ENCODE + SPLIT + SAVE ETHICS

le_eth = LabelEncoder()
df_eth["label_encoded"] = le_eth.fit_transform(df_eth["label"])

print("\n  Ethics label mapping:")
for i, cls in enumerate(le_eth.classes_):
    print(f"   {i} → {cls}")

eth_train, eth_test = train_test_split(
    df_eth,
    test_size=pre["test_size"],
    random_state=pre["random_state"],
    stratify=df_eth["label_encoded"]
)

os.makedirs(PROCESSED_DIR, exist_ok=True)

eth_train.to_csv(pre["ethics_train"],   index=False)
eth_test.to_csv(pre["ethics_test"],     index=False)
pickle.dump(le_eth, open(pre["ethics_encoder"], "wb"))

print(f" Saved -> {pre['ethics_train']}   ({len(eth_train)} rows)")
print(f" Saved -> {pre['ethics_test']}    ({len(eth_test)} rows)")
print(f" Saved -> {pre['ethics_encoder']}")



# FALLACY PIPELINE


#  EXTRACT FALLACY COLUMNS
# only keep source_article + updated_label
# drop: original_url, old_label,
#        explanations, rationale

print("\n\n Processing FALLACY dataset...")

df_fal = df_fallacy[["source_article", "updated_label"]].copy()
df_fal = df_fal.rename(columns={
    "source_article": "text",
    "updated_label":  "label"
})

print(f"Fallacy label distribution:\n{df_fal['label'].value_counts()}")
