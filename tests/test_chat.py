import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_chat_endpoint():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Gợi ý cho tôi phim hành động",
            "user_id": "test_user"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "recommendations" in data

@pytest.mark.asyncio
async def test_chat_invalid_request():
    response = client.post(
        "/api/v1/chat",
        json={
            "message": ""  # Empty message
        }
    )
    assert response.status_code == 422  # Validation error 