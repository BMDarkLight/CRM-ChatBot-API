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

@pytest.fixture
def authorized_headers():
    client.post("/signup", data={"username": "testuser", "password": "testpass"})
    users_db.update_one({"username": "testuser"}, {"$set": {"permission": "admin"}})
    response = client.post("/signin", data={"username": "testuser", "password": "testpass"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_user_auth_flow(authorized_headers):
    res = client.get("/users/testuser", headers=authorized_headers)
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"

def test_user_deletion(authorized_headers):
    res = client.delete("/users/testuser", headers=authorized_headers)
    assert res.status_code == 200
    assert "deleted successfully" in res.json()["message"]

def test_ui_routes():
    res = client.get("/")
    assert res.status_code == 200
    assert "CRM Chatbot API" in res.text

    res = client.get("/chatbot")
    assert res.status_code == 200
    assert "Chatbot Interface" in res.text