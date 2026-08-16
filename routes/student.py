import io
import json
import os
import random
from datetime import datetime
from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from models.db_models import CareerBookmark, CareerPrediction, InterviewQuestion, InterviewResult, Resume, SkillGapAnalysis, StudentSkill, UserActivity, User
from utils.catalog import CAREER_DOMAINS, INTERVIEW_QUESTION_BANK, SKILL_OPTIONS
from utils.db import db
from utils.helpers import allowed_file, json_dumps, json_loads, parse_skill_selection, percent, safe_filename
from utils.insights import build_user_rankings
from utils.notifications import send_email_notification
from utils.ml_utils import analyze_skill_gap, placement_readiness_score, predict_careers
from utils.nlp_utils import analyze_resume, evaluate_answer, extract_keywords, extract_text_from_file, generate_resume_suggestions


student_bp = Blueprint("student", __name__)


def _skill_labels_map():
    return {skill["key"]: skill["label"] for skill in SKILL_OPTIONS}


def _career_options():
    return list(CAREER_DOMAINS.keys())


@student_bp.route("/dashboard")
@login_required
def dashboard():
    prediction_count = CareerPrediction.query.filter_by(user_id=current_user.id).count()
    resume_count = Resume.query.filter_by(user_id=current_user.id).count()
    interview_count = InterviewResult.query.filter_by(user_id=current_user.id).count()
    analysis_count = SkillGapAnalysis.query.filter_by(user_id=current_user.id).count()
    bookmark_count = CareerBookmark.query.filter_by(user_id=current_user.id).count()

    recent_predictions = CareerPrediction.query.filter_by(user_id=current_user.id).order_by(CareerPrediction.created_at.desc()).limit(4).all()
    recent_resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).limit(4).all()
    recent_interviews = InterviewResult.query.filter_by(user_id=current_user.id).order_by(InterviewResult.created_at.desc()).limit(4).all()
    recent_analysis = SkillGapAnalysis.query.filter_by(user_id=current_user.id).order_by(SkillGapAnalysis.created_at.desc()).first()
    recent_activities = UserActivity.query.filter_by(user_id=current_user.id).order_by(UserActivity.created_at.desc()).limit(5).all()

    latest_prediction = recent_predictions[0] if recent_predictions else None
    latest_resume = recent_resumes[0] if recent_resumes else None
    latest_interview = recent_interviews[0] if recent_interviews else None

    prediction_score = latest_prediction.confidence if latest_prediction else 0
    skill_score = recent_analysis.current_score if recent_analysis else 0
    resume_score = latest_resume.ats_score if latest_resume else 0
    interview_score = latest_interview.score if latest_interview else 0
    readiness = placement_readiness_score(prediction_score, skill_score, resume_score, interview_score)

    history = {
        "predictions": [record.confidence for record in reversed(recent_predictions)],
        "resumes": [record.ats_score for record in reversed(recent_resumes)],
        "interviews": [record.score for record in reversed(recent_interviews)],
    }

    return render_template(
        "student/dashboard.html",
        metrics={
            "predictions": prediction_count,
            "resumes": resume_count,
            "interviews": interview_count,
            "analyses": analysis_count,
            "bookmarks": bookmark_count,
            "readiness": readiness,
        },
        recent_predictions=recent_predictions,
        recent_resumes=recent_resumes,
        recent_interviews=recent_interviews,
        recent_analysis=recent_analysis,
        recent_activities=recent_activities,
        history_json=json.dumps(history),
    )


