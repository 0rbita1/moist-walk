from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from datetime import datetime
from pathlib import Path

BRAND_COLOR = colors.HexColor("#2C5F2E")   # Deep green
ACCENT_COLOR = colors.HexColor("#97BC62")  # Light green

def generate_quote_pdf(pdf_data: dict, output_path: str):
    """Generate a professional quote/invoice PDF from structured data."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()
    story = []

    # --- Header ---
    company_style = ParagraphStyle("company", fontSize=20, textColor=BRAND_COLOR,
                                    spaceAfter=2, fontName="Helvetica-Bold")
    tagline_style = ParagraphStyle("tagline", fontSize=9, textColor=colors.grey,
                                    spaceAfter=12)
    story.append(Paragraph("Harvest &amp; Bloom Catering Co.", company_style))
    story.append(Paragraph("Premium Event Catering · contact@harvestandbloom.com · +65 9123 4567", tagline_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_COLOR))
    story.append(Spacer(1, 0.4*cm))

    # --- Document Type Banner ---
    doc_type = pdf_data.get("document_type", "Quote").upper()
    banner_style = ParagraphStyle("banner", fontSize=16, textColor=BRAND_COLOR,
                                   fontName="Helvetica-Bold", spaceAfter=12)
    story.append(Paragraph(doc_type, banner_style))

    # --- Meta Info Table ---
    meta_data = [
        ["Prepared for:", pdf_data.get("client_name", "Valued Client")],
        ["Event Date:", pdf_data.get("event_date", "TBC")],
        ["Issued On:", datetime.now().strftime("%d %B %Y")],
        ["Reference:", f"HBC-{datetime.now().strftime('%Y%m%d%H%M')}"],
    ]
    meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), BRAND_COLOR),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.6*cm))

    # --- Line Items Table ---
    header = ["Description", "Qty", "Unit Price (SGD)", "Total (SGD)"]
    rows = [header]
    for item in pdf_data.get("items", []):
        rows.append([
            item.get("description", ""),
            str(item.get("quantity", "")),
            f"{item.get('unit_price', 0):,.2f}",
            f"{item.get('total', 0):,.2f}",
        ])

    items_table = Table(rows, colWidths=[9*cm, 2*cm, 4*cm, 3.5*cm])
    items_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        # Body rows
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F9F5")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.4*cm))

    # --- Totals Block ---
    subtotal = pdf_data.get("subtotal", 0)
    tax_rate = pdf_data.get("tax_rate", 0.09)
    tax_amount = pdf_data.get("tax_amount", subtotal * tax_rate)
    grand_total = pdf_data.get("grand_total", subtotal + tax_amount)

    totals_data = [
        ["", "Subtotal:", f"SGD {subtotal:,.2f}"],
        ["", f"GST ({int(tax_rate*100)}%):", f"SGD {tax_amount:,.2f}"],
        ["", "GRAND TOTAL:", f"SGD {grand_total:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[9*cm, 4*cm, 3.5*cm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (1, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTSIZE", (1, 2), (-1, 2), 12),
        ("TEXTCOLOR", (1, 2), (-1, 2), BRAND_COLOR),
        ("LINEABOVE", (1, 2), (-1, 2), 1.5, BRAND_COLOR),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(totals_table)

    # --- Notes ---
    notes = pdf_data.get("notes", "")
    if notes:
        story.append(Spacer(1, 0.6*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 0.2*cm))
        notes_style = ParagraphStyle("notes", fontSize=8, textColor=colors.grey,
                                      leading=12)
        story.append(Paragraph(f"<b>Notes:</b> {notes}", notes_style))

    # --- Footer ---
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle("footer", fontSize=8, textColor=colors.grey,
                                   alignment=TA_CENTER)
    story.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT_COLOR))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This document is valid for 14 days from the date of issue. "
        "A 50% deposit is required to confirm your booking.",
        footer_style
    ))

    doc.build(story)
    print(f"  ✅ PDF generated: {output_path}")