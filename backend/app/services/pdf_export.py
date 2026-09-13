import re
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# Matches the numbered section headers your CLINICAL_PROMPT_TEMPLATE asks
# the LLM to produce, e.g. "1. CLINICAL SUMMARY", "6. SPECIFIC MEDICATION
# SUGGESTIONS (Include dosages, contraindications based on patient
# profile)" - used to split the flat report text into styled sections.
# Allows the parenthetical explanations that appear on headers 3, 4, and 6
# in the actual prompt template (lowercase letters, commas, parens) -
# an earlier all-caps-only version silently failed to match those three.
SECTION_PATTERN = re.compile(r"^(\d{1,2}\.\s+[A-Z][A-Za-z0-9 &/\-(),]*)\s*$", re.MULTILINE)


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CDSSTitle", parent=styles["Title"], fontSize=18, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="CDSSSubtitle", parent=styles["Normal"], fontSize=9,
        textColor=colors.grey, alignment=TA_CENTER, spaceAfter=14,
    ))
    styles.add(ParagraphStyle(
        name="CDSSSectionHeading", parent=styles["Heading2"], fontSize=12,
        textColor=colors.HexColor("#1a3d7c"), spaceBefore=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="CDSSBody", parent=styles["Normal"], fontSize=10,
        leading=14, alignment=TA_JUSTIFY,
    ))
    styles.add(ParagraphStyle(
        name="CDSSDisclaimer", parent=styles["Normal"], fontSize=8,
        leading=11, textColor=colors.grey, spaceBefore=16,
    ))
    return styles


def _split_into_sections(report_text: str):
    """Splits the flat LLM-generated report text into (heading, body) pairs
    using the numbered section headers as anchors. Falls back to a single
    unsectioned block if the model didn't follow the expected format."""
    matches = list(SECTION_PATTERN.finditer(report_text))
    if not matches:
        return [(None, report_text.strip())]

    sections = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(report_text)
        body = report_text[start:end].strip()
        sections.append((heading, body))

    # Anything before the first recognized heading (rare, but keep it safe)
    preamble = report_text[: matches[0].start()].strip()
    if preamble:
        sections.insert(0, (None, preamble))

    return sections


def _escape_for_reportlab(text: str) -> str:
    """Paragraph() interprets a small set of XML-like tags - escape raw
    text first so stray '<' or '&' in the LLM output don't break rendering
    or get silently swallowed."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_report_pdf(
    report_id: int,
    patient_name: str,
    patient_age,
    patient_gender: str,
    doctor_name: str,
    created_at: datetime,
    report_text: str,
) -> bytes:
    """Renders a saved report into a formatted PDF and returns the raw
    PDF bytes. Reuses the already-generated report_text - no LLM call
    here, so this is fast even though the original generation wasn't."""
    styles = _build_styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )

    story = []

    story.append(Paragraph("Clinical Decision Support System", styles["CDSSTitle"]))
    story.append(Paragraph("Guideline-Grounded Clinical Report", styles["CDSSSubtitle"]))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#1a3d7c"), thickness=1))
    story.append(Spacer(1, 10))

    meta_table = Table(
        [
            ["Report ID:", f"#{report_id}", "Generated:", created_at.strftime("%d %b %Y, %H:%M")],
            ["Patient:", patient_name, "Age / Gender:", f"{patient_age} / {patient_gender}"],
            ["Attending:", f"Dr. {doctor_name}", "", ""],
        ],
        colWidths=[1.0 * inch, 2.3 * inch, 1.1 * inch, 1.9 * inch],
    )
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1a3d7c")),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#1a3d7c")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.5))

    disclaimer_text = None
    working_text = report_text

    # Pull the required physician disclaimer out and render it separately
    # at the bottom, styled distinctly, instead of mixed into a numbered
    # section - matches how the prompt template defines it as a standalone
    # closing statement.
    disclaimer_match = re.search(r'"DISCLAIMER:.*?"', report_text, re.DOTALL)
    if disclaimer_match:
        disclaimer_text = disclaimer_match.group(0).strip('"')
        working_text = report_text[: disclaimer_match.start()].strip()

    for heading, body in _split_into_sections(working_text):
        if not body:
            continue
        if heading:
            story.append(Paragraph(_escape_for_reportlab(heading), styles["CDSSSectionHeading"]))
        for paragraph in body.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            # Preserve simple bullet-style lines without treating them as
            # separate flowables - just keep line breaks inside the block.
            safe_paragraph = _escape_for_reportlab(paragraph).replace("\n", "<br/>")
            story.append(Paragraph(safe_paragraph, styles["CDSSBody"]))
            story.append(Spacer(1, 4))

    if disclaimer_text:
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=0.5))
        story.append(Paragraph(_escape_for_reportlab(disclaimer_text), styles["CDSSDisclaimer"]))

    doc.build(story)
    return buffer.getvalue()