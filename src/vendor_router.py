"""
vendor_router.py
Determines which vendor an email targets via the plus-address tag in the To:
field.
"""

import json
import re
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config" / "vendors.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def extract_plus_tag(to_address: str) -> str | None:
    """Extract the plus-address tag from the To: field."""
    match = re.search(r"\+([a-zA-Z0-9_]+)@", to_address)
    if not match:
        return None

    return match.group(1).lower()


def iter_vendors(config: dict):
    """Yield each vendor together with its category metadata."""
    for category_key, category_data in config["categories"].items():
        for vendor in category_data["vendors"]:
            yield category_key, category_data, vendor


def get_vendor_tags(config: dict) -> list[str]:
    """Return the plus-address tags that should be monitored."""
    return [vendor["id"] for _, _, vendor in iter_vendors(config)]


def detect_vendor_by_tag(tag: str, config: dict) -> tuple[str, dict, dict] | None:
    """Map a plus-address tag directly to its category and vendor."""
    for category_key, category_data, vendor in iter_vendors(config):
        if vendor["id"].lower() == tag:
            return category_key, category_data, vendor
    return None


def route_email(to_address: str) -> dict:
    """
    Master routing function. Returns a result dict:
    {
        "category": "catering" | "transportation" | "events" | None,
        "category_label": "F&B Catering" | ...,
        "vendor": { id, name, persona_file } | None,
        "confidence": "high" | "unrouted"
    }
    """
    config = load_config()
    tag = extract_plus_tag(to_address)

    if not tag:
        return {
            "category": None,
            "category_label": None,
            "vendor": None,
            "confidence": "unrouted"
        }

    matched = detect_vendor_by_tag(tag, config)

    if not matched:
        return {
            "category": None,
            "category_label": None,
            "vendor": None,
            "confidence": "unrouted"
        }

    category, category_data, vendor = matched

    return {
        "category": category,
        "category_label": category_data["label"],
        "vendor": vendor,
        "confidence": "high"
    }