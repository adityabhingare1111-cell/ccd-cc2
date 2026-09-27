"""Tests for the Student Attendance System. Run with: pytest -v"""
import pytest

import app as attendance_app


@pytest.fixture(autouse=True)
def client():
    """Reset the in-memory data before EVERY test, then give the test a client."""
    attendance_app.reset_data()
    attendance_app.app.config["TESTING"] = True
    with attendance_app.app.test_client() as test_client:
        yield test_client


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_shows_short_commit(client, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abcdef1234567890")
    assert client.get("/health").get_json()["commit"] == "abcdef1"
