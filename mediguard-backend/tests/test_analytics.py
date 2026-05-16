from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_top_diseases_shape():
    response = client.get("/analytics/top-diseases")
    assert response.status_code == 200
    data = response.json()
    assert data
    assert {"disease", "count"}.issubset(data[0])


def test_trends_and_heatmap_shape():
    trends = client.get("/analytics/trends")
    heatmap = client.get("/analytics/heatmap")
    assert trends.status_code == 200
    assert heatmap.status_code == 200
    assert {"week", "disease", "count"}.issubset(trends.json()[0])
    assert {"region", "disease", "count"}.issubset(heatmap.json()[0])
