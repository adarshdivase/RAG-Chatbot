"""Smoke tests for system endpoints (no Google API required)."""

import os

os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-used")

from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness():
    client = TestClient(create_app())
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True


def test_health():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "environment" in data
