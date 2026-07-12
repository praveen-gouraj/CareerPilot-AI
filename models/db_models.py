from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from utils.db import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    college = db.Column(db.String(150))
    course = db.Column(db.String(120))
    year = db.Column(db.String(20))
    bio = db.Column(db.Text)
    photo = db.Column(db.String(255), default="default-avatar.svg")
    skills_json = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)

    career_predictions = db.relationship("CareerPrediction", backref="user", lazy=True, cascade="all, delete-orphan")
    resumes = db.relationship("Resume", backref="user", lazy=True, cascade="all, delete-orphan")
    interviews = db.relationship("InterviewResult", backref="user", lazy=True, cascade="all, delete-orphan")
    gaps = db.relationship("SkillGapAnalysis", backref="user", lazy=True, cascade="all, delete-orphan")
    bookmarks = db.relationship("CareerBookmark", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class StudentSkill(TimestampMixin, db.Model):
    __tablename__ = "student_skills"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skills_json = db.Column(db.Text, nullable=False)
    target_domain = db.Column(db.String(80))
    proficiency_score = db.Column(db.Float, default=0)


class CareerPrediction(TimestampMixin, db.Model):
    __tablename__ = "career_predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    input_skills_json = db.Column(db.Text, nullable=False)
    recommended_domain = db.Column(db.String(120), nullable=False)
    top_matches_json = db.Column(db.Text, nullable=False)
    confidence = db.Column(db.Float, default=0)


class Resume(TimestampMixin, db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    extracted_text = db.Column(db.Text)
    ats_score = db.Column(db.Float, default=0)
    keyword_matches_json = db.Column(db.Text)
    missing_keywords_json = db.Column(db.Text)
    summary_json = db.Column(db.Text)


class InterviewResult(TimestampMixin, db.Model):
    __tablename__ = "interview_results"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    interview_type = db.Column(db.String(40), nullable=False)
    score = db.Column(db.Float, default=0)
    accuracy = db.Column(db.Float, default=0)
    weak_topics_json = db.Column(db.Text)
    responses_json = db.Column(db.Text)
    question_json = db.Column(db.Text)


class SkillGapAnalysis(TimestampMixin, db.Model):
    __tablename__ = "skill_gap_analysis"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_domain = db.Column(db.String(120), nullable=False)
    current_score = db.Column(db.Float, default=0)
    missing_skills_json = db.Column(db.Text)
    roadmap_json = db.Column(db.Text)
    analysis_json = db.Column(db.Text)


class Admin(TimestampMixin, db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), default="superadmin", nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class CareerDomain(TimestampMixin, db.Model):
    __tablename__ = "career_domains"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills_json = db.Column(db.Text, nullable=False)
    courses_json = db.Column(db.Text, nullable=False)
    roadmap_json = db.Column(db.Text, nullable=False)


class InterviewQuestion(TimestampMixin, db.Model):
    __tablename__ = "interview_questions"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(30), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer_keywords_json = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default="medium", nullable=False)


class CareerBookmark(TimestampMixin, db.Model):
    __tablename__ = "career_bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    domain_name = db.Column(db.String(120), nullable=False)
    note = db.Column(db.String(255))


class UserActivity(TimestampMixin, db.Model):
    __tablename__ = "user_activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    detail = db.Column(db.Text)
    score = db.Column(db.Float, default=0)
