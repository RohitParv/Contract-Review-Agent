"""Render a review's structured results as a downloadable PDF.

Pure formatting step — no LLM call. Takes the same profile/risk_review/
financial_sim data already computed by the review pipeline (and the
narrative Markdown from the summary agent) and lays it out with reportlab,
styled to loosely match the web UI's indigo/purple accent.
"""

from __future__ import annotations

import io
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from shared.schemas.contract_profile import ContractProfile, FinancialSimulation, RiskReview

_ACCENT = colors.HexColor("#4f5bd5")
_ACCENT2 = colors.HexColor("#7c3aed")
_MUTED = colors.HexColor("#6b7280")
_BORDER = colors.HexColor("#e4e6eb")
_SEVERITY_COLORS = {
    "high": colors.HexColor("#dc2626"),
    "medium": colors.HexColor("#d97706"),
    "low": colors.HexColor("#16a34a"),
}

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle(
    "ReportTitle", parent=_styles["Title"], textColor=_ACCENT2, fontSize=20, spaceAfter=4
)
_DISCLAIMER = ParagraphStyle(
    "Disclaimer", parent=_styles["Normal"], textColor=_MUTED, fontSize=9, spaceAfter=16
)
_H2 = ParagraphStyle(
    "H2", parent=_styles["Heading2"], textColor=_ACCENT, fontSize=13, spaceBefore=16, spaceAfter=8
)
_BODY = ParagraphStyle("Body", parent=_styles["Normal"], fontSize=10, leading=14)
_BULLET = ParagraphStyle("Bullet", parent=_BODY, leftIndent=14, bulletIndent=2, spaceAfter=4)
_META = ParagraphStyle("Meta", parent=_BODY, textColor=_MUTED, fontSize=9.5)
_QUOTE = ParagraphStyle(
    "Quote",
    parent=_BODY,
    textColor=colors.HexColor("#374151"),
    fontName="Helvetica-Oblique",
    leftIndent=10,
    borderColor=_BORDER,
    borderWidth=0,
    spaceAfter=4,
)
_NOTE = ParagraphStyle("Note", parent=_BODY, textColor=_MUTED, fontSize=8.5, leading=11)


def _inline_md(text: str) -> str:
    """Bold/italic markdown -> reportlab's mini-markup, and escape the rest."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def _split_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "_preamble"
    buf: list[str] = []
    for line in markdown.splitlines():
        heading = re.match(r"^#{1,3}\s+(.*)", line)
        if heading:
            sections[current] = "\n".join(buf).strip()
            current = heading.group(1).strip()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf).strip()
    return sections


def _markdown_block(text: str, body_style=_BODY, bullet_style=_BULLET) -> list:
    flowables: list = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or re.match(r"^-{3,}$", stripped):
            continue
        bullet = re.match(r"^[-*]\s+(.*)", stripped)
        numbered = re.match(r"^\d+\.\s+(.*)", stripped)
        if bullet:
            flowables.append(Paragraph(f"&bull; {_inline_md(bullet.group(1))}", bullet_style))
        elif numbered:
            flowables.append(Paragraph(_inline_md(stripped), bullet_style))
        else:
            flowables.append(Paragraph(_inline_md(stripped), body_style))
    return flowables


def _money(value: float | None) -> str:
    return f"${value:,.2f}" if value is not None else "—"


def _financial_snapshot_table(sim: FinancialSimulation) -> Table:
    data = [
        ["Total Cost Over Term", "Worst-Case Late Fees", "Deposit at Stake"],
        [_money(sim.base_total_cost), _money(sim.worst_case_late_fees), _money(sim.deposit_at_stake)],
    ]
    table = Table(data, colWidths=[2.1 * inch, 2.1 * inch, 2.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f1f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), _MUTED),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("FONTSIZE", (0, 1), (-1, 1), 14),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (-1, 1), _ACCENT2),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ]
        )
    )
    return table


def generate_report_pdf(
    profile: ContractProfile,
    risk_review: RiskReview,
    financial_sim: FinancialSimulation,
    narrative_md: str,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        title="Contract & Lease Risk Report",
    )
    story: list = []

    story.append(Paragraph("Contract &amp; Lease Risk Report", _TITLE))
    story.append(
        Paragraph(
            "This is a reading aid, not legal advice. Always have anything "
            "important reviewed by an actual lawyer before you sign it.",
            _DISCLAIMER,
        )
    )

    meta_bits = [profile.document_type]
    if profile.parties:
        meta_bits.append(", ".join(profile.parties))
    if profile.term_length:
        meta_bits.append(profile.term_length)
    story.append(Paragraph(" • ".join(_inline_md(bit) for bit in meta_bits), _META))
    story.append(HRFlowable(width="100%", color=_BORDER, spaceBefore=10, spaceAfter=10))

    sections = _split_sections(narrative_md)

    overview = sections.get("Overview")
    if overview:
        story.append(Paragraph("Overview", _H2))
        story.extend(_markdown_block(overview))

    story.append(Paragraph("Financial Snapshot", _H2))
    story.append(_financial_snapshot_table(financial_sim))
    if financial_sim.notes:
        story.append(Spacer(1, 6))
        for note in financial_sim.notes:
            story.append(Paragraph(_inline_md(note), _NOTE))

    story.append(Paragraph("Risk Flags", _H2))
    if not risk_review.flags:
        story.append(Paragraph("No risky clauses were flagged in this document.", _BODY))
    for flag in risk_review.flags:
        color = _SEVERITY_COLORS.get(flag.severity.lower(), _MUTED)
        header_bits = [f'<font color="{color.hexval()}"><b>{flag.severity.upper()}</b></font>']
        header_bits.append(f"<b>{_inline_md(flag.category)}</b>")
        if flag.confidence is not None:
            header_bits.append(f'<font color="{_MUTED.hexval()}">confidence {flag.confidence:.0%}</font>')
        story.append(Paragraph("  &nbsp;&nbsp;•&nbsp;&nbsp;  ".join(header_bits), _BODY))
        story.append(Paragraph(f"“{_inline_md(flag.clause_excerpt)}”", _QUOTE))
        story.append(Paragraph(_inline_md(flag.explanation), _BODY))
        if flag.suggested_language:
            story.append(
                Paragraph(f"<b>Suggested language:</b> {_inline_md(flag.suggested_language)}", _NOTE)
            )
        story.append(Spacer(1, 10))

    questions = sections.get("Questions Worth Asking Before You Sign")
    if questions:
        story.append(Paragraph("Questions Worth Asking Before You Sign", _H2))
        story.extend(_markdown_block(questions))

    doc.build(story)
    return buffer.getvalue()
