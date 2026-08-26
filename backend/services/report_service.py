"""Report service -- generates PDF reports for analyses."""

from pathlib import Path
from datetime import datetime, timezone


def generate_report(analysis: dict) -> str:
    """Generate a PDF report. Returns the path to the PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"report_{analysis['id'][:8]}.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    el = []

    el.append(Paragraph("TruthLens Analysis Report", styles["Title"]))
    el.append(Spacer(1, 12))

    meta = [
        ["ID", analysis.get("id", "N/A")],
        ["Time", str(analysis.get("timestamp", ""))],
        ["Inputs", ", ".join(analysis.get("input_types", []))],
    ]
    el.append(Table(meta, colWidths=[80, 390], style=TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.grey), ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ])))
    el.append(Spacer(1, 20))

    verdict = analysis.get("verdict", "Unknown")
    score = analysis.get("threat_score", 0)
    vcolor = colors.green if verdict == "Low" else colors.orange if verdict == "Review Needed" else colors.red
    el.append(Paragraph(f"<b>Verdict: {verdict}</b>", styles["Heading2"]))
    el.append(Paragraph(f"Threat Score: <font color='{vcolor}'>{score}/100</font>", styles["Normal"]))
    el.append(Spacer(1, 20))

    breakdown = analysis.get("breakdown", {})
    rows = [["Modality", "Label", "Confidence"]]
    for mod, d in breakdown.items():
        if isinstance(d, dict) and "label" in d:
            rows.append([mod, d["label"], f"{d.get('confidence', 0):.2%}"])
    if len(rows) > 1:
        el.append(Table(rows, colWidths=[100, 100, 100], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ])))

    doc.build(el)
    return str(pdf_path)
