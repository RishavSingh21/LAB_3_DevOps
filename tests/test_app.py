import pytest

from app import main


@pytest.fixture
def client():
    main.app.config.update(TESTING=True)
    return main.app.test_client()


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_greeting_feature_flag_defaults_to_v1(client):
    response = client.get("/api/greeting")

    assert response.json == {
        "message": "Hello from Lab 3!",
        "feature_enabled": False,
    }


def test_greeting_feature_flag_enables_v2(client, monkeypatch):
    monkeypatch.setenv("FEATURE_GREETING_V2", "true")

    response = client.get("/api/greeting")

    assert response.json == {
        "message": "Hello from Lab 3, version 2!",
        "feature_enabled": True,
    }


def test_metrics_endpoint(client):
    client.get("/api/greeting")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"demo_http_requests_total" in response.data
