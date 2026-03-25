"""
ui/dashboard.py — Today's overview, upcoming classes, recent tests, alerts.
"""
import datetime
import streamlit as st
import plotly.graph_objects as go

from services.student_service import get_all_students, get_student_count
from services.session_service import get_sessions_for_date, get_upcoming_sessions
from services.test_service import get_all_tests
from services.schedule_service import day_name


def render():
    today = datetime.date.today()

    st.title("📊 Dashboard")
    st.caption(f"Today is **{today.strftime('%A, %d %B %Y')}**")

    # ── Top KPI cards ──────────────────────────────────────────────────────────
    students = get_all_students()
    todays_sessions = get_sessions_for_date(today)
    upcoming = get_upcoming_sessions(days_ahead=7)
    recent_tests = get_all_tests(limit=20)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👨‍🎓 Active Students", len(students))
    k2.metric("📅 Classes Today", len(todays_sessions))
    k3.metric("🔮 Upcoming (7d)", len(upcoming))
    k4.metric("📝 Total Tests Logged", len(recent_tests))

    st.divider()

    # ── Today's Classes ────────────────────────────────────────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🗓️ Today's Classes")
        if todays_sessions:
            for s in todays_sessions:
                time_str = (
                    f"{s.start_time.strftime('%I:%M %p')} – {s.end_time.strftime('%I:%M %p')}"
                    if s.start_time and s.end_time
                    else "Time not set"
                )
                status = "✅" if s.is_attended else "❌"
                logged = "📝" if s.topic_taught else "⏳"
                st.markdown(
                    f"""<div style='padding:10px;border-left:4px solid #6366F1;
                    background:#EEF2FF;border-radius:6px;margin-bottom:8px'>
                    <b>{status} {s.student.name}</b> — {s.student.subject}<br>
                    <small>🕐 {time_str} &nbsp; {logged} {'Logged' if s.topic_taught else 'Not logged yet'}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No classes scheduled for today.")

    with col_right:
        st.subheader("🔮 Upcoming Classes")
        if upcoming:
            for s in upcoming[:8]:
                days_away = (s.session_date - today).days
                label = (
                    "Tomorrow" if days_away == 1 else f"In {days_away} days"
                )
                time_str = (
                    s.start_time.strftime("%I:%M %p") if s.start_time else "--"
                )
                st.markdown(
                    f"""<div style='padding:8px;border-left:4px solid #10B981;
                    background:#ECFDF5;border-radius:6px;margin-bottom:6px'>
                    <b>{s.student.name}</b> — {s.student.subject}<br>
                    <small>📅 {s.session_date.strftime('%d %b')} ({label}) &nbsp; 🕐 {time_str}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No upcoming classes in the next 7 days.")

    st.divider()

    # ── Recent Tests & Performance Chart ──────────────────────────────────────
    col_a, col_b = st.columns([1.2, 0.8])

    with col_a:
        st.subheader("📝 Recent Test Scores")
        if recent_tests:
            rows = []
            for t in recent_tests[:10]:
                rows.append({
                    "Student": t.student.name,
                    "Test": t.test_name,
                    "Date": t.date.strftime("%d %b"),
                    "Score": f"{t.marks_scored}/{t.total_marks}",
                    "%": f"{t.percentage}%",
                    "Grade": t.grade,
                })
            import pandas as pd
            df = pd.DataFrame(rows)

            def grade_color(val):
                if val in ("A+", "A"):
                    return "background-color:#DCFCE7"
                elif val == "B":
                    return "background-color:#FEF9C3"
                elif val in ("C", "D"):
                    return "background-color:#FFEDD5"
                else:
                    return "background-color:#FEE2E2"

            st.dataframe(
                df.style.applymap(grade_color, subset=["Grade"]),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No tests recorded yet.")

    with col_b:
        st.subheader("📈 Score Distribution")
        if recent_tests:
            buckets = {"A+ (≥90)": 0, "A (80-89)": 0, "B (70-79)": 0,
                       "C (60-69)": 0, "D (50-59)": 0, "F (<50)": 0}
            for t in recent_tests:
                p = t.percentage
                if p >= 90:   buckets["A+ (≥90)"] += 1
                elif p >= 80: buckets["A (80-89)"] += 1
                elif p >= 70: buckets["B (70-79)"] += 1
                elif p >= 60: buckets["C (60-69)"] += 1
                elif p >= 50: buckets["D (50-59)"] += 1
                else:         buckets["F (<50)"] += 1

            fig = go.Figure(go.Pie(
                labels=list(buckets.keys()),
                values=list(buckets.values()),
                hole=0.45,
                marker_colors=["#16A34A", "#22D3EE", "#6366F1",
                                "#FBBF24", "#F97316", "#EF4444"],
            ))
            fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                showlegend=True,
                legend=dict(font_size=10),
                height=280,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Score chart will appear once tests are logged.")

    st.divider()

    # ── Alerts ─────────────────────────────────────────────────────────────────
    st.subheader("⚠️ Alerts & Reminders")
    alerts = []

    # Students with unlogged sessions
    from services.lesson_service import get_unlogged_sessions
    for student in students:
        unlogged = get_unlogged_sessions(student.id)
        if unlogged:
            alerts.append(
                f"**{student.name}** has {len(unlogged)} past session(s) with no topic logged."
            )

    if alerts:
        for a in alerts:
            st.warning(a)
    else:
        st.success("All caught up! No pending alerts.")
