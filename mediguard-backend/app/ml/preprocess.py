import json
from pathlib import Path

import pandas as pd


def load_symptoms(path: str = "data_pipeline/symptoms_list.json") -> list[str]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_dataset(path: str = "data/raw/mediguard_dataset_full.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def build_feature_matrix(df: pd.DataFrame, symptoms: list[str] | None = None):
    symptoms = symptoms or [column for column in df.columns if column != "disease"]
    x = df[symptoms].astype(int)
    y = df["disease"]
    return x, y


def encode_symptoms(selected_symptoms: list[str], symptoms: list[str]) -> list[int]:
    selected = {symptom.strip().lower() for symptom in selected_symptoms}
    return [1 if symptom.lower() in selected else 0 for symptom in symptoms]

