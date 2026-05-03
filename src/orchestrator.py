#!/usr/bin/env python3
"""
Automated Mock Vendor System — Orchestrator
Usage: python src/orchestrator.py <path_to_eml_file>
       python src/orchestrator.py  (processes all .eml in input/ folder)
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent))

from email_parser import parse_eml
from ai_processor import load_persona, query_ollama, extract_pdf_data
from pdf_generator import generate_quote_pdf

# --- Config ---
PERSONA_FILE = Path(__file__).parent.parent / "personas" / "catering_vendor.txt"
INPUT_DIR    = Path(__file__).parent.parent / "input"
OUTPUT_DIR   = Path(__file__).parent.parent / "output"

def process_eml(eml_path: Path):
    print(f"\n{'='*60}")
    print(f"📧 Processing: {eml_path.name}")
    print(f"{'='*60}")

    # 1. Parse email
    email_data = parse_eml(str(eml_path))
    print(f"  From:    {email_data['from']}")
    print(f"  Subject: {email_data['subject']}")

    # 2. Build user message for the AI
    user_message = (
        f"From: {email_data['from']}\n"
        f"Subject: {email_data['subject']}\n"
        f"Date: {email_data['date']}\n\n"
        f"{email_data['body']}"
    )

    # 3. Query Ollama
    print("  🤖 Querying local AI model...")
    persona = load_persona(str(PERSONA_FILE))
    ai_raw = query_ollama(persona, user_message)

    # 4. Extract clean response + optional PDF data
    clean_response, pdf_data = extract_pdf_data(ai_raw)

    # 5. Build output filenames (timestamp + stem)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = eml_path.stem
    OUTPUT_DIR.mkdir(exist_ok=True)

    # 6. Write .md file
    md_path = OUTPUT_DIR / f"{stem}_{timestamp}.md"
    md_content = f"""# Vendor Response
**Original Email:** {eml_path.name}  
**From:** {email_data['from']}  
**Subject:** {email_data['subject']}  
**Processed At:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## AI-Generated Response

{clean_response}
"""
    if pdf_data:
        md_content += f"\n---\n\n> 📄 A PDF document was generated alongside this response.\n"

    md_path.write_text(md_content)
    print(f"  ✅ Markdown saved: {md_path.name}")

    # 7. Generate PDF if needed
    if pdf_data:
        pdf_path = OUTPUT_DIR / f"{stem}_{timestamp}.pdf"
        generate_quote_pdf(pdf_data, str(pdf_path))

    print(f"\n  Done! Outputs in: {OUTPUT_DIR}")


def main():
    if len(sys.argv) > 1:
        # Process a specific file
        eml_file = Path(sys.argv[1])
        if not eml_file.exists():
            print(f"❌ File not found: {eml_file}")
            sys.exit(1)
        process_eml(eml_file)
    else:
        # Process all .eml files in input/
        eml_files = sorted(INPUT_DIR.glob("*.eml"))
        if not eml_files:
            print(f"No .eml files found in {INPUT_DIR}")
            sys.exit(0)
        for eml_file in eml_files:
            process_eml(eml_file)

if __name__ == "__main__":
    main()