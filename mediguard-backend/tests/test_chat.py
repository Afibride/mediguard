from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_returns_answer_sources_and_disclaimer():
    response = client.post("/chat", json={"query": "What are malaria symptoms?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"]
    assert "fever" in data["answer"].lower()
    assert "sources" in data
    assert "disclaimer" in data


def test_chat_handles_greetings_and_help_without_sources():
    greeting = client.post("/chat", json={"query": "hello"})
    help_me = client.post("/chat", json={"query": "can you help me?"})
    how_are_you = client.post("/chat", json={"query": "how are you?"})
    thanks = client.post("/chat", json={"query": "thank you"})

    assert greeting.status_code == 200
    assert help_me.status_code == 200
    assert how_are_you.status_code == 200
    assert thanks.status_code == 200
    assert "welcome" in greeting.json()["answer"].lower()
    assert "yes" in help_me.json()["answer"].lower()
    assert "ready to help" in how_are_you.json()["answer"].lower()
    assert "welcome" in thanks.json()["answer"].lower()
    assert greeting.json()["sources"] == []


def test_chat_answers_malaria_prevention_accurately():
    response = client.post("/chat", json={"query": "how do i prevent against malaria"})
    assert response.status_code == 200
    data = response.json()
    answer = data["answer"].lower()
    assert "malaria" in answer
    assert any(term in answer for term in ["mosquito", "net", "stagnant water", "repellent"])
    assert "iv solution" not in answer
    assert "intravenous" not in answer
    assert data["sources"] == ["Malaria"]


def test_chat_answers_facility_and_platform_questions():
    facilities = client.post("/chat", json={"query": "where can i find nearby hospitals"})
    platform = client.post("/chat", json={"query": "how do i view my history on this platform"})

    assert facilities.status_code == 200
    assert platform.status_code == 200
    assert facilities.json()["mode"] == "facilities"
    assert "/nearby-facilities" in facilities.json()["answer"]
    assert "Nkwen Baptist Hospital" in facilities.json()["answer"]
    assert platform.json()["mode"] == "platform_help"
    assert "History" in platform.json()["answer"]


def test_chat_asks_questions_before_symptom_results():
    response = client.post("/chat", json={"query": "I have fever and chills and headache. What could this be?"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "symptom_follow_up"
    assert data["predictions"] == []
    assert set(["Fever", "Chills", "Headache"]).issubset(set(data["symptoms"]))
    assert data["follow_up_questions"]


def test_chat_returns_results_after_followup_answer():
    response = client.post(
        "/chat",
        json={
            "query": "It started 3 days ago, it is moderate, and I also have sweating.",
            "history": [
                {"role": "user", "content": "I have fever and chills and headache. What could this be?"},
                {"role": "assistant", "content": "Before I show possible matches, I need a little more information. Please answer the follow-up questions below."},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "symptom_check"
    assert data["predictions"]
    assert "Malaria" in data["answer"]
    assert data["follow_up_questions"] == []


def test_chat_can_answer_new_general_question_after_followup():
    response = client.post(
        "/chat",
        json={
            "query": "What is fever?",
            "history": [
                {"role": "user", "content": "I have fever and chills and headache. What could this be?"},
                {"role": "assistant", "content": "Before I show possible matches, I need a little more information. Please answer the follow-up questions below."},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("mode") != "symptom_check"
    assert data["answer"]
    assert data["sources"]


def test_chat_triages_pregnancy_warning_symptoms():
    response = client.post("/chat", json={"query": "I am 30 weeks pregnant and I have vaginal bleeding and severe abdominal pain"})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "pregnancy_triage"
    assert data["pregnancy_context"] is True
    assert "urgent care" in data["answer"].lower()
