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


def find_student(client, roll_no):
    """Look up one student in /api/students, or return None."""
    data = client.get("/api/students").get_json()
    return next((s for s in data["students"] if s["roll_no"] == roll_no), None)


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_health_shows_short_commit(client, monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abcdef1234567890")
    assert client.get("/health").get_json()["commit"] == "abcdef1"


def test_add_valid_student_appears_in_api(client):
    response = client.post("/students", data={"roll_no": "CE200", "name": "Meera Iyer"})
    assert response.status_code == 302  # redirected back to the home page
    student = find_student(client, "CE200")
    assert student is not None
    assert student["name"] == "Meera Iyer"


def test_duplicate_roll_number_rejected(client):
    response = client.post("/students", data={"roll_no": "CE101", "name": "Someone Else"})
    assert response.status_code == 400
    assert b"already exists" in response.data


def test_empty_name_rejected(client):
    response = client.post("/students", data={"roll_no": "CE201", "name": "   "})
    assert response.status_code == 400
    assert find_student(client, "CE201") is None
