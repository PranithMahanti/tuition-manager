"""
lesson_service.py
-----------------
Thin layer on top of session_service for logging lesson content
(topic taught, homework assigned, teacher remarks).
"""
from typing import Optional, List
from database.db import db_session, get_db
from database.models import ClassSession


def log_lesson(
    session_id: int,
    topic_taught: str,
    homework: str = "",
    remarks: str = "",
    is_attended: bool = True,
) -> Optional[ClassSession]:
    """Write lesson notes into an existing ClassSession."""
    with db_session() as db:
        session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
        if not session:
            return None
        session.topic_taught = topic_taught.strip()
        session.homework = homework.strip()
        session.remarks = remarks.strip()
        session.is_attended = is_attended
        db.flush()
        db.refresh(session)
        return session


def get_unlogged_sessions(student_id: int) -> List[ClassSession]:
    """
    Return past sessions that have no topic logged yet.
    Useful to flag sessions needing teacher input.
    """
    import datetime
    today = datetime.date.today()
    db = get_db()
    try:
        return (
            db.query(ClassSession)
            .filter(
                ClassSession.student_id == student_id,
                ClassSession.session_date <= today,
                (ClassSession.topic_taught == "") | (ClassSession.topic_taught == None),
            )
            .order_by(ClassSession.session_date)
            .all()
        )
    finally:
        db.close()


def get_lesson_log(student_id: int, year: int, month: int) -> List[dict]:
    """
    Return a structured lesson log for a student's month —
    used for report generation.
    """
    import calendar
    import datetime
    _, days_in_month = calendar.monthrange(year, month)
    db = get_db()
    try:
        sessions = (
            db.query(ClassSession)
            .filter(
                ClassSession.student_id == student_id,
                ClassSession.session_date >= datetime.date(year, month, 1),
                ClassSession.session_date <= datetime.date(year, month, days_in_month),
                ClassSession.is_attended == True,
            )
            .order_by(ClassSession.session_date)
            .all()
        )
        return [
            {
                "date": s.session_date.strftime("%d %b %Y"),
                "topic": s.topic_taught or "—",
                "homework": s.homework or "—",
                "remarks": s.remarks or "—",
            }
            for s in sessions
        ]
    finally:
        db.close()
