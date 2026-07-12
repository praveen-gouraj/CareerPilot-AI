import json
import os
import pickle
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler

from config import Config
from utils.catalog import CAREER_DOMAINS, SKILL_OPTIONS

FEATURE_COLUMNS = [skill["key"] for skill in SKILL_OPTIONS]
MODEL_FILE = os.path.join(Config.TRAINED_MODEL_FOLDER, "career_knn_model.pkl")
SCALER_FILE = os.path.join(Config.TRAINED_MODEL_FOLDER, "career_knn_scaler.pkl")


class CareerModelBundle:
    def __init__(self, model, scaler, feature_columns, classes):
        self.model = model
        self.scaler = scaler
        self.feature_columns = feature_columns
        self.classes = classes


def _vector_from_skills(selected_skills: List[str]) -> np.ndarray:
    vector = [1 if feature in selected_skills else 0 for feature in FEATURE_COLUMNS]
    return np.array(vector, dtype=float).reshape(1, -1)


def _ensure_model_directory() -> None:
    os.makedirs(Config.TRAINED_MODEL_FOLDER, exist_ok=True)


def train_career_model(dataframe: pd.DataFrame = None) -> CareerModelBundle:
    _ensure_model_directory()
    if dataframe is None:
        dataframe = pd.read_csv(os.path.join(Config.BASE_DIR, "dataset", "career_training_data.csv"))

    x = dataframe[FEATURE_COLUMNS].astype(float).values
    y = dataframe["career"].astype(str).values

    scaler = MinMaxScaler()
    x_scaled = scaler.fit_transform(x)
    model = KNeighborsClassifier(n_neighbors=5, weights="distance")
    model.fit(x_scaled, y)

    bundle = CareerModelBundle(model=model, scaler=scaler, feature_columns=FEATURE_COLUMNS, classes=list(model.classes_))
    with open(MODEL_FILE, "wb") as model_file:
        pickle.dump(bundle, model_file)
    return bundle


def load_career_model() -> CareerModelBundle:
    _ensure_model_directory()
    if not os.path.exists(MODEL_FILE):
        return train_career_model()
    with open(MODEL_FILE, "rb") as model_file:
        bundle = pickle.load(model_file)
    return bundle


def predict_careers(selected_skills: List[str]) -> Dict:
    bundle = load_career_model()
    raw_vector = _vector_from_skills(selected_skills)
    scaled_vector = bundle.scaler.transform(raw_vector)
    probabilities = bundle.model.predict_proba(scaled_vector)[0]
    classes = bundle.model.classes_
    ranking = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
    top_matches = ranking[:3]
    recommended_domain, confidence = top_matches[0]

    return {
        "recommended_domain": recommended_domain,
        "confidence": round(float(confidence) * 100, 2),
        "top_matches": [
            {"career": career, "score": round(float(score) * 100, 2)} for career, score in top_matches
        ],
    }


def get_domain_profile(domain_name: str) -> Dict:
    return CAREER_DOMAINS.get(domain_name, CAREER_DOMAINS["Software Development"])


def analyze_skill_gap(selected_skills: List[str], target_domain: str) -> Dict:
    profile = get_domain_profile(target_domain)
    required_skills = profile["required_skills"]
    matched = sorted(set(selected_skills).intersection(required_skills))
    missing = sorted(set(required_skills) - set(selected_skills))
    score = 100 if not required_skills else round((len(matched) / len(required_skills)) * 100, 2)
    readiness = min(100, round(score + (len(selected_skills) * 2.5), 2))
    roadmap = profile["roadmap"] + [f"Work on {skill.replace('_', ' ').title()}" for skill in missing]

    return {
        "target_domain": target_domain,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "score": score,
        "readiness": readiness,
        "courses": profile["courses"],
        "roadmap": roadmap,
        "description": profile["description"],
    }


def placement_readiness_score(prediction_score: float, skill_score: float, resume_score: float, interview_score: float) -> float:
    return round((prediction_score * 0.25) + (skill_score * 0.3) + (resume_score * 0.25) + (interview_score * 0.2), 2)
