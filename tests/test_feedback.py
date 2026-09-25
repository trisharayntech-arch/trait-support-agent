from fastapi.testclient import TestClient

from backend.main import app


def test_submit_positive_feedback():
    with TestClient(app) as client:
        response = client.post(
            "/chat/feedback",
            json={
                "session_id": "feedback-test-positive",
                "rating": "positive",
                "comment": "Very helpful support.",
            },
        )

    assert response.status_code == 201

    data = response.json()
    assert data["session_id"] == "feedback-test-positive"
    assert data["rating"] == "positive"
    assert data["comment"] == "Very helpful support."


def test_submit_negative_feedback():
    with TestClient(app) as client:
        response = client.post(
            "/chat/feedback",
            json={
                "session_id": "feedback-test-negative",
                "rating": "negative",
                "comment": "The answer did not solve my problem.",
            },
        )

    assert response.status_code == 201

    data = response.json()
    assert data["rating"] == "negative"


def test_feedback_rejects_invalid_rating():
    with TestClient(app) as client:
        response = client.post(
            "/chat/feedback",
            json={
                "session_id": "feedback-test-invalid",
                "rating": "neutral",
                "comment": "Invalid rating.",
            },
        )

    assert response.status_code == 422