import json
from functools import wraps

import os
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required

from models.db_models import CareerDomain, CareerPrediction, InterviewQuestion, InterviewResult, Resume, SkillGapAnalysis, User, UserActivity
from utils.db import db
from utils.helpers import allowed_file, json_dumps, json_loads, safe_filename
from utils.insights import build_user_rankings


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            flash("Administrator access required.", "danger")
            return redirect(url_for("student.dashboard"))
        return view_function(*args, **kwargs)

    return wrapper


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    users = User.query.count()
    students = User.query.filter_by(role="student").count()
    admins = User.query.filter_by(role="admin").count()
    predictions = CareerPrediction.query.count()
    resumes = Resume.query.count()
    interviews = InterviewResult.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(6).all()
    domains = CareerDomain.query.all()
    return render_template(
        "admin/dashboard.html",
        metrics={
            "users": users,
            "students": students,
            "admins": admins,
            "predictions": predictions,
            "resumes": resumes,
            "interviews": interviews,
            "domains": len(domains),
        },
        recent_users=recent_users,
        domains=domains,
    )


@admin_bp.route("/reports")
@admin_required
def reports():
    rankings = build_user_rankings()[:10]
    recent_activities = UserActivity.query.order_by(UserActivity.created_at.desc()).limit(12).all()
    return render_template("admin/reports.html", rankings=rankings, recent_activities=recent_activities)


@admin_bp.route("/datasets", methods=["GET", "POST"])
@admin_required
def datasets():
    if request.method == "POST":
        dataset_file = request.files.get("dataset_file")
        dataset_type = request.form.get("dataset_type", "career")
        if not dataset_file or not dataset_file.filename:
            flash("Choose a dataset file to upload.", "warning")
            return redirect(url_for("admin.datasets"))

        if not allowed_file(dataset_file.filename, {"csv", "json"}):
            flash("Only CSV and JSON datasets are supported.", "danger")
            return redirect(url_for("admin.datasets"))

        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        filename = f"dataset_{safe_filename(dataset_file.filename)}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        dataset_file.save(save_path)

        if dataset_type == "career" and filename.endswith(".csv"):
            target_path = os.path.join(current_app.root_path, "dataset", "career_training_data.csv")
            dataset_file.stream.seek(0)
            dataset_file.save(target_path)
            flash("Career dataset updated. Retrain the model to refresh predictions.", "success")
        elif dataset_type == "questions" and filename.endswith(".json"):
            with open(save_path, "r", encoding="utf-8") as source_file:
                question_items = json.load(source_file)
            for item in question_items:
                db.session.add(
                    InterviewQuestion(
                        category=item.get("category", "technical"),
                        question=item.get("question", "").strip(),
                        answer_keywords_json=json_dumps(item.get("answer_keywords", [])),
                        difficulty=item.get("difficulty", "medium"),
                    )
                )
            db.session.commit()
            flash("Interview question dataset imported successfully.", "success")
        else:
            flash("Dataset uploaded, but the file type does not match the selected dataset category.", "warning")

        return redirect(url_for("admin.datasets"))

    career_count = CareerPrediction.query.count()
    question_count = InterviewQuestion.query.count()
    return render_template("admin/datasets.html", career_count=career_count, question_count=question_count)


@admin_bp.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    search = request.args.get("search", "").strip()
    query = User.query
    if search:
        like_term = f"%{search}%"
        query = query.filter((User.full_name.ilike(like_term)) | (User.email.ilike(like_term)))
    users = query.order_by(User.created_at.desc()).all()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        role = request.form.get("role", "student")
        is_active = request.form.get("is_active") == "on"
        target_user = User.query.get(int(user_id))
        if target_user:
            target_user.role = role
            target_user.is_active = is_active
            db.session.commit()
            flash("User updated successfully.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/users.html", users=users, search=search)


@admin_bp.route("/questions", methods=["GET", "POST"])
@admin_required
def questions():
    if request.method == "POST":
        category = request.form.get("category", "technical")
        question_text = request.form.get("question", "").strip()
        keywords = [word.strip() for word in request.form.get("keywords", "").split(",") if word.strip()]
        difficulty = request.form.get("difficulty", "medium")
        if question_text and keywords:
            db.session.add(
                InterviewQuestion(
                    category=category,
                    question=question_text,
                    answer_keywords_json=json_dumps(keywords),
                    difficulty=difficulty,
                )
            )
            db.session.commit()
            flash("Interview question added.", "success")
        else:
            flash("Question text and keywords are required.", "warning")
        return redirect(url_for("admin.questions"))

    questions = InterviewQuestion.query.order_by(InterviewQuestion.created_at.desc()).all()
    return render_template("admin/questions.html", questions=questions)


@admin_bp.route("/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def delete_question(question_id):
    question = InterviewQuestion.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question removed.", "info")
    return redirect(url_for("admin.questions"))


@admin_bp.route("/domains", methods=["GET", "POST"])
@admin_required
def domains():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        required_skills = [skill.strip() for skill in request.form.get("required_skills", "").split(",") if skill.strip()]
        courses = [course.strip() for course in request.form.get("courses", "").split(",") if course.strip()]
        roadmap = [item.strip() for item in request.form.get("roadmap", "").split("\n") if item.strip()]
        if name and description and required_skills:
            existing = CareerDomain.query.filter_by(name=name).first()
            if existing:
                existing.description = description
                existing.required_skills_json = json_dumps(required_skills)
                existing.courses_json = json_dumps(courses)
                existing.roadmap_json = json_dumps(roadmap)
            else:
                db.session.add(
                    CareerDomain(
                        name=name,
                        description=description,
                        required_skills_json=json_dumps(required_skills),
                        courses_json=json_dumps(courses),
                        roadmap_json=json_dumps(roadmap),
                    )
                )
            db.session.commit()
            flash("Career domain saved.", "success")
        else:
            flash("Provide the domain name, description, and required skills.", "warning")
        return redirect(url_for("admin.domains"))

    domains = CareerDomain.query.order_by(CareerDomain.created_at.desc()).all()
    return render_template("admin/domains.html", domains=domains)
