"""Tests for the Student Attendance System. Run with: pytest -v"""
from datetime import date, timedelta

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


def test_percentage_after_two_days(client):
    client.post("/students", data={"roll_no": "CE300", "name": "Test Student"})
    client.post("/attendance", data={"date": "2024-01-10", "present": ["CE300"]})  # present
    client.post("/attendance", data={"date": "2024-01-11"})  # absent (box not ticked)

    student = find_student(client, "CE300")
    assert student["attended"] == 1
    assert student["total"] == 2
    assert student["percentage"] == 50.0


def test_future_date_rejected(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    response = client.post("/attendance", data={"date": tomorrow, "present": ["CE101"]})
    assert response.status_code == 400
    assert b"future" in response.data


def test_same_date_twice_rejected(client):
    first = client.post("/attendance", data={"date": "2024-02-01", "present": ["CE101"]})
    second = client.post("/attendance", data={"date": "2024-02-01", "present": ["CE101"]})
    assert first.status_code == 302
    assert second.status_code == 400
    assert b"already marked" in second.data
