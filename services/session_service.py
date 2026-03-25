import datetime
import calendar
from typing import List, Optional, Tuple

from sqlalchemy.orm import joinedload

from database.db import db_session, get_db
from database.models import ClassSession, Schedule, Student


# Auto-gen
def generate_monthly_sessions(
    student_id: int, year: int, month: int
) -> Tuple[int, int]:
    db = get_db()
    try:
        schedules: List[Schedule] = (
            db.query(Schedule).filter(Schedule.student_id == student_id).all()
        )
        if not schedules:
            return 0, 0

        _, days_in_month = calendar.monthrange(year, month)
        targets: List[Tuple[datetime.date, Schedule]] = []
        for day_num in range(1, days_in_month + 1):
            date = datetime.date(year, month, day_num)
            for sched in schedules:
                if date.weekday() == sched.day_of_week:
                    targets.append((date, sched))

        existing_dates = {
            s.session_date
            for s in db.query(ClassSession)
            .filter(
                ClassSession.student_id == student_id,
                ClassSession.session_date >= datetime.date(year, month, 1),
                ClassSession.session_date
                <= datetime.date(year, month, days_in_month),
            )
            .all()
        }

        created = 0
        skipped = 0
        with db_session() as write_db:
            for date, sched in targets:
                if date in existing_dates:
                    skipped += 1
                    continue
                session = ClassSession(
                    student_id=student_id,
                    session_date=date,
                    start_time=sched.start_time,
                    end_time=sched.end_time,
                    is_generated=True,
                    is_attended=True,
                )
                write_db.add(session)
                existing_dates.add(date)
                created += 1

        return created, skipped
    finally:
        db.close()


def generate_sessions_for_all_students(year: int, month: int) -> dict:
    db = get_db()
    try:
        students = db.query(Student).filter(Student.is_active == True).all()
        results = {}
        for student in students:
            created, skipped = generate_monthly_sessions(student.id, year, month)
            results[student.id] = {"name": student.name, "created": created, "skipped": skipped}
        return results
    finally:
        db.close()


# CRUD
def create_session(
    student_id: int,
    session_date: datetime.date,
    start_time: Optional[datetime.time] = None,
    end_time: Optional[datetime.time] = None,
    topic_taught: str = "",
    homework: str = "",
    remarks: str = "",
    is_attended: bool = True,
) -> ClassSession:
    with db_session() as db:
        session = ClassSession(
            student_id=student_id,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            topic_taught=topic_taught,
            homework=homework,
            remarks=remarks,
            is_attended=is_attended,
            is_generated=False,
        )
        db.add(session)
        db.flush()
        db.refresh(session)
        return session


def get_sessions_for_student(
    student_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[ClassSession]:
    db = get_db()
    try:
        q = (
            db.query(ClassSession)
            .options(joinedload(ClassSession.student))
            .filter(ClassSession.student_id == student_id)
        )
        if year and month:
            _, days_in_month = calendar.monthrange(year, month)
            q = q.filter(
                ClassSession.session_date >= datetime.date(year, month, 1),
                ClassSession.session_date <= datetime.date(year, month, days_in_month),
            )
        return q.order_by(ClassSession.session_date).all()
    finally:
        db.close()


def get_sessions_for_date(date: datetime.date) -> List[ClassSession]:
    db = get_db()
    try:
        return (
            db.query(ClassSession)
            .options(joinedload(ClassSession.student))
            .filter(ClassSession.session_date == date)
            .order_by(ClassSession.start_time)
            .all()
        )
    finally:
        db.close()


def get_upcoming_sessions(days_ahead: int = 7) -> List[ClassSession]:
    today = datetime.date.today()
    future = today + datetime.timedelta(days=days_ahead)
    db = get_db()
    try:
        return (
            db.query(ClassSession)
            .options(joinedload(ClassSession.student))
            .filter(
                ClassSession.session_date > today,
                ClassSession.session_date <= future,
            )
            .order_by(ClassSession.session_date, ClassSession.start_time)
            .all()
        )
    finally:
        db.close()


def get_session_by_id(session_id: int) -> Optional[ClassSession]:
    db = get_db()
    try:
        return (
            db.query(ClassSession)
            .options(joinedload(ClassSession.student))
            .filter(ClassSession.id == session_id)
            .first()
        )
    finally:
        db.close()


def update_session(session_id: int, **kwargs) -> Optional[ClassSession]:
    with db_session() as db:
        session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
        if not session:
            return None
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        db.flush()
        db.refresh(session)
        return session


def delete_session(session_id: int) -> bool:
    with db_session() as db:
        session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
        if not session:
            return False
        db.delete(session)
        return True


# Stats
def get_attendance_stats(
    student_id: int, year: int, month: int
) -> dict:
    sessions = get_sessions_for_student(student_id, year, month)
    total = len(sessions)
    attended = sum(1 for s in sessions if s.is_attended)
    return {
        "total": total,
        "attended": attended,
        "absent": total - attended,
        "pct": round((attended / total * 100), 1) if total else 0,
    }