@student_bp.route("/career-prediction", methods=["GET", "POST"])
@login_required
def career_prediction():
    selected_skills = []
    result = None
    if request.method == "POST":
        selected_skills = parse_skill_selection(request.form, [skill["key"] for skill in SKILL_OPTIONS])
        if not selected_skills:
            flash("Choose at least one skill to generate recommendations.", "warning")
        else:
            result = predict_careers(selected_skills)
            db.session.add(
                StudentSkill(
                    user_id=current_user.id,
                    skills_json=json_dumps(selected_skills),
                    target_domain=result["recommended_domain"],
                    proficiency_score=result["confidence"],
                )
            )
            db.session.add(
                CareerPrediction(
                    user_id=current_user.id,
                    input_skills_json=json_dumps(selected_skills),
                    recommended_domain=result["recommended_domain"],
                    top_matches_json=json_dumps(result["top_matches"]),
                    confidence=result["confidence"],
                )
            )
            db.session.commit()
            db.session.add(UserActivity(user_id=current_user.id, activity_type="career_prediction", title=f"Predicted {result['recommended_domain']}", detail="Generated top career matches", score=result["confidence"]))
            db.session.commit()
            send_email_notification(current_user.email, "Career prediction ready", f"Your top recommendation is {result['recommended_domain']} with confidence {result['confidence']}%.")
            flash("Career recommendation generated successfully.", "success")

    latest_prediction = CareerPrediction.query.filter_by(user_id=current_user.id).order_by(CareerPrediction.created_at.desc()).first()
    return render_template(
        "student/career_prediction.html",
        skills=SKILL_OPTIONS,
        selected_skills=selected_skills,
        result=result,
        latest_prediction=latest_prediction,
    )

@student_bp.route("/career-assistant")
@login_required
def career_assistant():
    return render_template("student/career_assistant.html")


@student_bp.route("/bookmark-career/<domain_name>", methods=["POST"])
@login_required
def bookmark_career(domain_name):
    note = request.form.get("note", "").strip()
    existing = CareerBookmark.query.filter_by(user_id=current_user.id, domain_name=domain_name).first()
    if existing:
        existing.note = note or existing.note
    else:
        db.session.add(CareerBookmark(user_id=current_user.id, domain_name=domain_name, note=note))
    db.session.commit()
    flash(f"Saved {domain_name} to bookmarks.", "success")
    return redirect(url_for("student.career_prediction"))


@student_bp.route("/bookmarks")
@login_required
def bookmarks():
    saved = CareerBookmark.query.filter_by(user_id=current_user.id).order_by(CareerBookmark.created_at.desc()).all()
    return render_template("student/bookmarks.html", bookmarks=saved, career_domains=_career_options())


@student_bp.route("/skill-gap", methods=["GET", "POST"])
@login_required
def skill_gap():
    analysis = None
    selected_skills = []
    target_domain = request.form.get("target_domain", "Software Development")

    if request.method == "POST":
        selected_skills = parse_skill_selection(request.form, [skill["key"] for skill in SKILL_OPTIONS])
        if not selected_skills:
            flash("Select your current skills to analyze the gap.", "warning")
        else:
            analysis = analyze_skill_gap(selected_skills, target_domain)
            db.session.add(
                StudentSkill(
                    user_id=current_user.id,
                    skills_json=json_dumps(selected_skills),
                    target_domain=target_domain,
                    proficiency_score=analysis["score"],
                )
            )
            db.session.add(
                SkillGapAnalysis(
                    user_id=current_user.id,
                    target_domain=target_domain,
                    current_score=analysis["score"],
                    missing_skills_json=json_dumps(analysis["missing_skills"]),
                    roadmap_json=json_dumps(analysis["roadmap"]),
                    analysis_json=json_dumps(analysis),
                )
            )
            db.session.commit()
            db.session.add(UserActivity(user_id=current_user.id, activity_type="skill_gap", title=f"Skill gap for {target_domain}", detail="Generated learning roadmap", score=analysis["score"]))
            db.session.commit()
            flash("Skill gap analysis generated.", "success")

    latest_analysis = SkillGapAnalysis.query.filter_by(user_id=current_user.id).order_by(SkillGapAnalysis.created_at.desc()).first()
    return render_template(
        "student/skill_gap.html",
        skills=SKILL_OPTIONS,
        career_domains=_career_options(),
        selected_skills=selected_skills,
        analysis=analysis,
        latest_analysis=latest_analysis,
        target_domain=target_domain,
    )


