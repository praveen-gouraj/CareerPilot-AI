import os
from datetime import timedelta


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get("SECRET_KEY", "career-guidance-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'database', 'app.db')}",
    )
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    TRAINED_MODEL_FOLDER = os.path.join(BASE_DIR, "trained_model")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    ALLOWED_RESUME_EXTENSIONS = {"pdf", "docx", "txt"}
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
