from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code in [200, 404]

def test_chat_generate_validation():
    # Should fail pydantic validation without user_id and conversation_id
    response = client.post("/api/v1/chat/generate", headers={"X-API-KEY": "secret-enterprise-key"}, json={"question": "Test"})
    assert response.status_code == 422
