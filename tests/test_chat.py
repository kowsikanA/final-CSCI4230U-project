import json
from unittest.mock import patch, MagicMock

# This test ensures that the chatbox returns 400 when no propmt entered
def test_ask_without_prompt_returns_400(client):
    resp = client.post("/ai/ask", json={})  # no prompt
    assert resp.status_code == 400

    data = resp.get_json()
    assert data is not None
    
    assert "error" in data


# This enpoint does not connect to the AI model itself
# It ensures that chat.py calls the model
# Reads the streamed json
# Builds a final string
# And returns json field 
@patch("chat.requests.post")
def test_ask_with_prompt_calls_ollama_and_returns_output(mock_post, client):

    # Fake streaming response from Ollama 
    fake_chunk = {"response": "Hello from model!"}

    def fake_iter_lines():
        # Simulate the streaming JSON lines that chat.py reads
        yield json.dumps(fake_chunk).encode("utf-8")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = fake_iter_lines()
    mock_post.return_value = mock_response

    # Call the endpoint via Flask test client 
    resp = client.post("/ai/ask", json={"prompt": "Hello?"})

    #  Assert response 
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert "output" in data
    assert data["output"] == "Hello from model!"

    # Ensure external API was called once 
    mock_post.assert_called_once()
    called_url = mock_post.call_args.args[0]
    assert "api/generate" in called_url or "http://localhost" in called_url