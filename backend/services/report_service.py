"""Report service — generates PDF reports for analyses."""

from pathlib import Path


def generate_report(analysis: dict) -> str:
    """Generate a PDF report. Returns the path to the PDF."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = reports_dir / f"report_{analysis['id'][:8]}.pdf"

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=20*mm, rightMargin=20*mm)
    styles = getSampleStyleSheet()
    el = []

    # --- Title ---
    el.append(Paragraph("TruthLens Analysis Report", styles["Title"]))
    el.append(Spacer(1, 6))
    el.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#333333")))
    el.append(Spacer(1, 12))

    # --- Metadata ---
    meta = [
        ["ID", analysis.get("id", "N/A")[:16] + "..."],
        ["Timestamp", str(analysis.get("timestamp", ""))],
        ["Inputs", ", ".join(analysis.get("input_types", [])) or "None"],
    ]
    el.append(Table(meta, colWidths=[80, 370], style=TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])))
    el.append(Spacer(1, 16))

    # --- Threat Score Bar ---
    verdict = analysis.get("verdict", "Unknown")
    score = analysis.get("threat_score", 0)
    consistency = analysis.get("consistency", "unanimous")

    vcolor = colors.green if verdict == "Low" else colors.orange if verdict == "Review Needed" else colors.red
    bar_color = colors.HexColor("#22c55e") if score <= 30 else colors.HexColor("#f59e0b") if score <= 70 else colors.HexColor("#ef4444")

    el.append(Paragraph("Threat Assessment", styles["Heading2"]))
    el.append(Spacer(1, 6))

    # Score + verdict row
    score_data = [
        ["Score", f"{score}/100", "Verdict", verdict, "Consistency", consistency],
    ]
    el.append(Table(score_data, colWidths=[50, 50, 55, 90, 75, 80], style=TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTSIZE", (1, 0), (1, 0), 14),
        ("TEXTCOLOR", (1, 0), (1, 0), bar_color),
        ("TEXTCOLOR", (3, 0), (3, 0), vcolor),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])))
    el.append(Spacer(1, 8))

    # Visual bar
    bar_width = 450
    bar_height = 14
    filled = int(bar_width * score / 100)

    bar_data = [["" for _ in range(2)]]
    bar_table = Table(bar_data, colWidths=[filled or 1, bar_width - filled or 1], rowHeights=[bar_height])
    bar_style = [
        ("BACKGROUND", (0, 0), (0, 0), bar_color),
        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#e5e7eb")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#999999")),
    ]
    bar_table.setStyle(TableStyle(bar_style))
    el.append(bar_table)
    el.append(Spacer(1, 16))

    # --- Modality Breakdown ---
    breakdown = analysis.get("breakdown", {})
    mod_rows = [["Modality", "Label", "Confidence", "Threat Contrib.", "Weight"]]
    for mod in ["text", "image", "video", "audio"]:
        d = breakdown.get(mod)
        if d and isinstance(d, dict) and "label" in d:
            label = d["label"]
            conf = d.get("confidence", 0)
            threat = d.get("threat_contribution", 0)
            weight = d.get("weight", 0)
            mod_rows.append([mod.upper(), label, f"{conf:.1%}", f"{threat:.1f}", f"{weight:.0%}"])

    if len(mod_rows) > 1:
        el.append(Paragraph("Modality Breakdown", styles["Heading2"]))
        el.append(Spacer(1, 6))

        header_color = colors.HexColor("#1e293b")
        mod_table = Table(mod_rows, colWidths=[70, 70, 80, 90, 70])
        mod_style = [
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        # Color rows by label
        for i, row in enumerate(mod_rows[1:], 1):
            if row[1] in ("fake", "cloned"):
                mod_style.append(("TEXTCOLOR", (1, i), (1, i), colors.HexColor("#ef4444")))
            else:
                mod_style.append(("TEXTCOLOR", (1, i), (1, i), colors.HexColor("#22c55e")))

        mod_table.setStyle(TableStyle(mod_style))
        el.append(mod_table)
        el.append(Spacer(1, 16))

    # --- Explanations ---
    explanations = analysis.get("explanations", {})
    if explanations:
        el.append(Paragraph("Explanations", styles["Heading2"]))
        el.append(Spacer(1, 6))

        # Text explanations (token attributions)
        text_exp = explanations.get("text")
        if text_exp and "tokens" in text_exp:
            el.append(Paragraph("<b>Text — Token Attributions (SHAP)</b>", styles["Normal"]))
            el.append(Spacer(1, 4))
            token_rows = [["Token", "Attribution"]]
            for t in text_exp["tokens"][:10]:
                token_rows.append([t.get("token", ""), f"{t.get('attribution', 0):+.4f}"])
            token_table = Table(token_rows, colWidths=[200, 100])
            token_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            el.append(token_table)
            el.append(Spacer(1, 10))

        # Video explanations (frame importance)
        video_exp = explanations.get("video")
        if video_exp and "frame_importance" in video_exp:
            el.append(Paragraph("<b>Video — Frame Importance</b>", styles["Normal"]))
            el.append(Spacer(1, 4))
            frame_rows = [["Frame", "Importance"]]
            for f in video_exp["frame_importance"][:10]:
                frame_rows.append([f"Frame {f.get('frame', 0)}", f"{f.get('importance', 0):.4f}"])
            frame_table = Table(frame_rows, colWidths=[200, 100])
            frame_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            el.append(frame_table)
            el.append(Spacer(1, 10))

        # Audio explanations (MFCC coefficients)
        audio_exp = explanations.get("audio")
        if audio_exp and "top_coefficients" in audio_exp:
            el.append(Paragraph("<b>Audio — Frequency Band Importance (MFCC)</b>", styles["Normal"]))
            el.append(Spacer(1, 4))
            coef_rows = [["Coefficient", "Est. Freq (Hz)", "Importance"]]
            for c in audio_exp["top_coefficients"][:10]:
                coef_rows.append([
                    f"MFCC-{c.get('mfcc_index', 0)}",
                    f"{c.get('estimated_freq_hz', 0)}",
                    f"{c.get('importance', 0):.6f}",
                ])
            coef_table = Table(coef_rows, colWidths=[120, 120, 120])
            coef_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            el.append(coef_table)
            el.append(Spacer(1, 10))

    # --- Disclaimer ---
    el.append(Spacer(1, 20))
    el.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    el.append(Spacer(1, 6))
    disclaimer = (
        "DISCLAIMER: This report is generated by an AI system and should not be "
        "considered definitive proof of misinformation. Results are probabilistic "
        "estimates based on trained models. Human review is recommended for all "
        "high-risk assessments. TruthLens v0.1.0"
    )
    el.append(Paragraph(disclaimer, styles["Normal"]))
    el.append(Spacer(1, 4))
    el.append(Paragraph(f"Generated: {analysis.get('timestamp', 'N/A')}", styles["Normal"]))

    doc.build(el)
    if not pdf_path.exists():
        raise RuntimeError(f"PDF generation failed: {pdf_path}")
    return str(pdf_path)
