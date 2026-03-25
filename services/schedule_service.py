import datetime
from typing import List, Optional

from database.db import db_session, get_db
from database.models import Schedule


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ── Create ─────────────────────────────────────────────────────────────────────
def create_schedule(
    student_id: int,
    day_of_week: int,
    start_time: datetime.time,
    end_time: datetime.time,
) -> Schedule:
    with db_session() as db:
        schedule = Schedule(
            student_id=student_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
        )
        db.add(schedule)
        db.flush()
        db.refresh(schedule)
        return schedule


# ── Read ───────────────────────────────────────────────────────────────────────
def get_schedules_for_student(student_id: int) -> List[Schedule]:
    db = get_db()
    try:
        return (
            db.query(Schedule)
            .filter(Schedule.student_id == student_id)
            .order_by(Schedule.day_of_week, Schedule.start_time)
            .all()
        )
    finally:
        db.close()


def get_all_schedules() -> List[Schedule]:
    db = get_db()
    try:
        return (
            db.query(Schedule)
            .order_by(Schedule.day_of_week, Schedule.start_time)
            .all()
        )
    finally:
        db.close()


def get_schedules_for_day(day_of_week: int) -> List[Schedule]:
    """Return all schedules that fall on a given weekday (0=Monday)."""
    db = get_db()
    try:
        return (
            db.query(Schedule)
            .filter(Schedule.day_of_week == day_of_week)
            .order_by(Schedule.start_time)
            .all()
        )
    finally:
        db.close()


def get_schedule_by_id(schedule_id: int) -> Optional[Schedule]:
    db = get_db()
    try:
        return db.query(Schedule).filter(Schedule.id == schedule_id).first()
    finally:
        db.close()


# ── Update ─────────────────────────────────────────────────────────────────────
def update_schedule(schedule_id: int, **kwargs) -> Optional[Schedule]:
    with db_session() as db:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return None
        for key, value in kwargs.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        db.flush()
        db.refresh(schedule)
        return schedule


# ── Delete ─────────────────────────────────────────────────────────────────────
def delete_schedule(schedule_id: int) -> bool:
    with db_session() as db:
        schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if not schedule:
            return False
        db.delete(schedule)
        return True


# ── Utilities ──────────────────────────────────────────────────────────────────
def day_name(day_index: int) -> str:
    return DAYS[day_index] if 0 <= day_index <= 6 else "Unknown"
