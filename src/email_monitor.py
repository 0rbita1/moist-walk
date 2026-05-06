"""
email_monitor.py
Monitors the NUS Outlook mailbox via IMAP.
Polls for unread emails sent to vendor plus-addresses,
saves them as .eml files, triggers the orchestrator,
then marks them as read.
"""

import os
import re
import time
import imaplib
import email
import requests
from email import policy
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
IMAP_SERVER   = os.getenv("IMAP_SERVER", "outlook.office365.com")
IMAP_PORT     = int(os.getenv("IMAP_PORT", 993))
USERNAME      = os.getenv("IMAP_USERNAME")
PASSWORD      = os.getenv("IMAP_PASSWORD")

WATCHED_TAGS  = {"catering", "transportation", "events"}
POLL_INTERVAL = 30  # seconds

INPUT_DIR     = Path(__file__).parent.parent / "input"
PROCESSED_DIR = INPUT_DIR / "processed"
PROCESSED_LOG = Path(__file__).parent.parent / "input" / "processed_ids.txt"


def warmup_ollama():
    """Pre-load the model into memory so the first real request doesn't time out."""
    print("  🔥 Warming up Ollama model...")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "mistral", "prompt": "Hello", "stream": False},
            timeout=300
        )
        if response.status_code == 200:
            print("  ✅ Ollama ready.\n")
        else:
            print(f"  ⚠️  Ollama warmup returned status {response.status_code}\n")
    except Exception as e:
        print(f"  ⚠️  Ollama warmup failed: {e}")
        print("       Make sure Ollama is running: ollama serve\n")

# ── Log helpers detection ─────────────────────────────────────────────────────
def load_processed_ids() -> set:
    if not PROCESSED_LOG.exists():
        return set()
    return set(PROCESSED_LOG.read_text().splitlines())

def save_processed_id(msg_id: str):
    PROCESSED_LOG.parent.mkdir(exist_ok=True)
    with open(PROCESSED_LOG, "a") as f:
        f.write(msg_id + "\n")

# ── Plus-address detection ────────────────────────────────────────────────────

def extract_plus_tag(to_header: str) -> str | None:
    """
    Extract vendor tag from a To: header.
    e.g. "e1384355+catering@u.nus.edu" → "catering"
    """
    match = re.search(r"\+([a-zA-Z0-9_]+)@", to_header or "")
    return match.group(1).lower() if match else None


def is_vendor_email(msg: email.message.Message) -> bool:
    """
    Check To:, Delivered-To:, and X-Original-To: headers
    since Gmail sometimes stores the plus-address in a different header.
    """
    headers_to_check = [
        msg.get("To", ""),
        msg.get("Delivered-To", ""),
        msg.get("X-Original-To", ""),
        msg.get("X-Forwarded-To", ""),
    ]

    for header_value in headers_to_check:
        tag = extract_plus_tag(header_value)
        if tag in WATCHED_TAGS:
            return True

    return False


# ── IMAP helpers ──────────────────────────────────────────────────────────────

def connect() -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(USERNAME, PASSWORD)
    return mail


def fetch_vendor_email_ids(mail: imaplib.IMAP4_SSL) -> list[bytes]:
    """
    Search directly for emails sent to any of the watched plus-addresses.
    This avoids fetching all unread emails and filtering manually.
    """
    mail.select("INBOX")
    matching_ids = set()

    for tag in WATCHED_TAGS:
        plus_address = f"{USERNAME.split('@')[0].split('+')[0]}+{tag}@{USERNAME.split('@')[1]}"
        # Search for emails TO this specific plus-address
        status, data = mail.search(None, f'TO "{plus_address}"')
        if status == "OK" and data[0]:
            for msg_id in data[0].split():
                matching_ids.add(msg_id)

    return list(matching_ids)


def fetch_message(mail: imaplib.IMAP4_SSL, msg_id: bytes) -> email.message.Message:
    status, data = mail.fetch(msg_id, "(RFC822)")
    raw = data[0][1]
    return email.message_from_bytes(raw, policy=policy.default)


def mark_as_read(mail: imaplib.IMAP4_SSL, msg_id: bytes):
    mail.store(msg_id, "+FLAGS", "\\Seen")


# ── EML saving ────────────────────────────────────────────────────────────────

def save_as_eml(msg: email.message.Message, raw_bytes: bytes) -> Path:
    INPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_subject = re.sub(r"[^\w\-]", "_", msg.get("Subject", "email"))[:40]
    filename = f"{timestamp}_{safe_subject}.eml"
    eml_path = INPUT_DIR / filename
    eml_path.write_bytes(raw_bytes)
    return eml_path


def move_to_processed(eml_path: Path):
    PROCESSED_DIR.mkdir(exist_ok=True)
    eml_path.rename(PROCESSED_DIR / eml_path.name)


# ── Main polling loop ─────────────────────────────────────────────────────────

def run_monitor():
    from orchestrator import process_eml

    print("🔍 Mock Vendor Monitor started (IMAP mode)")
    local_part, domain = USERNAME.split("@", 1)
    base_user = local_part.split("+", 1)[0]
    watched_addresses = ", ".join(f"{base_user}+{t}@{domain}" for t in WATCHED_TAGS)
    print(f"   Watching: {watched_addresses}")
    print(f"   Polling every {POLL_INTERVAL}s. Press Ctrl+C to stop.\n")

    warmup_ollama()

    processed_ids = load_processed_ids()

    while True:
        try:
            mail = connect()
            vendor_ids = fetch_vendor_email_ids(mail)

            new_ids = [mid for mid in vendor_ids if mid.decode() not in processed_ids]

            if new_ids:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(new_ids)} new vendor email(s) found")

                for msg_id in new_ids:
                    status, data = mail.fetch(msg_id, "(RFC822)")
                    raw_bytes = data[0][1]
                    msg = email.message_from_bytes(raw_bytes, policy=policy.default)

                    subject = msg.get("Subject", "(No Subject)")
                    to      = msg.get("To", "")
                    print(f"  ✉️  '{subject}' → {to}")

                    eml_path = save_as_eml(msg, raw_bytes)
                    process_eml(eml_path)
                    move_to_processed(eml_path)

                    # Log this ID so we never process it again
                    processed_ids.add(msg_id.decode())
                    save_processed_id(msg_id.decode())

                    print(f"  ✅ Processed.\n")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No new vendor emails.")

            mail.logout()

        except KeyboardInterrupt:
            print("\n🛑 Monitor stopped.")
            break
        except imaplib.IMAP4.abort:
            print("  ⚠️  IMAP connection dropped. Reconnecting on next poll...")
        except Exception as e:
            print(f"  ⚠️  Error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_monitor()