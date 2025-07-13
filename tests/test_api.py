import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_main_page():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert "CRM Chatbot API for Online Shop" in response.text

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": True}

@pytest.mark.asyncio
async def test_ask_endpoint_empty_query():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ask", params={"query": ""})
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_ask_endpoint_valid(monkeypatch):
    class MockGraph:
        def invoke(self, state):
            return {"agent": "test-agent", "answer": "Test response"}

    monkeypatch.setattr("app.main.graph", MockGraph())

    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/ask", params={"query": "What is my order status?"})
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "test-agent"
        assert data["response"] == "Test response"