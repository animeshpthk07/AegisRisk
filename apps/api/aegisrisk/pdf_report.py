"""Read-only PDF presentation of server-calculated synthetic report evidence."""

from base64 import b64encode
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

MAX_PDF_BYTES = 4 * 1024 * 1024
WIDTH = A4[0] - 84
INK = colors.HexColor("#142C42")
TEAL = colors.HexColor("#087F8C")
PALE = colors.HexColor("#EEF5F7")


def literal(value):
    # No user-controlled markup, links, images, expressions or external resources.
    # ASCII escapes preserve unsupported Unicode visibly instead of missing glyphs.
    text = str(value).encode("ascii", "backslashreplace").decode("ascii")
    text = "".join(c if 32 <= ord(c) <= 126 else " " for c in text)
    return escape(text)


def render_pdf(report):
    scenario = report.get("report_kind") == "baseline_and_scenario"
    baseline = report["baseline"] if scenario else report
    if baseline.get("synthetic") is not True or report.get("synthetic") is not True:
        raise ValueError("Only synthetic evidence can be rendered")
    rows = baseline["source"]["input_rows"]
    if len(rows) > 1000:
        raise ValueError("PDF facility limit exceeded")
    styles = {
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9,
                               leading=13, textColor=INK, spaceAfter=7),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=23,
                                leading=28, textColor=INK, spaceAfter=12),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=13,
                             leading=17, textColor=TEAL, spaceBefore=10,
                             spaceAfter=9, keepWithNext=True),
        "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=7.5,
                               leading=10, textColor=INK, splitLongWords=True),
        "head": ParagraphStyle("head", fontName="Helvetica-Bold", fontSize=7.5,
                               leading=10, textColor=colors.white),
    }

    def p(value, style="body"):
        return Paragraph(literal(value), styles[style])

    def table(headings, values, widths):
        data = [[p(value, "head") for value in headings]]
        data += [[p(value, "cell") for value in row] for row in values]
        result = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
        result.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
        ]))
        return result

    def money(value):
        return f"INR {Decimal(str(value)):,.2f}"

    def ratio(value):
        return "Not defined" if value is None else f"{value:.6f}"

    title = "Scenario comparison" if scenario else "Baseline portfolio review"
    summary = baseline["summary"]
    calc = baseline["calculation"]
    story = [p("AEGISRISK | EVIDENCE REPORT", "h2"), p(title, "title"),
             p("SYNTHETIC EDUCATIONAL DATA ONLY - NOT A CREDIT DECISION"),
             p("Generated (UTC): " + report["generated_at"]),
             p("Dataset: " + baseline["dataset_version"]),
             p("One-year horizon | Currency: INR | Deterministic calculations"),
             p("Portfolio at a glance", "h2")]
    story.append(table(["Measure", "Value"], [
        ["Fictional facilities", summary["facility_count"]],
        ["Exposure at default", money(calc["total_ead_decimal"])],
        ["One-year expected loss", money(calc["total_expected_loss_decimal"])],
        ["EAD-weighted PD (fraction)", ratio(summary["weighted_pd"])],
        ["EAD-weighted LGD (fraction)", ratio(summary["weighted_lgd"])],
        ["Borrower HHI (0-1)", ratio(summary["borrower_hhi"])],
    ], [WIDTH * .54, WIDTH * .46]))
    if scenario:
        result = report["scenario"]
        inputs = result["inputs"]
        evidence = result["calculation"]
        story += [p("Scenario assumptions and comparison", "h2"),
                  p(f"PD x{inputs['pd_multiplier']}; LGD x{inputs['lgd_multiplier']}; "
                    f"EAD x{inputs['ead_multiplier']}; "
                    f"scope: {inputs['industry'] or 'Whole portfolio'}"),
                  table(["Measure", "Exact calculation (INR)"], [
                      ["Baseline expected loss", evidence["baseline_el_decimal"]],
                      ["Stressed expected loss", evidence["stressed_el_decimal"]],
                      ["Change in expected loss", evidence["delta_el_decimal"]],
                      ["Relative change (fraction)",
                       evidence["delta_pct_decimal"] or "Not defined: zero baseline"],
                      ["Affected facilities", evidence["affected_facility_count"]],
                  ], [WIDTH * .54, WIDTH * .46])]
    else:
        story.append(p("Baseline only. No stress scenario or model prediction is included."))
    story += [p("Provenance and interpretation", "h2"),
              p("Canonical source SHA-256: " + baseline["source"]["canonical_sha256"]),
              p("A fingerprint identifies the normalized input rows, not the original "
                "upload bytes. It is not a digital signature or an audit opinion."),
              p("EL = sum(PD * LGD * EAD). PD/LGD use fractions, not percentage points. "
                "Weighted PD/LGD use EAD; borrower HHI sums squared exposure shares."),
              p(f"Decimal precision: {calc['decimal_precision']}; "
                f"rounding: {calc['decimal_rounding']}. Headline amounts are rounded "
                "to two decimals; the appendix preserves calculation strings."),
              p("Non-ASCII names are displayed as explicit Unicode escapes in this "
                "portable PDF. Download JSON for the original Unicode text."),
              p("Limitations", "h2")]
    notes = baseline["warnings"] + calc["notes"]
    if scenario:
        notes += report["scenario"]["calculation"]["notes"]
    story += [p(note) for note in dict.fromkeys(notes)]
    story += [PageBreak(), p("Facility calculation evidence", "title"),
              p("All amounts are INR. PD/LGD are fractions. Rows are ordered by ID. "
                "Identifiers and labels are literal text, never executable markup.")]
    losses = {row["id"]: row["expected_loss"]
              for row in calc["facility_expected_loss_decimal"]}
    if rows:
        story.append(table(["Facility / borrower / industry / geography / rating",
                            "PD", "LGD", "EAD", "Expected loss"], [
            [" | ".join(str(row[k]) for k in
                        ("id", "borrower", "industry", "geography", "rating")),
             row["pd"], row["lgd"], row["ead"], losses[row["id"]]] for row in rows
        ], [WIDTH * .38, WIDTH * .10, WIDTH * .10, WIDTH * .21, WIDTH * .21]))
    else:
        story.append(p("No facilities loaded."))
    if scenario:
        story += [PageBreak(), p("Scenario calculation evidence", "title"),
                  p("PD/LGD are capped at 1. Unselected facilities remain unchanged. "
                    "These are assumed sensitivities, not forecasts.")]
        scenario_rows = report["scenario"]["calculation"]["facilities"]
        if scenario_rows:
            story.append(table(["ID / affected / PD cap / LGD cap", "Stressed PD / LGD",
                                "Stressed EAD", "Baseline EL / stressed EL / delta"], [
                [f"{r['id']} | {r['affected']} | {r['pd_capped']} | {r['lgd_capped']}",
                 r["stressed_pd"] + " / " + r["stressed_lgd"], r["stressed_ead"],
                 r["baseline_el"] + " / " + r["stressed_el"] + " / " + r["delta_el"]]
                for r in scenario_rows
            ], [WIDTH * .26, WIDTH * .18, WIDTH * .22, WIDTH * .34]))
        else:
            story.append(p("No facilities loaded."))
    story += [Spacer(1, 12), p("End of report. Keep the JSON evidence for machine-readable "
                             "reconciliation. Not IFRS 9 ECL or regulatory capital.")]
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=42, leftMargin=42,
                            topMargin=48, bottomMargin=48, title="AegisRisk - " + title,
                            author="AegisRisk", pageCompression=1)

    def footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(TEAL)
        canvas.line(42, 35, A4[0] - 42, 35)
        canvas.setFillColor(INK)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(42, 23, "AegisRisk | Synthetic educational evidence")
        canvas.drawRightString(A4[0] - 42, 23, f"Page {document.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    content = output.getvalue()
    if len(content) > MAX_PDF_BYTES:
        raise ValueError("PDF output limit exceeded")
    return content


def pdf_envelope(report):
    # Transport evidence and PDF together: one snapshot, no second-request race.
    content = render_pdf(report)
    return {"report": report, "pdf": {
        "media_type": "application/pdf", "byte_length": len(content),
        "sha256": sha256(content).hexdigest(),
        "base64": b64encode(content).decode("ascii"),
    }}
