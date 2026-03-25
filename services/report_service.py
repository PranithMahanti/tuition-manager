"""
report_service.py
-----------------
Aggregates data from all services into a single report payload,
then delegates PDF creation to utils/report_utils.py.
"""
import os
import datetime
from typing import Optional

from services.student_service import get_student_by_id
from services.session_service import get_attendance_stats, get_sessions_for_student
from services.lesson_service import get_lesson_log
from services.test_service import get_monthly_test_summary, get_test_analytics
from utils.report_utils import build_pdf_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def generate_monthly_report(
    student_id: int,
    year: int,
    month: int,
    teacher_comments: str = "",
) -> Optional[str]:
    """
    Build a full monthly report for a student and write a PDF.
    Returns the absolute path to the generated PDF, or None on failure.
    """
    student = get_student_by_id(student_id)
    if not student:
        return None

    month_name = MONTH_NAMES[month]
    attendance = get_attendance_stats(student_id, year, month)
    lesson_log = get_lesson_log(student_id, year, month)
    test_summary = get_monthly_test_summary(student_id, year, month)
    analytics = get_test_analytics(student_id)

    # Derive performance summary string
    avg = test_summary["avg_pct"]
    if avg >= 85:
        performance_summary = "Excellent performance this month. Keep it up!"
    elif avg >= 70:
        performance_summary = "Good performance. A little more focus will make it great."
    elif avg >= 55:
        performance_summary = "Satisfactory performance. Consistent revision is recommended."
    elif avg > 0:
        performance_summary = "Needs improvement. Please revisit core concepts and practice regularly."
    else:
        performance_summary = "No test data available for this month."

    payload = {
        "student": {
            "name": student.name,
            "class_grade": student.class_grade,
            "subject": student.subject,
            "parent_name": student.parent_name,
            "parent_phone": student.parent_phone,
            "parent_email": student.parent_email,
        },
        "period": {"month": month_name, "year": year},
        "attendance": attendance,
        "lesson_log": lesson_log,
        "test_summary": test_summary,
        "analytics": analytics,
        "performance_summary": performance_summary,
        "teacher_comments": teacher_comments.strip() or "No additional comments.",
        "generated_on": datetime.date.today().strftime("%d %B %Y"),
    }

    # Safe filename: "Rahul_March_2026_Report.pdf"
    safe_name = student.name.replace(" ", "_")
    filename = f"{safe_name}_{month_name}_{year}_Report.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    build_pdf_report(payload, filepath)
    return filepath


def list_generated_reports() -> list:
    """Return a sorted list of all PDFs in the reports folder."""
    files = []
    for f in os.listdir(REPORTS_DIR):
        if f.endswith(".pdf"):
            full = os.path.join(REPORTS_DIR, f)
            files.append(
                {
                    "filename": f,
                    "path": full,
                    "size_kb": round(os.path.getsize(full) / 1024, 1),
                    "modified": datetime.datetime.fromtimestamp(
                        os.path.getmtime(full)
                    ).strftime("%d %b %Y %H:%M"),
                }
            )
    return sorted(files, key=lambda x: x["modified"], reverse=True)
