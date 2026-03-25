"""
All ReportLab PDF construction lives here.
Receives a structured payload dict from report_service and writes a polished PDF.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Palette
INDIGO       = colors.HexColor("#3730A3")
INDIGO_LIGHT = colors.HexColor("#EEF2FF")
INDIGO_MID   = colors.HexColor("#6366F1")
SLATE        = colors.HexColor("#334155")
SLATE_LIGHT  = colors.HexColor("#F8FAFC")
GREEN        = colors.HexColor("#16A34A")
AMBER        = colors.HexColor("#D97706")
RED          = colors.HexColor("#DC2626")
WHITE        = colors.white
BORDER       = colors.HexColor("#CBD5E1")

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "title": ParagraphStyle(
            "rpt_title", parent=base["Heading1"],
            fontSize=22, textColor=INDIGO, spaceAfter=4,
            alignment=TA_CENTER, fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "rpt_subtitle", parent=base["Normal"],
            fontSize=11, textColor=SLATE, spaceAfter=2,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "rpt_section", parent=base["Heading2"],
            fontSize=13, textColor=INDIGO, spaceBefore=14, spaceAfter=6,
            fontName="Helvetica-Bold", borderPad=2,
        ),
        "body": ParagraphStyle(
            "rpt_body", parent=base["Normal"],
            fontSize=10, textColor=SLATE, leading=14,
        ),
        "small": ParagraphStyle(
            "rpt_small", parent=base["Normal"],
            fontSize=9, textColor=SLATE, leading=12,
        ),
        "highlight": ParagraphStyle(
            "rpt_highlight", parent=base["Normal"],
            fontSize=10, textColor=INDIGO, fontName="Helvetica-Bold",
        ),
        "footer": ParagraphStyle(
            "rpt_footer", parent=base["Normal"],
            fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
        ),
    }
    return custom


def _stat_table(stats: list) -> Table:
    """Render a row of (label, value) stat cards."""
    col_w = (PAGE_W - 2 * MARGIN) / len(stats)
    data = [[Paragraph(f"<b>{v}</b>", ParagraphStyle("sv", fontSize=18, textColor=INDIGO,
             fontName="Helvetica-Bold", alignment=TA_CENTER))
             for _, v in stats],
            [Paragraph(lbl, ParagraphStyle("sl", fontSize=8, textColor=SLATE,
             alignment=TA_CENTER)) for lbl, _ in stats]]
    tbl = Table(data, colWidths=[col_w] * len(stats), rowHeights=[30, 18])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INDIGO_LIGHT),
        ("ROUNDEDCORNERS", [6]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 1), 4),
    ]))
    return tbl


def _section_header(title: str, sty) -> list:
    return [
        Paragraph(title, sty["section"]),
        HRFlowable(width="100%", thickness=1, color=INDIGO_MID, spaceAfter=6),
    ]


def _attendance_badge_color(pct: float):
    if pct >= 80:
        return GREEN
    elif pct >= 60:
        return AMBER
    return RED


def build_pdf_report(payload: dict, filepath: str) -> None:
    """
    Main entry point.  Writes a PDF to *filepath* from the structured *payload*.
    """
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=f"Monthly Report – {payload['student']['name']}",
    )
    sty = _styles()
    story = []

    # Header
    story.append(Paragraph("📚 Monthly Progress Report", sty["title"]))
    story.append(Paragraph(
        f"{payload['period']['month']} {payload['period']['year']}",
        sty["subtitle"],
    ))
    story.append(Spacer(1, 0.3 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=INDIGO, spaceAfter=8))

    # Student Info Table
    st = payload["student"]
    info_data = [
        ["Student Name", st["name"], "Subject", st["subject"]],
        ["Class / Grade", st["class_grade"], "Parent", st["parent_name"] or "—"],
        ["Parent Phone", st["parent_phone"] or "—", "Parent Email", st["parent_email"] or "—"],
        ["Report Generated", payload["generated_on"], "", ""],
    ]
    col_w = (PAGE_W - 2 * MARGIN) / 4
    info_tbl = Table(info_data, colWidths=[col_w * 0.9, col_w * 1.1, col_w * 0.9, col_w * 1.1])
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), INDIGO_LIGHT),
        ("BACKGROUND", (2, 0), (2, -1), INDIGO_LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), INDIGO),
        ("TEXTCOLOR", (2, 0), (2, -1), INDIGO),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 0.4 * cm))

    # Quick Stats
    att = payload["attendance"]
    ts = payload["test_summary"]
    stats = [
        ("Classes Held", str(att["total"])),
        ("Classes Attended", str(att["attended"])),
        ("Attendance %", f"{att['pct']}%"),
        ("Tests Taken", str(ts["count"])),
        ("Avg Score", f"{ts['avg_pct']}%"),
    ]
    story.extend(_section_header("At a Glance", sty))
    story.append(_stat_table(stats))
    story.append(Spacer(1, 0.4 * cm))

    # Lesson logs
    story.extend(_section_header("Topics Covered", sty))
    lessons = payload["lesson_log"]
    if lessons:
        lesson_data = [["#", "Date", "Topic Taught", "Homework", "Remarks"]]
        for i, row in enumerate(lessons, 1):
            lesson_data.append([
                str(i), row["date"], row["topic"], row["homework"], row["remarks"]
            ])
        col_widths = [0.6 * cm, 2.2 * cm, 5.5 * cm, 4.0 * cm, 4.0 * cm]
        lesson_tbl = Table(lesson_data, colWidths=col_widths, repeatRows=1)
        lesson_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_LIGHT]),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("WORDWRAP", (0, 0), (-1, -1), True),
        ]))
        story.append(lesson_tbl)
    else:
        story.append(Paragraph("No lesson logs recorded for this month.", sty["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # Test Results
    story.extend(_section_header("Test Performance", sty))
    tests = ts.get("tests", [])
    if tests:
        test_data = [["Date", "Test Name", "Topic", "Scored", "Total", "%", "Grade"]]
        for t in tests:
            pct_color = (
                GREEN if t["pct"] >= 75 else (AMBER if t["pct"] >= 50 else RED)
            )
            test_data.append([
                t["date"], t["name"], t["topic"],
                str(t["scored"]), str(t["total"]),
                Paragraph(
                    f'<font color="{pct_color.hexval()}">{t["pct"]}%</font>',
                    sty["small"],
                ),
                t["grade"],
            ])

        col_widths = [1.8 * cm, 3.8 * cm, 4.0 * cm, 1.4 * cm, 1.4 * cm, 1.4 * cm, 1.4 * cm]
        test_tbl = Table(test_data, colWidths=col_widths, repeatRows=1)
        test_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INDIGO),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (3, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, SLATE_LIGHT]),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(test_tbl)

        # Comments sub-table if any
        comments = [(t["name"], t["comments"]) for t in tests if t["comments"] != "—"]
        if comments:
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph("<b>Test-wise Comments</b>", sty["body"]))
            for name, cmt in comments:
                story.append(Paragraph(f"• <b>{name}:</b> {cmt}", sty["small"]))
    else:
        story.append(Paragraph("No tests recorded for this month.", sty["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # Performance Summary
    story.extend(_section_header("Performance Summary", sty))
    an = payload["analytics"]
    trend_icon = {"improving": "Improving", "declining": "Declining", "stable": "Stable", "no data": "—"}.get(
        an["trend"], "—"
    )
    summary_data = [
        ["Overall Trend", f"{trend_icon} {an['trend'].title()}"],
        ["All-time Average", f"{an['average_pct']}%"],
        ["Best Score", f"{an['highest_pct']}%"],
        ["Lowest Score", f"{an['lowest_pct']}%"],
        ["This Month's Avg", f"{ts['avg_pct']}%"],
    ]
    sum_tbl = Table(summary_data, colWidths=[5 * cm, PAGE_W - 2 * MARGIN - 5 * cm])
    sum_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), INDIGO_LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), INDIGO),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sum_tbl)
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(payload["performance_summary"], sty["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # Comments
    story.extend(_section_header("Teacher's Comments", sty))
    comment_box_data = [[Paragraph(payload["teacher_comments"], sty["body"])]]
    comment_tbl = Table(comment_box_data, colWidths=[PAGE_W - 2 * MARGIN])
    comment_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INDIGO_LIGHT),
        ("BOX", (0, 0), (-1, -1), 1, INDIGO_MID),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(comment_tbl)
    story.append(Spacer(1, 0.5 * cm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
    story.append(Paragraph(
        f"Generated by Tuition Manager  •  {payload['generated_on']}  •  Confidential",
        sty["footer"],
    ))

    doc.build(story)
