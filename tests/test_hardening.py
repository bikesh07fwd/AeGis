import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_auth_bypass_blocked():
    # Security: Ensure missing X-API-KEY returns 401
    response = client.post("/api/v1/chat/generate", json={"question": "Test", "conversation_id": "1", "user_id": "tenant1"})
    assert response.status_code == 401

def test_auth_invalid_key_blocked():
    # Security: Ensure wrong X-API-KEY returns 401
    response = client.post("/api/v1/chat/generate", headers={"X-API-KEY": "wrong-key"}, json={"question": "Test", "conversation_id": "1", "user_id": "tenant1"})
    assert response.status_code == 401

def test_tenant_isolation_validation():
    # Reliability: Ensure user_id is mandatory to prevent unauthorized cross-tenant queries
    response = client.post("/api/v1/chat/stream", headers={"X-API-KEY": "secret-enterprise-key"}, json={"question": "Test", "conversation_id": "1"})
    # Should fail pydantic validation because user_id is missing
    assert response.status_code == 422
