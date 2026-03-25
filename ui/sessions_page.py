"""
ui/sessions_page.py — View sessions, log lesson content, mark attendance.
"""
import datetime
import streamlit as st
import pandas as pd

from services.student_service import get_all_students
from services.session_service import (
    get_sessions_for_student, get_session_by_id,
    create_session, delete_session,
)
from services.lesson_service import log_lesson, get_unlogged_sessions


def render():
    st.title("Sessions & Lesson Log")

    students = get_all_students()
    if not students:
        st.warning("Add students first.")
        return

    student_options = {f"{s.name} – {s.subject} (ID {s.id})": s for s in students}

    tab_view, tab_log, tab_add = st.tabs(
        ["View Sessions", "Log Lesson", "Manual Session"]
    )

    # VIEW
    with tab_view:
        st.subheader("Session History")
        c1, c2, c3 = st.columns([2, 1, 1])
        chosen = c1.selectbox("Student", list(student_options.keys()), key="view_sel")
        student = student_options[chosen]

        today = datetime.date.today()
        year = c2.number_input("Year", min_value=2020, max_value=2035,
                               value=today.year, key="view_year")
        month = c3.selectbox(
            "Month", list(range(1, 13)),
            index=today.month - 1, key="view_month",
            format_func=lambda m: datetime.date(2000, m, 1).strftime("%B"),
        )

        sessions = get_sessions_for_student(student.id, int(year), int(month))
        attended = sum(1 for s in sessions if s.is_attended)
        logged = sum(1 for s in sessions if s.topic_taught)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Sessions", len(sessions))
        m2.metric("Attended", attended)
        m3.metric("Absent", len(sessions) - attended)
        m4.metric("Lessons Logged", logged)

        if sessions:
            rows = [
                {
                    "ID": s.id,
                    "Date": s.session_date.strftime("%d %b %Y (%a)"),
                    "Time": (
                        f"{s.start_time.strftime('%I:%M %p')}"
                        if s.start_time else "—"
                    ),
                    "Attended": "Attended" if s.is_attended else "Nope.",
                    "Topic": s.topic_taught or "—",
                    "Homework": s.homework or "—",
                    "Remarks": s.remarks or "—",
                }
                for s in sessions
            ]
            df = pd.DataFrame(rows)
            st.dataframe(df, hide_index=True, use_container_width=True)

            with st.expander("Delete a Session"):
                del_id = st.number_input("Session ID to delete", min_value=1, step=1, key="del_s")
                if st.button("Delete Session", type="secondary", key="del_s_btn"):
                    if delete_session(int(del_id)):
                        st.success("Session deleted.")
                        st.rerun()
                    else:
                        st.error("Session not found.")
        else:
            st.info(
                f"No sessions found for "
                f"{datetime.date(int(year), int(month), 1).strftime('%B %Y')}. "
                "Generate sessions from the Schedule page."
            )

    # LOG LESSON
    with tab_log:
        st.subheader("Log Lesson Content into a Session")

        c1, c2 = st.columns([2, 2])
        chosen2 = c1.selectbox("Student", list(student_options.keys()), key="log_sel")
        student2 = student_options[chosen2]

        unlogged = get_unlogged_sessions(student2.id)
        all_sessions = get_sessions_for_student(student2.id)

        mode = c2.radio("Session picker", ["From unlogged sessions", "All sessions"], horizontal=True)
        pool = unlogged if mode == "From unlogged sessions" else all_sessions

        if not pool:
            st.info("No sessions available to log." if mode == "All sessions"
                    else "All sessions are already logged!")
        else:
            sess_opts = {
                f"[{s.id}] {s.session_date.strftime('%d %b %Y')} "
                f"{'– ' + s.topic_taught[:30] if s.topic_taught else '(not logged)'}": s
                for s in reversed(pool)
            }
            chosen_sess_label = st.selectbox("Select Session", list(sess_opts.keys()))
            sess = sess_opts[chosen_sess_label]

            with st.form("log_lesson_form"):
                st.markdown(
                    f"**Session:** {sess.session_date.strftime('%d %B %Y (%A)')} &nbsp; "
                    f"Student: **{student2.name}**"
                )
                attended = st.checkbox("Student attended this class", value=sess.is_attended)
                topic = st.text_area(
                    "Topic Taught *",
                    value=sess.topic_taught or "",
                    placeholder="e.g. Quadratic Equations – Factoring method",
                    height=80,
                )
                homework = st.text_area(
                    "Homework Assigned",
                    value=sess.homework or "",
                    placeholder="e.g. Exercise 5.3 Q1–Q10",
                    height=60,
                )
                remarks = st.text_area(
                    "Teacher Remarks",
                    value=sess.remarks or "",
                    placeholder="e.g. Student struggled with sign changes. Needs extra practice.",
                    height=60,
                )
                submitted = st.form_submit_button("Save Lesson Log", use_container_width=True)
                if submitted:
                    if not topic.strip():
                        st.error("Topic Taught is required.")
                    else:
                        log_lesson(
                            session_id=sess.id,
                            topic_taught=topic,
                            homework=homework,
                            remarks=remarks,
                            is_attended=attended,
                        )
                        st.success("Lesson log saved!")
                        st.rerun()

    # MANUAL SESSION
    with tab_add:
        st.subheader("Add a Manual (Ad-hoc) Session")
        st.caption("Use this for makeup classes or sessions outside the regular schedule.")

        with st.form("manual_session_form", clear_on_submit=True):
            chosen3 = st.selectbox("Student", list(student_options.keys()), key="man_sel")
            student3 = student_options[chosen3]

            c1, c2, c3 = st.columns(3)
            sess_date = c1.date_input("Session Date", value=datetime.date.today())
            start_t = c2.time_input("Start Time", value=datetime.time(16, 0))
            end_t = c3.time_input("End Time", value=datetime.time(17, 0))

            topic = st.text_area("Topic Taught", placeholder="Optional — can log later")
            homework = st.text_area("Homework Assigned", placeholder="Optional")
            remarks = st.text_area("Remarks", placeholder="Optional")
            attended = st.checkbox("Student attended", value=True)

            if st.form_submit_button("Add Session", use_container_width=True):
                create_session(
                    student_id=student3.id,
                    session_date=sess_date,
                    start_time=start_t,
                    end_time=end_t,
                    topic_taught=topic,
                    homework=homework,
                    remarks=remarks,
                    is_attended=attended,
                )
                st.success(
                    f"Manual session added for **{student3.name}** on "
                    f"{sess_date.strftime('%d %b %Y')}."
                )
                st.rerun()
