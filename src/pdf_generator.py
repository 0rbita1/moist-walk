from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER
from datetime import datetime

# Per-vendor branding: name, contact line, brand colour, accent colour
VENDOR_BRANDING = {
    # F&B Catering
    "kg_catering": {
        "display_name": "KG Catering Pte Ltd",
        "contact":      "sales@kgcatering.com.sg · +65 6123 4567",
        "brand":        colors.HexColor("#8B0000"),   # Deep red
        "accent":       colors.HexColor("#CD5C5C"),
        "footer":       "Quote valid for 14 days. 50% deposit required upon confirmation.",
    },
    "rilassi": {
        "display_name": "Rilassi Catering Pte Ltd",
        "contact":      "hello@rilassi.com.sg · +65 6234 5678",
        "brand":        colors.HexColor("#6B4423"),   # Warm brown
        "accent":       colors.HexColor("#C49A6C"),
        "footer":       "Quote valid for 14 days. 30% deposit required to secure booking.",
    },
    "canadian_pizza": {
        "display_name": "Canadian Pizza",
        "contact":      "orders@canadianpizza.com.sg · +65 6345 6789",
        "brand":        colors.HexColor("#C0392B"),   # Pizza red
        "accent":       colors.HexColor("#E74C3C"),
        "footer":       "24-hour advance notice required for Office Feast orders.",
    },
    # Transportation
    "comfortdelgro": {
        "display_name": "ComfortDelGro Bus Pte Ltd",
        "contact":      "charter@cdg.com.sg · +65 6535 0000",
        "brand":        colors.HexColor("#003DA5"),   # CDG blue
        "accent":       colors.HexColor("#4A90D9"),
        "footer":       "Quote valid for 7 days. 50% deposit required upon confirmation. All coaches are LTA-compliant.",
    },
    "hou_lee": {
        "display_name": "Hou Lee Bus Transport Service",
        "contact":      "houlee.transport@gmail.com · +65 9111 2222",
        "brand":        colors.HexColor("#1A5276"),   # Navy
        "accent":       colors.HexColor("#2E86C1"),
        "footer":       "No GST. Deposit of 30% required to confirm. Cash or PayNow accepted.",
    },
    "st_lee": {
        "display_name": "ST Lee Transport Pte Ltd",
        "contact":      "bookings@stleetransport.com.sg · +65 6456 7890",
        "brand":        colors.HexColor("#154360"),   # Dark blue
        "accent":       colors.HexColor("#1A8FC1"),
        "footer":       "Quote valid for 7 days. 40% deposit required upon confirmation.",
    },
    # Events
    "selfiebox": {
        "display_name": "Selfiebox Pte Ltd",
        "contact":      "hello@selfiebox.com.sg · +65 8123 4567",
        "brand":        colors.HexColor("#8E44AD"),   # Purple
        "accent":       colors.HexColor("#BB8FCE"),
        "footer":       "Quote valid for 14 days. 50% deposit required. Digital gallery delivered within 48 hours post-event.",
    },
    "partymojo": {
        "display_name": "PartyMojo Pte Ltd",
        "contact":      "hello@partymojo.com.sg · +65 8234 5678",
        "brand":        colors.HexColor("#E67E22"),   # Orange
        "accent":       colors.HexColor("#F0B27A"),
        "footer":       "Quote valid for 14 days. 50% deposit required. Setup 30 mins before event.",
    },
    "tagtical": {
        "display_name": "Tagtical Pte Ltd",
        "contact":      "missions@tagtical.com.sg · +65 8345 6789",
        "brand":        colors.HexColor("#1E8449"),   # Military green
        "accent":       colors.HexColor("#58D68D"),
        "footer":       "Quote valid for 14 days. 50% deposit required. All equipment included.",
    },
    "rave_productions": {
        "display_name": "Rave Productions",
        "contact":      "bookings@raveproductions.com.sg · +65 8456 7890",
        "brand":        colors.HexColor("#1A1A2E"),   # Dark navy
        "accent":       colors.HexColor("#E94560"),   # Neon pink
        "footer":       "Quote valid for 14 days. 50% deposit required. Setup begins 2 hours before event.",
    },
    "j2_terrarium": {
        "display_name": "J2 Terrarium",
        "contact":      "hello@j2terrarium.com.sg · +65 8567 8901",
        "brand":        colors.HexColor("#1E8449"),   # Forest green
        "accent":       colors.HexColor("#A9DFBF"),
        "footer":       "Quote valid for 14 days. 50% deposit required. All materials and care cards included.",
    },
    "party_rental_sg": {
        "display_name": "Party Rental SG LLP",
        "contact":      "rentals@partyrentalsg.com.sg · +65 8678 9012",
        "brand":        colors.HexColor("#2C3E50"),   # Charcoal
        "accent":       colors.HexColor("#F39C12"),   # Gold
        "footer":       "Full payment required to confirm. 20% damage deposit refunded after equipment inspection.",
    },
    "adpeak": {
        "display_name": "ADPEAK Pte Ltd",
        "contact":      "trek@adpeak.com.sg · +65 8789 0123",
        "brand":        colors.HexColor("#6E2F00"),   # Earth brown
        "accent":       colors.HexColor("#D4AC0D"),   # Trail gold
        "footer":       "Quote valid for 14 days. 30% deposit required. Cancellation policy applies.",
    },
}