@student_bp.route("/resume-analyzer", methods=["GET", "POST"])
@login_required
def resume_analyzer():
    analysis = None
    extracted_text = ""
    target_domain = request.form.get("target_domain", "Software Development")

    if request.method == "POST":
        resume_file = request.files.get("resume_file")
        if not resume_file or not resume_file.filename:
            flash("Upload a resume file to continue.", "warning")
        elif not allowed_file(resume_file.filename, current_app.config["ALLOWED_RESUME_EXTENSIONS"]):
            flash("Only PDF, DOCX, and TXT files are supported.", "danger")
        else:
            os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
            filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{safe_filename(resume_file.filename)}"
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            resume_file.save(file_path)
            extracted_text = extract_text_from_file(file_path)
            analysis = analyze_resume(extracted_text, target_domain)

            db.session.add(
                Resume(
                    user_id=current_user.id,
                    filename=filename,
                    file_type=resume_file.filename.rsplit(".", 1)[1].lower(),
                    extracted_text=extracted_text[:5000],
                    ats_score=analysis["ats_score"],
                    keyword_matches_json=json_dumps(analysis["matched_keywords"]),
                    missing_keywords_json=json_dumps(analysis["missing_keywords"]),
                    summary_json=json_dumps({"summary": analysis["summary"], "rating": analysis["rating"]}),
                )
            )
            db.session.commit()
            db.session.add(UserActivity(user_id=current_user.id, activity_type="resume_analysis", title="Resume analyzed", detail=f"ATS score {analysis['ats_score']} for {target_domain}", score=analysis["ats_score"]))
            db.session.commit()
            send_email_notification(current_user.email, "Resume analysis completed", f"Your resume ATS score for {target_domain} is {analysis['ats_score']}%.")
            flash("Resume analysis completed.", "success")

    latest_resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).first()
    suggestions = generate_resume_suggestions(json_loads(latest_resume.missing_keywords_json, []) if latest_resume else [])
    return render_template(
        "student/resume_analyzer.html",
        career_domains=_career_options(),
        analysis=analysis,
        extracted_preview=extracted_text[:1200],
        latest_resume=latest_resume,
        target_domain=target_domain,
        suggestions=suggestions,
    )


@student_bp.route("/mock-interview", methods=["GET", "POST"])
@login_required
def mock_interview():
    category = request.values.get("category", "technical")
    question = None
    result = None

    if request.method == "POST":
        question_id = request.form.get("question_id")
        response_text = request.form.get("response_text", "")
        interview_question = InterviewQuestion.query.get(int(question_id)) if question_id else None
        if interview_question:
            keywords = json_loads(interview_question.answer_keywords_json, [])
            result = evaluate_answer(response_text, keywords)
            db.session.add(
                InterviewResult(
                    user_id=current_user.id,
                    interview_type=category,
                    score=result["score"],
                    accuracy=result["coverage"],
                    weak_topics_json=json_dumps(result["weak_topics"]),
                    responses_json=json_dumps({"answer": response_text, "matched": result["matched_keywords"]}),
                    question_json=json_dumps({"question": interview_question.question, "keywords": keywords}),
                )
            )
            db.session.commit()
            db.session.add(UserActivity(user_id=current_user.id, activity_type="mock_interview", title="Interview evaluated", detail=f"Score {result['score']} for {category} interview", score=result["score"]))
            db.session.commit()
            flash("Interview response evaluated.", "success")
            question = interview_question

    if question is None:
        questions = InterviewQuestion.query.filter_by(category=category).all()
        if not questions:
            questions = InterviewQuestion.query.all()
        question = random.choice(questions) if questions else None

    latest_interview = InterviewResult.query.filter_by(user_id=current_user.id).order_by(InterviewResult.created_at.desc()).first()
    return render_template(
        "student/mock_interview.html",
        category=category,
        question=question,
        result=result,
        latest_interview=latest_interview,
    )


