import os
import re
from collections import Counter
from typing import Dict, List

import numpy as np
from docx import Document
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

from utils.catalog import JOB_DESCRIPTIONS

STEMMER = PorterStemmer()


def extract_text_from_file(file_path: str) -> str:
    extension = os.path.splitext(file_path)[1].lower().replace(".", "")
    if extension == "pdf":
        reader = PdfReader(file_path)
        return " ".join(page.extract_text() or "" for page in reader.pages)
    if extension == "docx":
        document = Document(file_path)
        return " ".join(paragraph.text for paragraph in document.paragraphs)
    with open(file_path, "r", encoding="utf-8", errors="ignore") as text_file:
        return text_file.read()


def normalize_text(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z0-9+#/.]+", text.lower())
    tokens = []
    for word in words:
        if word in ENGLISH_STOP_WORDS:
            continue
        stemmed = STEMMER.stem(word)
        if len(stemmed) > 1:
            tokens.append(stemmed)
    return tokens


def extract_keywords(text: str, top_n: int = 15) -> List[str]:
    tokens = normalize_text(text)
    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]


def analyze_resume(text: str, target_domain: str) -> Dict:
    description = JOB_DESCRIPTIONS.get(target_domain, next(iter(JOB_DESCRIPTIONS.values())))
    text = text or ""
    corpus = [text, description]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])

    resume_keywords = set(extract_keywords(text, top_n=25))
    job_keywords = set(extract_keywords(description, top_n=20))
    matched = sorted(resume_keywords.intersection(job_keywords))
    missing = sorted(job_keywords - resume_keywords)

    length_bonus = min(15, len(text.split()) / 60)
    ats_score = min(100, round((similarity * 72) + (len(matched) * 2.4) + length_bonus, 2))
    rating = "Excellent" if ats_score >= 85 else "Good" if ats_score >= 70 else "Average" if ats_score >= 55 else "Needs Improvement"

    return {
        "target_domain": target_domain,
        "ats_score": ats_score,
        "rating": rating,
        "matched_keywords": matched,
        "missing_keywords": missing[:12],
        "strengths": matched[:8],
        "weaknesses": missing[:8],
        "summary": f"Resume alignment with {target_domain} job profile is {round(similarity * 100, 1)}%.",
        "keyword_score": round(min(100, len(matched) * 6.5 + similarity * 40), 2),
    }


def evaluate_answer(answer: str, expected_keywords: List[str]) -> Dict:
    answer_tokens = set(normalize_text(answer))
    expected_set = set(normalize_text(" ".join(expected_keywords)))
    overlap = answer_tokens.intersection(expected_set)
    coverage = len(overlap) / max(1, len(expected_set))
    length_factor = min(1.0, len(answer.split()) / 60)
    score = round(min(100, (coverage * 75) + (length_factor * 25)), 2)
    feedback = "Strong answer with clear concept coverage." if score >= 80 else "Good attempt, but add more structure and technical terms." if score >= 60 else "Answer is too short or misses core concepts."
    return {
        "score": score,
        "coverage": round(coverage * 100, 2),
        "feedback": feedback,
        "matched_keywords": sorted(overlap),
        "weak_topics": sorted(expected_set - overlap),
    }


def generate_resume_suggestions(missing_keywords: List[str]) -> List[str]:
    suggestions = []
    for keyword in missing_keywords[:10]:
        suggestions.append(f"Include measurable evidence for {keyword}.")
    if not suggestions:
        suggestions.append("Add more impact-driven bullet points and project outcomes.")
    return suggestions
