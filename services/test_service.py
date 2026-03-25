import datetime
import calendar
from typing import List, Optional

import pandas as pd

from database.db import db_session, get_db
from sqlalchemy.orm import joinedload
from database.models import Test


# ── Create ─────────────────────────────────────────────────────────────────────
def create_test(
    student_id: int,
    date: datetime.date,
    test_name: str,
    topic: str,
    total_marks: float,
    marks_scored: float,
    comments: str = "",
) -> Test:
    with db_session() as db:
        test = Test(
            student_id=student_id,
            date=date,
            test_name=test_name,
            topic=topic,
            total_marks=total_marks,
            marks_scored=marks_scored,
            comments=comments,
        )
        db.add(test)
        db.flush()
        db.refresh(test)
        return test


# ── Read ───────────────────────────────────────────────────────────────────────
def get_tests_for_student(
    student_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Test]:
    db = get_db()
    try:
        q = db.query(Test).filter(Test.student_id == student_id)
        if year and month:
            _, dim = calendar.monthrange(year, month)
            q = q.filter(
                Test.date >= datetime.date(year, month, 1),
                Test.date <= datetime.date(year, month, dim),
            )
        return q.order_by(Test.date).all()
    finally:
        db.close()


def get_all_tests(limit: int = 50) -> List[Test]:
    db = get_db()
    try:
        return (
            db.query(Test).options(joinedload(Test.student)).order_by(Test.date.desc()).limit(limit).all()
        )
    finally:
        db.close()


def get_test_by_id(test_id: int) -> Optional[Test]:
    db = get_db()
    try:
        return db.query(Test).filter(Test.id == test_id).first()
    finally:
        db.close()


# ── Update / Delete ────────────────────────────────────────────────────────────
def update_test(test_id: int, **kwargs) -> Optional[Test]:
    with db_session() as db:
        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            return None
        for key, value in kwargs.items():
            if hasattr(test, key):
                setattr(test, key, value)
        db.flush()
        db.refresh(test)
        return test


def delete_test(test_id: int) -> bool:
    with db_session() as db:
        test = db.query(Test).filter(Test.id == test_id).first()
        if not test:
            return False
        db.delete(test)
        return True


# ── Analytics ──────────────────────────────────────────────────────────────────
def get_test_analytics(student_id: int) -> dict:
    """Return summary analytics for a student across all tests."""
    tests = get_tests_for_student(student_id)
    if not tests:
        return {
            "total_tests": 0,
            "average_pct": 0.0,
            "highest_pct": 0.0,
            "lowest_pct": 0.0,
            "trend": "no data",
        }

    percentages = [t.percentage for t in tests]
    avg = round(sum(percentages) / len(percentages), 2)

    trend = "stable"
    if len(percentages) >= 3:
        recent = percentages[-3:]
        if recent[-1] > recent[0]:
            trend = "improving"
        elif recent[-1] < recent[0]:
            trend = "declining"

    return {
        "total_tests": len(tests),
        "average_pct": avg,
        "highest_pct": max(percentages),
        "lowest_pct": min(percentages),
        "trend": trend,
    }


def get_test_dataframe(student_id: int) -> pd.DataFrame:
    """Return test data as a Pandas DataFrame for charting."""
    tests = get_tests_for_student(student_id)
    if not tests:
        return pd.DataFrame(
            columns=["date", "test_name", "topic", "marks_scored", "total_marks", "percentage", "grade"]
        )
    rows = [
        {
            "date": t.date,
            "test_name": t.test_name,
            "topic": t.topic,
            "marks_scored": t.marks_scored,
            "total_marks": t.total_marks,
            "percentage": t.percentage,
            "grade": t.grade,
            "comments": t.comments,
        }
        for t in tests
    ]
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")


def get_monthly_test_summary(student_id: int, year: int, month: int) -> dict:
    tests = get_tests_for_student(student_id, year, month)
    if not tests:
        return {"count": 0, "avg_pct": 0.0, "tests": []}

    percentages = [t.percentage for t in tests]
    return {
        "count": len(tests),
        "avg_pct": round(sum(percentages) / len(percentages), 2),
        "tests": [
            {
                "date": t.date.strftime("%d %b"),
                "name": t.test_name,
                "topic": t.topic or "—",
                "scored": t.marks_scored,
                "total": t.total_marks,
                "pct": t.percentage,
                "grade": t.grade,
                "comments": t.comments or "—",
            }
            for t in tests
        ],
    }