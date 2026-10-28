import os
import re
from collections import Counter
from typing import Dict, List

from docx import Document
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

from utils.catalog import CAREER_DOMAINS, JOB_DESCRIPTIONS, SKILL_OPTIONS

STEMMER = PorterStemmer()
SKILL_LABELS = {skill["key"]: skill["label"] for skill in SKILL_OPTIONS}
SKILL_ALIASES = {
    "python": ["python"],
    "java": ["java"],
    "cpp": ["c++", "cpp", "c plus plus"],
    "sql": ["sql", "mysql", "postgresql", "sqlite", "sql server"],
    "web_dev": ["web development", "html", "css", "responsive design", "web application"],
    "cloud": ["cloud", "aws", "azure", "google cloud", "gcp"],
    "ai_ml": ["machine learning", "artificial intelligence", "deep learning", "\bml\b"],
    "cybersecurity": ["cybersecurity", "cyber security", "network security", "information security"],
    "data_structures": ["data structures", "algorithm", "algorithms", "dsa"],
    "javascript": ["javascript", "js", "ecmascript"],
    "git": ["git", "github", "gitlab", "version control"],
    "linux": ["linux", "ubuntu", "bash", "shell scripting"],
    "docker": ["docker", "containerization", "containers"],
    "react": ["react", "react.js", "reactjs"],
    "statistics": ["statistics", "statistical analysis", "probability", "hypothesis testing"],
}
CONTENT_CHECKS = [
    ("email", "Contact email", r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "Add a professional email address."),
    ("phone", "Phone number", r"(?:\+?\d[\d ().-]{7,}\d)", "Add a phone number with country code if relevant."),
    ("summary", "Professional summary", r"\b(summary|profile|objective|about me)\b", "Add a short professional summary tailored to the target role."),
    ("skills_section", "Skills section", r"\b(technical skills|skills|core competencies|technologies)\b", "Add a clearly labeled skills section."),
    ("education", "Education section", r"\b(education|university|college|degree|bachelor|master)\b", "Add your education, qualification, or relevant training."),
    ("experience", "Experience or projects", r"\b(experience|employment|work history|projects| internship|internships)\b", "Add relevant work experience, internships, or projects."),
    ("measurable_impact", "Measurable results", r"\b\d+(?:\.\d+)?\s*(%|percent|users|customers|clients|hours|days|weeks|months|years|projects|applications|requests|\$|usd)\b", "Add measurable results, such as time saved, users served, or performance improved."),
]


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
    text = text or ""
    domain = CAREER_DOMAINS.get(target_domain, CAREER_DOMAINS["Software Development"])
    required_skills = domain["required_skills"]
    matched = []
    missing = []
    text_lower = text.lower()

    for skill_key in required_skills:
        aliases = SKILL_ALIASES.get(skill_key, [skill_key.replace("_", " ")])
        found = any(
            re.search(r"(?<![a-z0-9])" + alias + r"(?![a-z0-9])", text_lower)
            for alias in aliases
        )
        label = SKILL_LABELS.get(skill_key, skill_key.replace("_", " ").title())
        (matched if found else missing).append(label)

    content_checks = [
        {"key": key, "label": label, "passed": bool(re.search(pattern, text, re.IGNORECASE)), "suggestion": suggestion}
        for key, label, pattern, suggestion in CONTENT_CHECKS
    ]
    skill_score = round((len(matched) / max(1, len(required_skills))) * 100, 2)
    content_score = round((sum(check["passed"] for check in content_checks) / len(content_checks)) * 100, 2)
    ats_score = round((skill_score * 0.65) + (content_score * 0.35), 2)
    rating = "Excellent" if ats_score >= 85 else "Good" if ats_score >= 70 else "Average" if ats_score >= 55 else "Needs Improvement"
    word_count = len(re.findall(r"\b[\w+#.-]+\b", text))
    suggestions = [f"Include relevant experience with {skill}." for skill in missing[:6]]
    suggestions.extend(check["suggestion"] for check in content_checks if not check["passed"])
    if word_count < 150:
        suggestions.append("Add more detail about your responsibilities, projects, and results.")
    if not suggestions:
        suggestions.append("Your resume covers the target skills and key sections. Keep achievements specific and current.")

    return {
        "target_domain": target_domain,
        "ats_score": ats_score,
        "rating": rating,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "strengths": matched,
        "weaknesses": missing,
        "summary": f"Found {len(matched)} of {len(required_skills)} target skills for {target_domain}.",
        "keyword_score": skill_score,
        "content_score": content_score,
        "content_checks": content_checks,
        "word_count": word_count,
        "suggestions": suggestions,
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
