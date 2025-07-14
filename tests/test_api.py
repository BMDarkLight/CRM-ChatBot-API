import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

access_token = None
transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_main_page():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert "CRM Chatbot API for Online Shop" in response.text


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": True}


@pytest.mark.asyncio
async def test_signup_and_signin():
    global access_token
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "test1234"

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/signup", data={"username": username, "password": password})
        assert response.status_code == 200
        assert response.json()["message"] == "User created successfully"

        response = await ac.post("/signin", data={"username": username, "password": password})
        assert response.status_code == 200
        access_token = response.json()["access_token"]
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        response = await ac.post("/signin", data={"username": username, "password": "wrongpass"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_ask_endpoint_valid(monkeypatch):
    token = access_token

    class MockGraph:
        def invoke(self, state):
            return {"agent": "test-agent", "answer": "42"}

    monkeypatch.setattr("app.agent.graph", MockGraph())

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/ask",
            json={"query": "What is the answer?"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "unknown"
        assert data["response"] == "42"


@pytest.mark.asyncio
async def test_ask_missing_token():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/ask", json={"query": "What's the time?"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_ask_empty_query(monkeypatch):
    token = access_token

    monkeypatch.setattr("app.agent.graph", lambda: None)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/ask",
            json={"query": ""},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Query cannot be empty"