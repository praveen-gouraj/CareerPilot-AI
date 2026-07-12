import os
import json
from datetime import datetime

from flask import Flask, render_template

from config import Config
from models.db_models import Admin, CareerDomain, InterviewQuestion, User
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.main import main_bp
from routes.student import student_bp
from utils.catalog import CAREER_DOMAINS, INTERVIEW_QUESTION_BANK
from utils.db import db, login_manager
from utils.helpers import json_dumps


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_reference_data(app):
    from utils.db import db

    if not User.query.filter_by(email="admin@careerplatform.com").first():
        admin_user = User(
            full_name="Platform Admin",
            email="admin@careerplatform.com",
            role="admin",
            bio="Seeded administrator account for the career guidance system.",
        )
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)

    if not Admin.query.filter_by(email="admin@careerplatform.com").first():
        admin_user = Admin(name="Platform Admin", email="admin@careerplatform.com")
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)

    for domain_name, payload in CAREER_DOMAINS.items():
        existing_domain = CareerDomain.query.filter_by(name=domain_name).first()
        if not existing_domain:
            db.session.add(
                CareerDomain(
                    name=domain_name,
                    description=payload["description"],
                    required_skills_json=json_dumps(payload["required_skills"]),
                    courses_json=json_dumps(payload["courses"]),
                    roadmap_json=json_dumps(payload["roadmap"]),
                )
            )

    if InterviewQuestion.query.count() == 0:
        for category, questions in INTERVIEW_QUESTION_BANK.items():
            for question in questions:
                db.session.add(
                    InterviewQuestion(
                        category=category,
                        question=question["question"],
                        answer_keywords_json=json_dumps(question["keywords"]),
                        difficulty="medium",
                    )
                )

    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.jinja_env.filters["from_json"] = lambda value: json.loads(value) if value else []

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["TRAINED_MODEL_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(Config.BASE_DIR, "database"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.utcnow().year}

    with app.app_context():
        db.create_all()
        seed_reference_data(app)

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
