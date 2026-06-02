"""
email_sender.py
Sends the vendor's AI-generated reply back to the original participant
via Gmail SMTP, with an optional PDF attachment.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email                import encoders
from pathlib              import Path
from dotenv               import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587
USERNAME    = os.getenv("IMAP_USERNAME")
PASSWORD    = os.getenv("IMAP_PASSWORD")


def send_reply(
    to_address:   str,
    to_name:      str,
    subject:      str,
    body_text:    str,
    vendor_name:  str,
    reply_to:     str,
    pdf_path:     str | None = None,
):
    """
    Send an email reply to the participant.

    Args:
        to_address:  Recipient email address (the original sender)
        to_name:     Recipient display name
        subject:     Original email subject (will be prefixed with Re:)
        body_text:   Plain-text AI-generated response
        vendor_name: Name of the vendor (shown in From display name)
        pdf_path:    Optional path to a PDF to attach
    """
    msg = MIMEMultipart()
    msg["From"]    = f"{vendor_name} <{USERNAME}>"
    msg["To"]      = f"{to_name} <{to_address}>" if to_name else to_address
    msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject

    msg = MIMEMultipart()
    msg["From"]     = f"{vendor_name} <{USERNAME}>"
    msg["To"]       = f"{to_name} <{to_address}>" if to_name else to_address
    msg["Subject"]  = f"Re: {subject}" if not subject.startswith("Re:") else subject
    msg["Reply-To"] = reply_to

    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    if pdf_path and Path(pdf_path).exists():
        with open(pdf_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = Path(pdf_path).name
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)
        print(f"  📎 PDF attached: {filename}")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(USERNAME, PASSWORD)
            server.sendmail(USERNAME, to_address, msg.as_string())
        print(f"  📤 Reply sent to: {to_address}")
        print(f"  ↩️  Reply-To set: {reply_to}")
    except Exception as e:
        print(f"  ❌ Failed to send email: {e}")
        raise