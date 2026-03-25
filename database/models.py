from sqlalchemy import (
    Column, Integer, String, Date, Time, Float,
    ForeignKey, Text, Boolean, DateTime
)
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    class_grade = Column(String(20), nullable=False)
    subject = Column(String(50), nullable=False)
    parent_name = Column(String(100))
    parent_phone = Column(String(20))
    parent_email = Column(String(100))
    join_date = Column(Date, default=datetime.date.today)
    monthly_class_count = Column(Integer, default=8)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    schedules = relationship(
        "Schedule", back_populates="student", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "ClassSession", back_populates="student", cascade="all, delete-orphan"
    )
    tests = relationship(
        "Test", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}', subject='{self.subject}')>"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday … 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    student = relationship("Student", back_populates="schedules", lazy="joined")

    @property
    def day_name(self):
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else "Unknown"

    def __repr__(self):
        return (
            f"<Schedule(student_id={self.student_id}, "
            f"day='{self.day_name}', start='{self.start_time}')>"
        )


class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    session_date = Column(Date, nullable=False)
    start_time = Column(Time)
    end_time = Column(Time)
    topic_taught = Column(Text, default="")
    homework = Column(Text, default="")
    remarks = Column(Text, default="")
    is_attended = Column(Boolean, default=True)
    is_generated = Column(Boolean, default=True)  # True = auto-generated

    student = relationship("Student", back_populates="sessions", lazy="joined")

    def __repr__(self):
        return (
            f"<ClassSession(student_id={self.student_id}, "
            f"date='{self.session_date}', attended={self.is_attended})>"
        )


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    date = Column(Date, nullable=False)
    test_name = Column(String(100), nullable=False)
    topic = Column(String(200))
    total_marks = Column(Float, nullable=False)
    marks_scored = Column(Float, nullable=False)
    comments = Column(Text, default="")

    student = relationship("Student", back_populates="tests", lazy="joined")

    @property
    def percentage(self) -> float:
        if self.total_marks and self.total_marks > 0:
            return round((self.marks_scored / self.total_marks) * 100, 2)
        return 0.0

    @property
    def grade(self) -> str:
        pct = self.percentage
        if pct >= 90:
            return "A+"
        elif pct >= 80:
            return "A"
        elif pct >= 70:
            return "B"
        elif pct >= 60:
            return "C"
        elif pct >= 50:
            return "D"
        else:
            return "F"

    def __repr__(self):
        return (
            f"<Test(student_id={self.student_id}, "
            f"name='{self.test_name}', pct={self.percentage}%)>"
        )