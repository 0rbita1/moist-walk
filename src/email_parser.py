import email
from pathlib import Path

def parse_eml(filepath: str) -> dict:
    """Parse a .eml file and return structured fields."""
    with open(filepath, "rb") as f:
        msg = email.message_from_bytes(f.read())

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                break
    else:
        body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

    return {
        "from": msg.get("From", "Unknown Sender"),
        "to": msg.get("To", ""),
        "subject": msg.get("Subject", "(No Subject)"),
        "date": msg.get("Date", ""),
        "body": body.strip(),
    }