@student_bp.route("/analytics")
@login_required
def analytics():
    prediction_history = CareerPrediction.query.filter_by(user_id=current_user.id).order_by(CareerPrediction.created_at.asc()).all()
    resume_history = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.asc()).all()
    interview_history = InterviewResult.query.filter_by(user_id=current_user.id).order_by(InterviewResult.created_at.asc()).all()
    gap_history = SkillGapAnalysis.query.filter_by(user_id=current_user.id).order_by(SkillGapAnalysis.created_at.asc()).all()

    latest_prediction = prediction_history[-1] if prediction_history else None
    latest_resume = resume_history[-1] if resume_history else None
    latest_interview = interview_history[-1] if interview_history else None
    latest_gap = gap_history[-1] if gap_history else None
    readiness = placement_readiness_score(
        latest_prediction.confidence if latest_prediction else 0,
        latest_gap.current_score if latest_gap else 0,
        latest_resume.ats_score if latest_resume else 0,
        latest_interview.score if latest_interview else 0,
    )

    return render_template(
        "student/analytics.html",
        prediction_history=[item.confidence for item in prediction_history],
        resume_history=[item.ats_score for item in resume_history],
        interview_history=[item.score for item in interview_history],
        gap_history=[item.current_score for item in gap_history],
        readiness=readiness,
        latest_prediction=latest_prediction,
        latest_resume=latest_resume,
        latest_interview=latest_interview,
        latest_gap=latest_gap,
    )


@student_bp.route("/assistant", methods=["POST"])
@login_required
def assistant():
    message = request.json.get("message", "").lower()
    reply = "I can help with career prediction, resume review, skill gap analysis, and interview practice."
    if "career" in message:
        reply = "Try the Career Prediction page and select your strongest technical and communication skills."
    elif "resume" in message:
        reply = "Upload a PDF or DOCX resume on the Resume Analyzer page and compare it with a target role."
    elif "interview" in message:
        reply = "Use the Mock Interview page to answer random technical or HR questions and get a score."
    elif "skill" in message:
        reply = "The Skill Gap page highlights missing skills and generates a learning roadmap for your target domain."
    return jsonify({"reply": reply})


@student_bp.route("/download-report")
@login_required
def download_report():
    latest_prediction = CareerPrediction.query.filter_by(user_id=current_user.id).order_by(CareerPrediction.created_at.desc()).first()
    latest_resume = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.created_at.desc()).first()
    latest_interview = InterviewResult.query.filter_by(user_id=current_user.id).order_by(InterviewResult.created_at.desc()).first()
    latest_gap = SkillGapAnalysis.query.filter_by(user_id=current_user.id).order_by(SkillGapAnalysis.created_at.desc()).first()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    pdf.setTitle("Placement Readiness Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "AI-Based Career Guidance Report")
    y -= 28
    pdf.setFont("Helvetica", 11)
    lines = [
        f"Student: {current_user.full_name}",
        f"Email: {current_user.email}",
        f"Recommended Career: {latest_prediction.recommended_domain if latest_prediction else 'N/A'}",
        f"Career Confidence: {latest_prediction.confidence if latest_prediction else 0}%",
        f"Resume ATS Score: {latest_resume.ats_score if latest_resume else 0}%",
        f"Interview Score: {latest_interview.score if latest_interview else 0}%",
        f"Skill Gap Score: {latest_gap.current_score if latest_gap else 0}%",
    ]
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 18
    pdf.drawString(50, y - 4, "This report is generated by the placement platform.")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="placement_report.pdf", mimetype="application/pdf")


@student_bp.route("/rankings")
@login_required
def rankings():
    rankings = build_user_rankings()
    return render_template("student/rankings.html", rankings=rankings)

