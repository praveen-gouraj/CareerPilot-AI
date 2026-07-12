from datetime import datetime
from typing import Dict, List

from models.db_models import CareerPrediction, InterviewResult, Resume, SkillGapAnalysis, User
from utils.ml_utils import placement_readiness_score


def build_user_rankings() -> List[Dict]:
    rankings = []
    students = User.query.filter_by(role="student", is_active=True).all()
    for student in students:
        latest_prediction = CareerPrediction.query.filter_by(user_id=student.id).order_by(CareerPrediction.created_at.desc()).first()
        latest_resume = Resume.query.filter_by(user_id=student.id).order_by(Resume.created_at.desc()).first()
        latest_interview = InterviewResult.query.filter_by(user_id=student.id).order_by(InterviewResult.created_at.desc()).first()
        latest_gap = SkillGapAnalysis.query.filter_by(user_id=student.id).order_by(SkillGapAnalysis.created_at.desc()).first()
        readiness = placement_readiness_score(
            latest_prediction.confidence if latest_prediction else 0,
            latest_gap.current_score if latest_gap else 0,
            latest_resume.ats_score if latest_resume else 0,
            latest_interview.score if latest_interview else 0,
        )
        rankings.append(
            {
                "user": student,
                "readiness": readiness,
                "career": latest_prediction.recommended_domain if latest_prediction else "N/A",
                "resume_score": latest_resume.ats_score if latest_resume else 0,
                "interview_score": latest_interview.score if latest_interview else 0,
                "skill_score": latest_gap.current_score if latest_gap else 0,
                "updated_at": max(
                    [value for value in [
                        latest_prediction.created_at if latest_prediction else None,
                        latest_resume.created_at if latest_resume else None,
                        latest_interview.created_at if latest_interview else None,
                        latest_gap.created_at if latest_gap else None,
                    ] if value],
                    default=datetime.utcnow(),
                ),
            }
        )
    rankings.sort(key=lambda item: item["readiness"], reverse=True)
    for position, item in enumerate(rankings, start=1):
        item["rank"] = position
    return rankings
