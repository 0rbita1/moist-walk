#!/usr/bin/env python3
"""
orchestrator.py — Main entry point for the Mock Vendor System.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from email_parser  import parse_eml
from vendor_router import route_email
from ai_processor  import load_persona, query_ollama, extract_pdf_data
from pdf_generator import generate_quote_pdf
from email_sender  import send_reply

INPUT_DIR    = Path(__file__).parent.parent / "input"
OUTPUT_DIR   = Path(__file__).parent.parent / "output"
PROJECT_ROOT = Path(__file__).parent.parent


def process_eml(eml_path: Path):
    print(f"\n{'='*60}")
    print(f"📧 Processing: {eml_path.name}")
    print(f"{'='*60}")

    # 1. Parse email — now returns clean structured fields
    email_data = parse_eml(str(eml_path))
    print(f"  To:      {email_data['to']}")
    print(f"  From:    {email_data['from']}")
    print(f"  Subject: {email_data['subject']}")
    print(f"  Body preview: {email_data['body'][:120].strip()!r}")

    # 2. Route to category + vendor
    route = route_email(to_address=email_data["to"])

    print(f"\n  📂 Category : {route['category_label'] or 'UNKNOWN'}")

    if route["confidence"] == "unrouted":
        print("  ⚠️  Could not determine vendor category from To: address.")
        _write_error_md(eml_path, email_data, "Unrouted: No category detected from To: address.")
        return

    vendor = route["vendor"]
    print(f"  🏢 Vendor   : {vendor['name']}")

    # 3. Load persona
    persona_path = PROJECT_ROOT / vendor["persona_file"]
    try:
        persona = load_persona(str(persona_path))
    except FileNotFoundError:
        print(f"  ❌ Persona file missing: {persona_path}")
        return

    # 4. Query Ollama
    print("  🤖 Querying local AI model...")
    user_message = (
        f"From: {email_data['from']}\n"
        f"Subject: {email_data['subject']}\n"
        f"Date: {email_data['date']}\n\n"
        f"{email_data['body']}"
    )
    ai_raw = query_ollama(persona, user_message)

    # 5. Extract response + optional PDF data
    clean_response, pdf_data = extract_pdf_data(ai_raw)
    if not pdf_data:
        pdf_data = {
            "document_type": "Quote",
            "client_name": email_data["from_name"] or email_data["from"],
            "event_date": "TBC",
            "items": [],
            "subtotal": 0,
            "tax_rate": 0.09,
            "tax_amount": 0,
            "grand_total": 0,
            "notes": clean_response,
        }

    # 6. Prepare output paths
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = eml_path.stem
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 7. Write .md file
    md_path = OUTPUT_DIR / f"{stem}_{timestamp}.md"
    md_lines = [
        f"# Vendor Response — {vendor['name']}",
        f"",
        f"| Field | Value |",
        f"|---|---|",
        f"| **Original Email** | `{eml_path.name}` |",
        f"| **Category** | {route['category_label']} |",
        f"| **Vendor** | {vendor['name']} |",
        f"| **Client** | {email_data['from']} |",
        f"| **Subject** | {email_data['subject']} |",
        f"| **Processed At** | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |",
        f"",
        f"---",
        f"",
        f"## Response",
        f"",
        clean_response,
    ]
    md_lines += ["", "---", "", "> 📄 A PDF document was generated alongside this response."]
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"  ✅ Markdown : {md_path.name}")

    # 8. Generate PDF for every model reply
    pdf_path = OUTPUT_DIR / f"{stem}_{timestamp}.pdf"
    generate_quote_pdf(pdf_data, str(pdf_path), vendor_id=vendor["id"])
        
    # 9. Send reply email back to the original participant
    print("  📤 Sending reply...")
    send_reply(
        to_address  = email_data["from_address"],
        to_name     = email_data["from_name"],
        subject     = email_data["subject"],
        body_text   = clean_response,
        vendor_name = vendor["name"],
        reply_to    = email_data["to"],
        pdf_path    = str(pdf_path),
    )

    print(f"\n  ✅ Done. Outputs in: {OUTPUT_DIR.relative_to(PROJECT_ROOT)}/")


def _write_error_md(eml_path: Path, email_data: dict, reason: str):
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = OUTPUT_DIR / f"{eml_path.stem}_{timestamp}_ERROR.md"
    md_path.write_text(
        f"# Routing Error\n\n"
        f"**File:** `{eml_path.name}`  \n"
        f"**To:** {email_data['to']}  \n"
        f"**From:** {email_data['from']}  \n"
        f"**Reason:** {reason}\n"
    )
    print(f"  📄 Error report: {md_path.name}")


def main():
    if len(sys.argv) > 1:
        eml_file = Path(sys.argv[1])
        if not eml_file.exists():
            print(f"❌ File not found: {eml_file}")
            sys.exit(1)
        process_eml(eml_file)
    else:
        eml_files = sorted(INPUT_DIR.glob("*.eml"))
        if not eml_files:
            print(f"No .eml files found in {INPUT_DIR}/")
            sys.exit(0)
        for eml_file in eml_files:
            process_eml(eml_file)


if __name__ == "__main__":
    main()