"""
ui/tests_page.py — Log tests, view results, performance trend charts.
"""
import datetime
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from services.student_service import get_all_students
from services.test_service import (
    create_test, get_tests_for_student, get_test_by_id,
    update_test, delete_test,
    get_test_analytics, get_test_dataframe,
)


def _grade_badge(grade: str) -> str:
    colors = {"A+": "#16A34A", "A": "#22C55E", "B": "#3B82F6",
              "C": "#F59E0B", "D": "#F97316", "F": "#EF4444"}
    bg = colors.get(grade, "#6B7280")
    return f'<span style="background:{bg};color:white;padding:2px 8px;border-radius:12px;font-weight:bold;">{grade}</span>'


def render():
    st.title("Tests & Scores")

    students = get_all_students()
    if not students:
        st.warning("Add students first.")
        return

    student_options = {f"{s.name} – {s.subject} (ID {s.id})": s for s in students}

    tab_log, tab_view, tab_chart = st.tabs(
        ["Log Test", "Test Records", "Performance Charts"]
    )

    # LOG TEST
    with tab_log:
        st.subheader("Log a New Test")
        with st.form("log_test_form", clear_on_submit=True):
            chosen = st.selectbox("Student", list(student_options.keys()))
            student = student_options[chosen]

            c1, c2 = st.columns(2)
            test_name = c1.text_input("Test Name *", placeholder="e.g. Unit Test 1")
            topic = c2.text_input("Topic", placeholder="e.g. Algebra – Linear Equations")
            test_date = c1.date_input("Test Date", value=datetime.date.today())

            c3, c4 = st.columns(2)
            total_marks = c3.number_input("Total Marks *", min_value=1.0, value=100.0, step=1.0)
            marks_scored = c4.number_input("Marks Scored *", min_value=0.0, value=0.0, step=0.5)

            comments = st.text_area("Comments", placeholder="Optional teacher comments on performance")

            submitted = st.form_submit_button("Save Test", use_container_width=True)
            if submitted:
                if not test_name.strip():
                    st.error("Test Name is required.")
                elif marks_scored > total_marks:
                    st.error("Marks scored cannot exceed total marks.")
                else:
                    t = create_test(
                        student_id=student.id,
                        date=test_date,
                        test_name=test_name.strip(),
                        topic=topic.strip(),
                        total_marks=float(total_marks),
                        marks_scored=float(marks_scored),
                        comments=comments.strip(),
                    )
                    pct = t.percentage
                    st.success(
                        f"Test saved for **{student.name}**! "
                        f"Score: {marks_scored}/{total_marks} = **{pct}%** (Grade: {t.grade})"
                    )
                    st.rerun()

    # VIEW RECORDS
    with tab_view:
        st.subheader("Test Records")
        c1, c2 = st.columns([2, 1])
        chosen2 = c1.selectbox("Student", list(student_options.keys()), key="view_t")
        student2 = student_options[chosen2]

        analytics = get_test_analytics(student2.id)
        tests = get_tests_for_student(student2.id)

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tests Taken", analytics["total_tests"])
        m2.metric("Average %", f"{analytics['average_pct']}%")
        m3.metric("Best Score", f"{analytics['highest_pct']}%")
        trend_icon = {"improving": "Improving", "declining": "Declining", "stable": "Stable", "no data": "—"}.get(
            analytics["trend"], "—"
        )
        m4.metric("Trend", f"{trend_icon} {analytics['trend'].title()}")

        if not tests:
            st.info("No tests recorded for this student.")
        else:
            rows = [
                {
                    "ID": t.id,
                    "Date": t.date.strftime("%d %b %Y"),
                    "Test Name": t.test_name,
                    "Topic": t.topic or "—",
                    "Scored": t.marks_scored,
                    "Total": t.total_marks,
                    "%": t.percentage,
                    "Grade": t.grade,
                    "Comments": t.comments or "—",
                }
                for t in tests
            ]
            df = pd.DataFrame(rows)
            st.dataframe(
                df.style.background_gradient(subset=["%"], cmap="RdYlGn", vmin=0, vmax=100),
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("---")
            col_edit, col_del = st.columns(2)
            with col_edit.expander("Edit a Test"):
                edit_id = st.number_input("Test ID to edit", min_value=1, step=1, key="edit_t_id")
                t_obj = get_test_by_id(int(edit_id))
                if t_obj and t_obj.student_id == student2.id:
                    with st.form("edit_test_form"):
                        en = st.text_input("Test Name", value=t_obj.test_name)
                        et = st.text_input("Topic", value=t_obj.topic or "")
                        em = st.number_input("Marks Scored", value=t_obj.marks_scored)
                        ec = st.text_area("Comments", value=t_obj.comments or "")
                        if st.form_submit_button("Save"):
                            update_test(int(edit_id), test_name=en, topic=et,
                                        marks_scored=em, comments=ec)
                            st.success("Updated!")
                            st.rerun()
                elif edit_id:
                    st.warning("Test not found for this student.")

            with col_del.expander("Delete a Test"):
                del_id = st.number_input("Test ID to delete", min_value=1, step=1, key="del_t_id")
                if st.button("Delete Test", type="secondary", key="del_t_btn"):
                    if delete_test(int(del_id)):
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.error("Not found.")

    # CHARTS
    with tab_chart:
        st.subheader("Performance Charts")
        chosen3 = st.selectbox("Student", list(student_options.keys()), key="chart_t")
        student3 = student_options[chosen3]

        df = get_test_dataframe(student3.id)
        if df.empty:
            st.info("No test data to chart.")
        else:
            c_left, c_right = st.columns(2)

            with c_left:
                st.markdown("#### Score Trend Over Time")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["date"], y=df["percentage"],
                    mode="lines+markers+text",
                    text=[f"{p}%" for p in df["percentage"]],
                    textposition="top center",
                    line=dict(color="#6366F1", width=2.5),
                    marker=dict(size=9, color="#6366F1"),
                    name="Score %",
                ))
                # Add reference lines
                fig.add_hline(y=75, line_dash="dot", line_color="#16A34A",
                              annotation_text="Pass (75%)")
                if len(df) > 1:
                    avg_pct = df["percentage"].mean()
                    fig.add_hline(y=avg_pct, line_dash="dash", line_color="#F59E0B",
                                  annotation_text=f"Avg ({avg_pct:.1f}%)")
                fig.update_layout(
                    xaxis_title="Date", yaxis_title="Score (%)",
                    yaxis_range=[0, 105],
                    height=320,
                    margin=dict(t=20, b=40, l=40, r=20),
                    plot_bgcolor="white",
                )
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
                st.plotly_chart(fig, use_container_width=True)

            with c_right:
                st.markdown("#### Score by Test")
                fig2 = px.bar(
                    df,
                    x="test_name", y="percentage",
                    color="percentage",
                    color_continuous_scale="RdYlGn",
                    range_color=[0, 100],
                    text=[f"{p}%" for p in df["percentage"]],
                    labels={"test_name": "Test", "percentage": "%"},
                )
                fig2.update_traces(textposition="outside")
                fig2.update_layout(
                    showlegend=False,
                    height=320,
                    margin=dict(t=20, b=60, l=40, r=20),
                    plot_bgcolor="white",
                    coloraxis_showscale=False,
                )
                fig2.update_xaxes(tickangle=-30)
                st.plotly_chart(fig2, use_container_width=True)

            # Topic-wise breakdown if multiple topics
            if df["topic"].nunique() > 1:
                st.markdown("#### Average Score by Topic")
                topic_df = df.groupby("topic")["percentage"].mean().reset_index()
                topic_df.columns = ["Topic", "Avg %"]
                topic_df = topic_df.sort_values("Avg %", ascending=True)
                fig3 = px.bar(
                    topic_df, x="Avg %", y="Topic", orientation="h",
                    color="Avg %", color_continuous_scale="Blues",
                    text=[f"{v:.1f}%" for v in topic_df["Avg %"]],
                )
                fig3.update_traces(textposition="outside")
                fig3.update_layout(
                    coloraxis_showscale=False,
                    height=max(200, 40 * len(topic_df)),
                    margin=dict(t=10, b=30, l=10, r=40),
                    plot_bgcolor="white",
                )
                st.plotly_chart(fig3, use_container_width=True)
