import os
from datetime import datetime

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from models.db_models import User, UserActivity
from utils.db import db
from utils.helpers import allowed_file, ensure_upload_directory, json_dumps, json_loads, safe_filename
from utils.notifications import send_email_notification


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard") if current_user.role != "admin" else url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        if not user.is_active:
            flash("Your account is inactive. Contact the administrator.", "warning")
            return render_template("auth/login.html")

        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user, remember=remember)
        flash("Welcome back to the career platform.", "success")
        return redirect(url_for("admin.dashboard") if user.role == "admin" else url_for("student.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard") if current_user.role != "admin" else url_for("admin.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        college = request.form.get("college", "").strip()
        course = request.form.get("course", "").strip()
        year = request.form.get("year", "").strip()
        bio = request.form.get("bio", "").strip()
        skills_text = request.form.get("skills", "")

        if not full_name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("auth/register.html")

        user = User(
            full_name=full_name,
            email=email,
            role="student",
            college=college,
            course=course,
            year=year,
            bio=bio,
            skills_json=json_dumps([skill.strip() for skill in skills_text.split(",") if skill.strip()]),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        db.session.add(UserActivity(user_id=user.id, activity_type="register", title="Account created", detail="Registered on the career guidance platform"))
        db.session.commit()
        login_user(user, remember=True)
        send_email_notification(user.email, "Welcome to the Career Guidance Platform", "Your account is ready. You can now access career prediction, resume analysis, and interview practice.")
        flash("Registration successful. Your dashboard is ready.", "success")
        return redirect(url_for("student.dashboard"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.landing"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
        current_user.college = request.form.get("college", current_user.college)
        current_user.course = request.form.get("course", current_user.course)
        current_user.year = request.form.get("year", current_user.year)
        current_user.bio = request.form.get("bio", current_user.bio)
        current_user.skills_json = json_dumps(
            [skill.strip() for skill in request.form.get("skills", "").split(",") if skill.strip()]
        )

        password = request.form.get("password", "")
        if password:
            current_user.set_password(password)

        file = request.files.get("photo")
        if file and file.filename:
            ensure_upload_directory()
            if allowed_file(file.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
                filename = safe_filename(file.filename)
                target_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(target_path)
                current_user.photo = filename
            else:
                flash("Unsupported image format.", "danger")
                return redirect(url_for("auth.profile"))

        db.session.commit()
        db.session.add(UserActivity(user_id=current_user.id, activity_type="profile", title="Profile updated", detail="Updated profile and preferences"))
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    profile_skills = ", ".join(json_loads(current_user.skills_json, []))
    return render_template("auth/profile.html", profile_skills=profile_skills)
