# Imports 
from flask import Blueprint, request, jsonify
import os
import requests
import json

chat_bp = Blueprint("chat", __name__)

# Setting ollama url and model 
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")

# Post
@chat_bp.route("/ask", methods=["POST"])
def generate():

    # Getting entered message from json body 
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    # If nothing entered, error thrown 
    if not prompt:
        return jsonify({"error": "Missing 'prompt'"}), 400

    # Build the payload to send to the Ollama API
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
    }

    try:
        # Call the Ollama server and stream the response line by line
        resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=300)

        # Raise an error if the status code is not 2xx
        resp.raise_for_status()
    except requests.RequestException as e:
        # Any network / HTTP error from Ollama is reported as 500
        return jsonify({"error": f"Ollama request failed: {e}"}), 500

    # Collect streamed text chunks from Ollama
    chunks = []
    for line in resp.iter_lines():
        if not line:
            continue
        try:
            # Each line is a JSON object from Ollama
            chunk = json.loads(line.decode("utf-8"))
            
            # 'response' contains the generated text piece
            piece = chunk.get("response", "")
            if piece:
                chunks.append(piece)
        except Exception:
            # If one line is malformed, ignore it and continue
            continue

    # Join all pieces into one final answer
    output = "".join(chunks).strip()
    
    # Send the generated text back to the frontend
    return jsonify({"output": output})
