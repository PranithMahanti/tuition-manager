"""
ui/schedule_page.py — Manage recurring weekly schedules per student.
"""
import datetime
import streamlit as st
import pandas as pd

from services.student_service import get_all_students
from services.schedule_service import (
    create_schedule, get_schedules_for_student,
    delete_schedule, DAYS,
)
from services.session_service import generate_monthly_sessions


def render():
    st.title("Schedules")

    students = get_all_students()
    if not students:
        st.warning("Add students first before creating schedules.")
        return

    student_options = {f"{s.name} – {s.subject} (ID {s.id})": s for s in students}

    tab_view, tab_add, tab_gen = st.tabs(
        ["View Schedules", "Add Slot", "Generate Monthly Sessions"]
    )

    # VIEW
    with tab_view:
        st.subheader("All Student Schedules")
        all_rows = []
        for s in students:
            for sch in get_schedules_for_student(s.id):
                all_rows.append({
                    "Student": s.name,
                    "Subject": s.subject,
                    "Day": sch.day_name,
                    "Start": sch.start_time.strftime("%I:%M %p") if sch.start_time else "—",
                    "End": sch.end_time.strftime("%I:%M %p") if sch.end_time else "—",
                    "Schedule ID": sch.id,
                })
        if all_rows:
            df = pd.DataFrame(all_rows)
            st.dataframe(df, hide_index=True, use_container_width=True)

            st.subheader("Delete a Schedule Slot")
            del_id = st.number_input("Enter Schedule ID to delete", min_value=1, step=1)
            if st.button("Delete Schedule", type="secondary"):
                if delete_schedule(int(del_id)):
                    st.success(f"Schedule {del_id} deleted.")
                    st.rerun()
                else:
                    st.error("Schedule not found.")
        else:
            st.info("No schedules yet. Add one in the 'Add Slot' tab.")

    # ADD
    with tab_add:
        st.subheader("Add a Weekly Schedule Slot")
        with st.form("add_schedule_form", clear_on_submit=True):
            chosen = st.selectbox("Student", list(student_options.keys()))
            student = student_options[chosen]

            c1, c2, c3 = st.columns(3)
            day_label = c1.selectbox("Day of Week", DAYS)
            start_t = c2.time_input("Start Time", value=datetime.time(16, 0))
            end_t = c3.time_input("End Time", value=datetime.time(17, 0))

            submitted = st.form_submit_button("Add Schedule", use_container_width=True)
            if submitted:
                if start_t >= end_t:
                    st.error("End time must be after start time.")
                else:
                    day_idx = DAYS.index(day_label)
                    sch = create_schedule(
                        student_id=student.id,
                        day_of_week=day_idx,
                        start_time=start_t,
                        end_time=end_t,
                    )
                    st.success(
                        f"Schedule added: **{student.name}** every **{day_label}** "
                        f"{start_t.strftime('%I:%M %p')} – {end_t.strftime('%I:%M %p')}"
                    )
                    st.rerun()

        # Show existing slots for the selected student
        st.markdown("---")
        st.subheader("Existing Slots for Selected Student")
        if "add_schedule_form" in st.session_state:
            pass
        preview_choice = st.selectbox(
            "Preview schedules for:", list(student_options.keys()), key="preview_sel"
        )
        preview_student = student_options[preview_choice]
        slots = get_schedules_for_student(preview_student.id)
        if slots:
            for sl in slots:
                st.markdown(
                    f"- **{sl.day_name}** &nbsp; "
                    f"{sl.start_time.strftime('%I:%M %p')} – {sl.end_time.strftime('%I:%M %p')} "
                    f"&nbsp; *(ID: {sl.id})*"
                )
        else:
            st.info("No slots yet for this student.")

    # GENERATE SESSIONS
    with tab_gen:
        st.subheader("Auto-Generate Monthly Class Sessions")
        st.markdown(
            "This will create class session entries for the selected month "
            "based on the student's weekly schedule. Already-existing sessions "
            "are skipped automatically."
        )

        c1, c2, c3 = st.columns(3)
        gen_mode = c1.radio("Generate for", ["Single Student", "All Students"])
        year = c2.number_input("Year", min_value=2020, max_value=2035,
                               value=datetime.date.today().year)
        month = c3.selectbox(
            "Month",
            list(range(1, 13)),
            index=datetime.date.today().month - 1,
            format_func=lambda m: datetime.date(2000, m, 1).strftime("%B"),
        )

        if gen_mode == "Single Student":
            chosen2 = st.selectbox("Student", list(student_options.keys()), key="gen_sel")
            student2 = student_options[chosen2]

            if st.button("Generate Sessions", type="primary"):
                created, skipped = generate_monthly_sessions(student2.id, int(year), int(month))
                st.success(
                    f"Done! **{created}** session(s) created, "
                    f"**{skipped}** already existed."
                )
        else:
            if st.button("Generate for ALL Students", type="primary"):
                from services.session_service import generate_sessions_for_all_students
                results = generate_sessions_for_all_students(int(year), int(month))
                total_c = sum(r["created"] for r in results.values())
                total_s = sum(r["skipped"] for r in results.values())
                st.success(
                    f"Bulk generation complete! "
                    f"**{total_c}** created, **{total_s}** skipped across {len(results)} student(s)."
                )
                with st.expander("Detailed Results"):
                    for sid, info in results.items():
                        st.write(
                            f"• **{info['name']}**: {info['created']} created, "
                            f"{info['skipped']} skipped"
                        )
