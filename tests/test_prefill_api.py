"""C3: Prefill API tests."""
import pytest
import json
from app.services.prefill_service import extract_prefill


def test_prefill_empty_text_returns_degraded(app):
    """Empty document returns degraded and warnings."""
    with app.app_context():
        out = extract_prefill("")
        assert out["degraded"] is True
        assert out["warnings"]
        assert "suggestions" in out


def test_prefill_short_text_returns_suggestions(app):
    """Short text gets suggestions (course_title, topic)."""
    with app.app_context():
        out = extract_prefill("Course A\nTopic B")
        assert "suggestions" in out
        assert out["suggestions"].get("course_title")
        assert out["suggestions"]["course_title"]["value"] == "Course A"
        assert out["suggestions"]["topic"]["value"] == "Topic B"


def test_prefill_endpoint_200(client, app, seed_users):
    """GET prefill for existing doc returns 200 and suggestions."""
    client.post("/api/auth/login", json={"user_id": "T001", "password": "teacher123"})
    upload = client.post(
        "/api/cscl/courses/default-course/docs/upload",
        json={
            "title": "Prefill Test",
            "text": "Data Science 101. Topic: Machine Learning. Learning objectives: Understand ML. Skills: Apply algorithms. Duration 90 minutes. Class size 30."
        },
        content_type="application/json",
    )
    assert upload.status_code == 201
    doc_id = json.loads(upload.data).get("document", {}).get("id")
    assert doc_id
    resp = client.get(f"/api/cscl/courses/default-course/docs/{doc_id}/prefill")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["success"] is True
    assert "suggestions" in data
    assert "course_title" in data["suggestions"] or "topic" in data["suggestions"]


def test_prefill_endpoint_404(client, app, seed_users):
    """GET prefill for non-existent doc returns 404."""
    client.post("/api/auth/login", json={"user_id": "T001", "password": "teacher123"})
    resp = client.get("/api/cscl/courses/default-course/docs/00000000-0000-0000-0000-000000000000/prefill")
    assert resp.status_code == 404
