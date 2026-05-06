"""
vendor_router.py
Determines (1) which vendor category an email belongs to via the To: address,
and (2) which specific vendor it targets via keyword matching in the email content.
"""

import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "vendors.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def detect_category(to_address: str, config: dict) -> str | None:
    """
    Extracts the plus-address tag from the To: field and maps it to a category.
    e.g. "e1384355+catering@u.nus.edu" → "catering"
    Returns None if no match found.
    """
    match = re.search(r"\+([a-zA-Z0-9_]+)@", to_address)
    if not match:
        return None

    tag = match.group(1).lower()
    return config["email_to_category"].get(tag)


def detect_vendor(email_text: str, category: str, config: dict) -> dict | None:
    """
    Scans the full email text (subject + body) for vendor keywords.
    Returns the matched vendor dict, or None if no match.

    Scoring: vendor with the most keyword hits wins.
    Falls back to the first vendor in the category if nothing matches
    (so the AI can still attempt a generic reply).
    """
    vendors = config["categories"][category]["vendors"]
    text_lower = email_text.lower()

    scores = {}
    for vendor in vendors:
        hits = sum(1 for kw in vendor["keywords"] if kw in text_lower)
        scores[vendor["id"]] = hits

    best_id = max(scores, key=scores.get)
    best_score = scores[best_id]

    if best_score == 0:
        # No keyword matched — return None so orchestrator can handle gracefully
        return None

    # Return the full vendor dict for the best match
    return next(v for v in vendors if v["id"] == best_id)


def route_email(to_address: str, subject: str, body: str) -> dict:
    """
    Master routing function. Returns a result dict:
    {
        "category": "catering" | "transportation" | "events" | None,
        "category_label": "F&B Catering" | ...,
        "vendor": { id, name, keywords, persona_file } | None,
        "confidence": "high" | "low" | "unrouted"
    }
    """
    config = load_config()
    full_text = f"{subject} {body}"

    category = detect_category(to_address, config)

    if not category:
        return {
            "category": None,
            "category_label": None,
            "vendor": None,
            "confidence": "unrouted"
        }

    category_label = config["categories"][category]["label"]
    vendor = detect_vendor(full_text, category, config)

    return {
        "category": category,
        "category_label": category_label,
        "vendor": vendor,
        "confidence": "high" if vendor else "low"
    }