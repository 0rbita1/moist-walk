import requests
import json
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"  # Change to "llama3" if preferred

def load_persona(persona_file: str) -> str:
    return Path(persona_file).read_text()

def query_ollama(system_prompt: str, user_message: str) -> str:
    """Send a message to Ollama and return the full response text."""
    full_prompt = f"[SYSTEM]\n{system_prompt}\n\n[EMAIL FROM CLIENT]\n{user_message}\n\n[YOUR RESPONSE AS MARCUS]"

    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 1024,
        }
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["response"].strip()

def extract_pdf_data(ai_response: str) -> tuple[str, dict | None]:
    """
    Splits the AI response into (clean_text, pdf_data_dict or None).
    Looks for a <PDF_DATA>...</PDF_DATA> block.
    """
    if "<PDF_DATA>" not in ai_response:
        return ai_response, None

    parts = ai_response.split("<PDF_DATA>")
    clean_text = parts[0].strip()
    json_part = parts[1].split("</PDF_DATA>")[0].strip()

    try:
        pdf_data = json.loads(json_part)
        return clean_text, pdf_data
    except json.JSONDecodeError:
        # If JSON is malformed, return raw text and skip PDF
        return ai_response, None