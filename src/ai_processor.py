"""
ai_processor.py
Handles all communication with the local Ollama LLM.
"""

import requests
import re
import json
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3"


def load_persona(persona_file: str) -> str:
    path = Path(persona_file)
    if not path.exists():
        raise FileNotFoundError(f"Persona file not found: {persona_file}")
    return path.read_text()


def query_ollama(system_prompt: str, user_message: str) -> str:
    full_prompt = (
        f"[SYSTEM]\n{system_prompt}\n\n"
        f"[EMAIL FROM CLIENT]\n{user_message}\n\n"
        f"[YOUR RESPONSE]"
    )

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 1024,
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=240)
    response.raise_for_status()
    return response.json()["response"].strip()


def extract_pdf_data(ai_response: str) -> tuple[str, dict | None]:
    """
    Splits the AI response into (clean_text, pdf_data_dict or None).
    Handles common LLM formatting mistakes: markdown fences, extra whitespace,
    stray text inside the PDF_DATA block.
    """
    if "<PDF_DATA>" not in ai_response:
        return ai_response, None

    parts = ai_response.split("<PDF_DATA>")
    clean_text = parts[0].strip()

    # Get everything between the tags
    raw_block = parts[1].split("</PDF_DATA>")[0].strip()

    # Strip markdown code fences if the model wrapped JSON in ```json ... ```
    raw_block = re.sub(r"^```(?:json)?\s*", "", raw_block)
    raw_block = re.sub(r"\s*```$", "", raw_block)
    raw_block = raw_block.strip()

    # Attempt to extract just the JSON object if there's surrounding text
    json_match = re.search(r"\{.*\}", raw_block, re.DOTALL)
    if not json_match:
        print("  ⚠️  <PDF_DATA> block found but no valid JSON object inside.")
        return clean_text, None

    json_str = json_match.group(0)

    try:
        pdf_data = json.loads(json_str)
        return clean_text, pdf_data
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parse error in <PDF_DATA> block: {e}")
        print(f"      Raw block was:\n{json_str[:300]}")
        return clean_text, None