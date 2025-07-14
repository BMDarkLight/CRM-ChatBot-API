import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import users_db
from app.agent import sessions_db

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def cleanup():
    users_db.delete_many({"username": "testuser"})
    sessions_db.delete_many({})
    yield
    users_db.delete_many({"username": "testuser"})
    sessions_db.delete_many({})

def test_signup_and_signin():
    res = client.post("/signup", data={"username": "testuser", "password": "testpass"})
    assert res.status_code == 200
    assert res.json()["message"] == "User created successfully"

    res = client.post("/signin", data={"username": "testuser", "password": "testpass"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token
    return token

def test_user_auth_flow():
    token = test_signup_and_signin()
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/users/testuser", headers=headers)
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"

def test_chat_session_lifecycle():
    token = test_signup_and_signin()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post("/ask", headers=headers, json={"query": "What's up?"})
    assert res.status_code == 200
    assert "agent" in res.json()
    assert "response" in res.json()

    res = client.get("/sessions", headers=headers)
    assert res.status_code == 200
    sessions = res.json()
    assert len(sessions) >= 1
    session_id = sessions[0]["session_id"]

    res = client.get(f"/sessions/{session_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["session_id"] == session_id

    res = client.delete(f"/sessions/{session_id}", headers=headers)
    assert res.status_code == 200
    assert "deleted successfully" in res.json()["message"]

def test_user_deletion():
    token = test_signup_and_signin()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.delete("/users/testuser", headers=headers)
    assert res.status_code == 200
    assert "deleted successfully" in res.json()["message"]

def test_ui_routes():
    res = client.get("/")
    assert res.status_code == 200
    assert "CRM Chatbot API" in res.text

    res = client.get("/chatbot")
    assert res.status_code == 200
    assert "Chatbot Interface" in res.text