"""
email_parser.py
Parses .eml files into clean, structured data.
Handles: quoted-printable encoding, multipart MIME,
HTML fallback, and Microsoft Exchange headers.
"""

import email
import quopri
import re
from email import policy
from pathlib import Path


def decode_payload(part) -> str:
    """Decode a message part to clean UTF-8 text."""
    raw = part.get_payload(decode=True)
    if raw is None:
        return ""

    # Detect charset, fall back to utf-8 then latin-1
    charset = part.get_content_charset() or "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except (LookupError, UnicodeDecodeError):
        return raw.decode("latin-1", errors="replace")


def extract_plain_text(msg: email.message.Message) -> str:
    """
    Extract the best plain-text body from a message.
    Preference order: text/plain → strip HTML from text/html → empty string.
    """
    plain = None
    html  = None

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                continue
            if ct == "text/plain" and plain is None:
                plain = decode_payload(part)
            elif ct == "text/html" and html is None:
                html = decode_payload(part)
    else:
        ct = msg.get_content_type()
        if ct == "text/plain":
            plain = decode_payload(msg)
        elif ct == "text/html":
            html = decode_payload(msg)

    if plain:
        return clean_plain_text(plain)
    if html:
        return clean_plain_text(strip_html(html))
    return ""


def strip_html(html: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    return text


def clean_plain_text(text: str) -> str:
    """
    Remove quoted-printable soft line breaks, normalize whitespace,
    and strip Microsoft Exchange disclaimer boilerplate.
    """
    # Remove quoted-printable soft line breaks (=\n)
    text = re.sub(r"=\r?\n", "", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip common email footer separators and everything below them
    cutoff_patterns = [
        r"_{5,}",                        # _____ separator lines
        r"From:.*Sent:.*To:.*Subject:",  # Forwarded message headers
        r"CAUTION:.*external email",     # NUS/institutional warnings
        r"This e-mail.*confidential",    # Legal disclaimers
    ]
    for pattern in cutoff_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            text = text[:match.start()]

    return text.strip()


def decode_header_value(value: str) -> str:
    """Decode encoded email header values (e.g. =?utf-8?...?=)."""
    if not value:
        return ""
    parts = email.header.decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded).strip()


def parse_eml(filepath: str) -> dict:
    """
    Parse a .eml file and return a clean structured dict:
    {
        from_name:    display name of sender
        from_address: email address of sender
        to:           raw To: header value
        subject:      decoded subject line
        date:         date string
        body:         clean plain-text body
    }
    """
    raw = Path(filepath).read_bytes()
    msg = email.message_from_bytes(raw, policy=policy.compat32)

    # --- From ---
    raw_from = decode_header_value(msg.get("From", ""))
    from_match = re.match(r"^(.*?)\s*<([^>]+)>$", raw_from.strip())
    if from_match:
        from_name    = from_match.group(1).strip().strip('"')
        from_address = from_match.group(2).strip()
    else:
        from_name    = ""
        from_address = raw_from.strip()

    return {
        "from_name":    from_name,
        "from_address": from_address,
        "from":         raw_from,
        "to":           decode_header_value(msg.get("To", "")),
        "subject":      decode_header_value(msg.get("Subject", "(No Subject)")),
        "date":         msg.get("Date", ""),
        "body":         extract_plain_text(msg),
    }