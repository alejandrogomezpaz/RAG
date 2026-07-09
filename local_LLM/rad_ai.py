"""
rad_ai.py — query the local RAD-AI model (served by Ollama) from any script or notebook.

Prerequisites (one time):
    - Ollama running:            brew services start ollama   (or: ollama serve)
    - Model imported as "rad-ai": ollama create rad-ai -f Modelfile

Usage from a notebook:
    from rad_ai import query
    print(query("What is a pulmonary nodule?"))

    # override defaults per call:
    print(query("Summarize this report:", temperature=0.2, num_ctx=8192))
"""

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "rad-ai"


def query(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.7,
    top_p: float = 0.9,
    num_ctx: int = 4096,
    model: str = MODEL,
    timeout: int = 300,
) -> str:
    """
    Send a prompt to the local model and return the generated text.

    prompt      : your question / instruction
    system      : optional system prompt to steer behavior
    temperature : randomness (lower = more focused/deterministic)
    top_p       : nucleus sampling cutoff
    num_ctx     : context window in tokens
    model       : Ollama model name (default "rad-ai")
    timeout     : seconds to wait before giving up
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_ctx": num_ctx,
        },
    }
    if system:
        payload["system"] = system

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Can't reach Ollama at localhost:11434. "
            "Start it with:  brew services start ollama"
        )
    return resp.json()["response"].strip()


if __name__ == "__main__":
    # quick smoke test:  python rad_ai.py
    print(query("Say hello in one sentence."))
