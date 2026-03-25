import datetime
from typing import List, Optional

from database.db import db_session, get_db
from database.models import Student


# ── Create ─────────────────────────────────────────────────────────────────────
def create_student(
    name: str,
    class_grade: str,
    subject: str,
    parent_name: str = "",
    parent_phone: str = "",
    parent_email: str = "",
    join_date: Optional[datetime.date] = None,
    monthly_class_count: int = 8,
) -> Student:
    with db_session() as db:
        student = Student(
            name=name,
            class_grade=class_grade,
            subject=subject,
            parent_name=parent_name,
            parent_phone=parent_phone,
            parent_email=parent_email,
            join_date=join_date or datetime.date.today(),
            monthly_class_count=monthly_class_count,
            is_active=True,
        )
        db.add(student)
        db.flush()
        db.refresh(student)
        return student


# ── Read ───────────────────────────────────────────────────────────────────────
def get_all_students(active_only: bool = True) -> List[Student]:
    db = get_db()
    try:
        q = db.query(Student)
        if active_only:
            q = q.filter(Student.is_active == True)
        return q.order_by(Student.name).all()
    finally:
        db.close()


def get_student_by_id(student_id: int) -> Optional[Student]:
    db = get_db()
    try:
        return db.query(Student).filter(Student.id == student_id).first()
    finally:
        db.close()


def search_students(query: str) -> List[Student]:
    db = get_db()
    try:
        like = f"%{query}%"
        return (
            db.query(Student)
            .filter(
                Student.is_active == True,
                (Student.name.ilike(like) | Student.subject.ilike(like)),
            )
            .all()
        )
    finally:
        db.close()


# ── Update ─────────────────────────────────────────────────────────────────────
def update_student(student_id: int, **kwargs) -> Optional[Student]:
    with db_session() as db:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return None
        for key, value in kwargs.items():
            if hasattr(student, key):
                setattr(student, key, value)
        db.flush()
        db.refresh(student)
        return student


# ── Deactivate / Delete ────────────────────────────────────────────────────────
def deactivate_student(student_id: int) -> bool:
    with db_session() as db:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False
        student.is_active = False
        return True


def delete_student(student_id: int) -> bool:
    with db_session() as db:
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return False
        db.delete(student)
        return True


# ── Stats ──────────────────────────────────────────────────────────────────────
def get_student_count() -> int:
    db = get_db()
    try:
        return db.query(Student).filter(Student.is_active == True).count()
    finally:
        db.close()
