from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_predict_returns_ranked_predictions():
    response = client.post("/predict", json={"symptoms": ["Fever", "Chills", "Headache"]})
    assert response.status_code == 200
    data = response.json()
    assert data["predictions"]
    assert "disclaimer" in data
    assert {"disease", "probability"}.issubset(data["predictions"][0])


def test_symptoms_returns_reference_feature_list():
    response = client.get("/symptoms")
    assert response.status_code == 200
    symptoms = response.json()["symptoms"]
    assert len(symptoms) == 126
    assert {"Fever", "Chills", "Headache"}.issubset(set(symptoms))


def test_predict_includes_pregnancy_context_note():
    response = client.post(
        "/predict",
        json={"symptoms": ["Fever", "Chills", "Headache"], "gender": "female", "is_pregnant": True, "pregnancy_weeks": 24},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pregnancy_note"]
    assert data["predictions"][0]["pregnancy_context"] is True
