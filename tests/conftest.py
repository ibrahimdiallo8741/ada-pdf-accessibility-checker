"""Shared test setup.

Run everything against the code in this repository:

    pytest

Run the service tests against ANY deployed copy of the service, without editing code:

    BASE_URL=https://your-service.example.com pytest tests/test_api.py

(PDF fixtures are generated in memory and uploaded, so a deployed service needs no
extra files.) When BASE_URL is not set, the tests start the app in-process.
"""
import os
import pathlib
import sys
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BASE_URL = os.getenv("BASE_URL")


@pytest.fixture(scope="session")
def client():
    if BASE_URL:
        import httpx
        with httpx.Client(base_url=BASE_URL, timeout=120) as session:
            yield session
    else:
        from fastapi.testclient import TestClient
        from service import app
        with TestClient(app) as session:
            yield session


def wait_done(client, scan_id, timeout=60):
    start = time.time()
    while True:
        response = client.get(f"/scans/{scan_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] in ("COMPLETED", "REJECTED"):
            return body
        assert time.time() - start < timeout, "scan did not finish in time"
        time.sleep(0.25)


@pytest.fixture
def scan_pdf(client):
    """scan_pdf(bytes) -> the completed scan, as returned by GET /scans/{id}."""
    def run(data, name="doc.pdf", content_type="application/pdf"):
        response = client.post("/scans/pdf", files={"file": (name, data, content_type)})
        assert response.status_code == 202, response.text
        return wait_done(client, response.json()["scan_id"])
    return run
