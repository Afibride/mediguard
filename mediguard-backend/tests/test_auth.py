from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_login_and_me():
    email = f"test-{uuid4().hex}@example.com"
    password = "strongpass123"

    register_response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    login_response = client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_forgot_and_reset_password_flow():
    email = f"reset-{uuid4().hex}@example.com"
    old_password = "oldpass123"
    new_password = "newpass123"

    client.post("/auth/register", json={"email": email, "password": old_password, "full_name": "Reset User"})
    forgot_response = client.post("/auth/forgot-password", json={"email": email})
    assert forgot_response.status_code == 200
    token = forgot_response.json()["reset_token"]

    reset_response = client.post("/auth/reset-password", json={"token": token, "password": new_password})
    assert reset_response.status_code == 200

    old_login = client.post("/auth/login", json={"email": email, "password": old_password})
    new_login = client.post("/auth/login", json={"email": email, "password": new_password})
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_chat_history_persists_for_authenticated_user():
    email = f"chat-history-{uuid4().hex}@example.com"
    password = "secret123"

    client.post("/auth/register", json={"email": email, "password": password, "full_name": "Chat History"})
    login = client.post("/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/history/chats",
        headers=headers,
        json={
            "title": "Fever question",
            "message": "I have fever and chills",
            "response": "Please use the symptom checker.",
            "sources": ["Malaria"],
            "follow_up_questions": ["How long has this been happening?"],
            "mode": "symptom_check",
            "pregnancy_context": False,
        },
    )
    assert created.status_code == 200
    chat_id = created.json()["id"]

    history = client.get("/history/chats", headers=headers)
    assert history.status_code == 200
    assert any(
        item["id"] == chat_id
        and item["sources"] == ["Malaria"]
        and item["follow_up_questions"] == ["How long has this been happening?"]
        for item in history.json()
    )

    deleted = client.delete(f"/history/chats/{chat_id}", headers=headers)
    assert deleted.status_code == 200
