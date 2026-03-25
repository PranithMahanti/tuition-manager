"""
ui/students_page.py — Add, view, edit, deactivate students.
"""
import datetime
import streamlit as st
import pandas as pd

from services.student_service import (
    get_all_students, get_student_by_id, create_student,
    update_student, deactivate_student,
)


def render():
    st.title("👨‍🎓 Students")

    tab_list, tab_add, tab_edit = st.tabs(["📋 All Students", "➕ Add Student", "✏️ Edit / Deactivate"])

    # ── LIST ───────────────────────────────────────────────────────────────────
    with tab_list:
        students = get_all_students(active_only=False)
        if not students:
            st.info("No students yet. Use the '➕ Add Student' tab to get started.")
        else:
            rows = [
                {
                    "ID": s.id,
                    "Name": s.name,
                    "Grade": s.class_grade,
                    "Subject": s.subject,
                    "Parent": s.parent_name or "—",
                    "Phone": s.parent_phone or "—",
                    "Joined": s.join_date.strftime("%d %b %Y") if s.join_date else "—",
                    "Classes/Mo": s.monthly_class_count,
                    "Active": "✅" if s.is_active else "❌",
                }
                for s in students
            ]
            df = pd.DataFrame(rows)

            search = st.text_input("🔍 Search by name or subject", "")
            if search:
                mask = df["Name"].str.contains(search, case=False) | \
                       df["Subject"].str.contains(search, case=False)
                df = df[mask]

            st.dataframe(df, hide_index=True, use_container_width=True)
            st.caption(f"Showing {len(df)} student(s).")

    # ── ADD ────────────────────────────────────────────────────────────────────
    with tab_add:
        st.subheader("Add New Student")
        with st.form("add_student_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            name = c1.text_input("Student Name *", placeholder="e.g. Rahul Sharma")
            subject = c2.text_input("Subject *", placeholder="e.g. Mathematics")
            grade = c1.text_input("Class / Grade *", placeholder="e.g. Grade 10")
            monthly = c2.number_input("Classes per Month", min_value=1, max_value=31, value=8)
            join_date = st.date_input("Join Date", value=datetime.date.today())

            st.markdown("**Parent / Guardian Details**")
            p1, p2, p3 = st.columns(3)
            parent_name = p1.text_input("Parent Name")
            parent_phone = p2.text_input("Phone Number")
            parent_email = p3.text_input("Email Address")

            submitted = st.form_submit_button("✅ Add Student", use_container_width=True)
            if submitted:
                if not name.strip() or not subject.strip() or not grade.strip():
                    st.error("Name, Subject, and Grade are required.")
                else:
                    s = create_student(
                        name=name.strip(),
                        class_grade=grade.strip(),
                        subject=subject.strip(),
                        parent_name=parent_name.strip(),
                        parent_phone=parent_phone.strip(),
                        parent_email=parent_email.strip(),
                        join_date=join_date,
                        monthly_class_count=int(monthly),
                    )
                    st.success(f"✅ Student **{s.name}** added successfully (ID: {s.id})!")
                    st.rerun()

    # ── EDIT / DEACTIVATE ──────────────────────────────────────────────────────
    with tab_edit:
        st.subheader("Edit or Deactivate a Student")
        all_students = get_all_students(active_only=False)
        if not all_students:
            st.info("No students found. Add one in the '➕ Add Student' tab.")
        else:
            options = {f"{s.name} (ID {s.id}) – {s.subject}": s.id for s in all_students}
            chosen_label = st.selectbox("Select Student", list(options.keys()))
            sid = options[chosen_label]
            student = get_student_by_id(sid)

            if student:
                with st.form("edit_student_form"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Name", value=student.name)
                    subject = c2.text_input("Subject", value=student.subject)
                    grade = c1.text_input("Grade", value=student.class_grade)
                    monthly = c2.number_input(
                        "Classes/Month", min_value=1, max_value=31,
                        value=student.monthly_class_count,
                    )
                    p1, p2, p3 = st.columns(3)
                    parent_name = p1.text_input("Parent Name", value=student.parent_name or "")
                    parent_phone = p2.text_input("Phone", value=student.parent_phone or "")
                    parent_email = p3.text_input("Email", value=student.parent_email or "")

                    save, deact = st.columns(2)
                    save_btn = save.form_submit_button("💾 Save Changes", use_container_width=True)
                    deact_btn = deact.form_submit_button(
                        "🚫 Deactivate Student",
                        use_container_width=True,
                        type="secondary",
                    )

                    if save_btn:
                        update_student(
                            sid,
                            name=name.strip(),
                            class_grade=grade.strip(),
                            subject=subject.strip(),
                            parent_name=parent_name.strip(),
                            parent_phone=parent_phone.strip(),
                            parent_email=parent_email.strip(),
                            monthly_class_count=int(monthly),
                        )
                        st.success("✅ Student updated!")
                        st.rerun()

                    if deact_btn:
                        deactivate_student(sid)
                        st.warning(f"Student **{student.name}** has been deactivated.")
                        st.rerun()