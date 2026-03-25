"""
ui/reports_page.py — Generate PDF monthly reports and download them.
"""
import datetime
import os
import streamlit as st

from services.student_service import get_all_students
from services.report_service import generate_monthly_report, list_generated_reports
from services.session_service import get_attendance_stats
from services.test_service import get_monthly_test_summary


MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def render():
    st.title("Monthly Reports")

    students = get_all_students()
    if not students:
        st.warning("Add students first.")
        return

    student_options = {f"{s.name} – {s.subject} (ID {s.id})": s for s in students}

    tab_gen, tab_prev, tab_hist = st.tabs(
        ["Generate Report", "Preview Data", "Report History"]
    )

    # GENERATE
    with tab_gen:
        st.subheader("Generate Monthly PDF Report")

        c1, c2, c3 = st.columns([2, 1, 1])
        chosen = c1.selectbox("Student", list(student_options.keys()))
        student = student_options[chosen]

        today = datetime.date.today()
        year = c2.number_input("Year", min_value=2020, max_value=2035,
                               value=today.year, step=1)
        month = c3.selectbox(
            "Month", list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda m: MONTH_NAMES[m],
        )

        teacher_comments = st.text_area(
            "Teacher's Comments (will be included in the PDF)",
            placeholder=(
                "e.g. Rahul has shown great improvement in algebra this month. "
                "I recommend focusing on geometry in the coming weeks."
            ),
            height=120,
        )

        st.markdown("---")

        # Quick preview stats
        att = get_attendance_stats(student.id, int(year), int(month))
        ts = get_monthly_test_summary(student.id, int(year), int(month))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Classes Held", att["total"])
        m2.metric("Attended", att["attended"])
        m3.metric("Tests Recorded", ts["count"])
        m4.metric("Avg Test Score", f"{ts['avg_pct']}%")

        if att["total"] == 0 and ts["count"] == 0:
            st.warning(
                f"No sessions or tests found for "
                f"{MONTH_NAMES[int(month)]} {int(year)}. "
                "The report will be generated but will have minimal data."
            )

        if st.button("Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Building PDF report…"):
                path = generate_monthly_report(
                    student_id=student.id,
                    year=int(year),
                    month=int(month),
                    teacher_comments=teacher_comments,
                )
            if path:
                st.success(f"Report generated: `{os.path.basename(path)}`")
                with open(path, "rb") as f:
                    st.download_button(
                        label="⬇Download PDF",
                        data=f,
                        file_name=os.path.basename(path),
                        mime="application/pdf",
                        use_container_width=True,
                    )
            else:
                st.error("Failed to generate report. Check logs.")

    # PREVIEW DATA
    with tab_prev:
        st.subheader("Preview Report Data")
        c1, c2, c3 = st.columns([2, 1, 1])
        chosen2 = c1.selectbox("Student", list(student_options.keys()), key="prev_s")
        student2 = student_options[chosen2]
        year2 = c2.number_input("Year", min_value=2020, max_value=2035,
                                value=datetime.date.today().year, key="prev_y")
        month2 = c3.selectbox(
            "Month", list(range(1, 13)),
            index=datetime.date.today().month - 1,
            key="prev_m",
            format_func=lambda m: MONTH_NAMES[m],
        )

        from services.lesson_service import get_lesson_log
        import pandas as pd

        lessons = get_lesson_log(student2.id, int(year2), int(month2))
        ts2 = get_monthly_test_summary(student2.id, int(year2), int(month2))
        att2 = get_attendance_stats(student2.id, int(year2), int(month2))

        st.markdown(
            f"#### {student2.name} — {MONTH_NAMES[int(month2)]} {int(year2)}"
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Attendance**")
            st.write(
                f"- Total sessions: **{att2['total']}**\n"
                f"- Attended: **{att2['attended']}**\n"
                f"- Absent: **{att2['absent']}**\n"
                f"- Attendance %: **{att2['pct']}%**"
            )

        with col_b:
            st.markdown("**Test Summary**")
            st.write(
                f"- Tests conducted: **{ts2['count']}**\n"
                f"- Average score: **{ts2['avg_pct']}%**"
            )

        if lessons:
            st.markdown("**Lesson Log**")
            st.dataframe(pd.DataFrame(lessons), hide_index=True, use_container_width=True)
        else:
            st.info("No lesson logs for this period.")

        if ts2["tests"]:
            st.markdown("**Test Results**")
            st.dataframe(pd.DataFrame(ts2["tests"]), hide_index=True, use_container_width=True)

    # ── HISTORY ───────────────────────────────────────────────────────────────
    with tab_hist:
        st.subheader("Generated Reports")
        reports = list_generated_reports()
        if not reports:
            st.info("No reports generated yet.")
        else:
            for r in reports:
                col1, col2, col3, col4 = st.columns([3, 1.5, 1, 1])
                col1.markdown(f"**{r['filename']}**")
                col2.caption(r["modified"])
                col3.caption(f"{r['size_kb']} KB")
                with open(r["path"], "rb") as f:
                    col4.download_button(
                        "⬇:DOWNLOAD",
                        data=f,
                        file_name=r["filename"],
                        mime="application/pdf",
                        key=f"dl_{r['filename']}",
                    )
            st.caption(f"{len(reports)} report(s) on disk.")