# Fallback branding if vendor_id not found
DEFAULT_BRANDING = {
    "display_name": "Vendor",
    "contact":      "",
    "brand":        colors.HexColor("#2C3E50"),
    "accent":       colors.HexColor("#95A5A6"),
    "footer":       "Quote valid for 14 days.",
}


def generate_quote_pdf(pdf_data: dict, output_path: str, vendor_id: str = ""):
    """
    Generate a professional quote/invoice PDF from structured data.
    Uses vendor-specific branding based on vendor_id.
    """
    branding = VENDOR_BRANDING.get(vendor_id, DEFAULT_BRANDING)

    BRAND_COLOR  = branding["brand"]
    ACCENT_COLOR = branding["accent"]

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    story = []

    # --- Header ---
    company_style = ParagraphStyle(
        "company", fontSize=20, textColor=BRAND_COLOR,
        spaceAfter=2, fontName="Helvetica-Bold"
    )
    tagline_style = ParagraphStyle(
        "tagline", fontSize=9, textColor=colors.grey, spaceAfter=12
    )
    story.append(Paragraph(branding["display_name"], company_style))
    if branding["contact"]:
        story.append(Paragraph(branding["contact"], tagline_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_COLOR))
    story.append(Spacer(1, 0.4*cm))

    # --- Document Type Banner ---
    doc_type = pdf_data.get("document_type", "Quote").upper()
    banner_style = ParagraphStyle(
        "banner", fontSize=16, textColor=BRAND_COLOR,
        fontName="Helvetica-Bold", spaceAfter=12
    )
    story.append(Paragraph(doc_type, banner_style))

    # --- Meta Info Table ---
    reference_prefix = "".join(w[0] for w in branding["display_name"].split()[:3]).upper()
    meta_data = [
        ["Prepared for:", pdf_data.get("client_name", "Valued Client")],
        ["Event Date:",   pdf_data.get("event_date", "TBC")],
        ["Issued On:",    datetime.now().strftime("%d %B %Y")],
        ["Reference:",    f"{reference_prefix}-{datetime.now().strftime('%Y%m%d%H%M')}"],
    ]
    meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",     (0, 0), (0, -1), BRAND_COLOR),
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
        ("BACKGROUND",   (0, 0),  (-1, 0),  BRAND_COLOR),
        ("TEXTCOLOR",    (0, 0),  (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0),  (-1, 0),  10),
        ("ALIGN",        (1, 0),  (-1, -1), "RIGHT"),
        ("FONTSIZE",     (0, 1),  (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID",         (0, 0),  (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
        ("BOTTOMPADDING",(0, 0),  (-1, -1), 6),
        ("TOPPADDING",   (0, 0),  (-1, -1), 6),
        ("LEFTPADDING",  (0, 0),  (-1, -1), 8),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.4*cm))

    # --- Totals Block ---
    subtotal    = pdf_data.get("subtotal", 0)
    tax_rate    = pdf_data.get("tax_rate", 0.09)
    tax_amount  = pdf_data.get("tax_amount", subtotal * tax_rate)
    grand_total = pdf_data.get("grand_total", subtotal + tax_amount)

    totals_data = [
        ["", "Subtotal:",    f"SGD {subtotal:,.2f}"],
        ["", f"GST ({int(tax_rate*100)}%):", f"SGD {tax_amount:,.2f}"],
        ["", "GRAND TOTAL:", f"SGD {grand_total:,.2f}"],
    ]
    totals_table = Table(totals_data, colWidths=[9*cm, 4*cm, 3.5*cm])
    totals_table.setStyle(TableStyle([
        ("ALIGN",         (1, 0),  (-1, -1), "RIGHT"),
        ("FONTNAME",      (1, 2),  (-1, 2),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0),  (-1, -1), 10),
        ("FONTSIZE",      (1, 2),  (-1, 2),  12),
        ("TEXTCOLOR",     (1, 2),  (-1, 2),  BRAND_COLOR),
        ("LINEABOVE",     (1, 2),  (-1, 2),  1.5, BRAND_COLOR),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), 5),
    ]))
    story.append(totals_table)

    # --- Notes ---
    notes = pdf_data.get("notes", "")
    if notes:
        story.append(Spacer(1, 0.6*cm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 0.2*cm))
        notes_style = ParagraphStyle(
            "notes", fontSize=8, textColor=colors.grey, leading=12
        )
        story.append(Paragraph(f"<b>Notes:</b> {notes}", notes_style))

    # --- Footer ---
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        "footer", fontSize=8, textColor=colors.grey, alignment=TA_CENTER
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT_COLOR))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(branding["footer"], footer_style))

    doc.build(story)
    print(f"  ✅ PDF generated: {output_path}")