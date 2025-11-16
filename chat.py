from flask import Blueprint, request, jsonify
import os
import requests
import json

chat_bp = Blueprint("chat", __name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")


@chat_bp.route("/ask", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Missing 'prompt'"}), 400

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300)
        resp.raise_for_status()
    except requests.RequestException as e:
        return jsonify({"error": f"Ollama request failed: {e}"}), 500

    chunks = []
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            chunk = json.loads(line.decode("utf-8"))
            piece = chunk.get("response", "")
            if piece:
                chunks.append(piece)
        except Exception:
            continue

    output = "".join(chunks).strip()
    return jsonify({"output": output})
