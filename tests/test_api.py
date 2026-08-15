"""Smoke tests for the FastAPI backend.

None of these hit a real network -- Hunar's create_call and PDL's
search_people are mocked at the module they're defined in (api._hunar,
api._pdl), since both api/index.py and api/_people_search.py hold a
reference to those modules (`from . import _hunar as hunar`), so patching
the module attribute is what actually intercepts the call. No real API
credits are spent running this suite.

Run with: pip install -r requirements-dev.txt && pytest
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from api.index import app

client = TestClient(app)

VALID_PHONE = "+919876543210"


def _screen_payload(**overrides):
    payload = {
        "candidate_name": "Jane Doe",
        "mobile_number": VALID_PHONE,
        "job_role": "Backend Engineer",
        "consent_confirmed": True,
    }
    payload.update(overrides)
    return payload


def _reachout_payload(**overrides):
    payload = {
        "candidate_id": "pdl-abc123",
        "candidate_name": "Jane Doe",
        "phone_number": VALID_PHONE,
        "consent_confirmed": True,
    }
    payload.update(overrides)
    return payload


def test_health_reports_all_expected_keys():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert set(body) == {
        "status",
        "hunar_key_configured",
        "hiring_agent_configured",
        "reachout_agent_configured",
        "pdl_key_configured",
    }


def test_screening_rejects_missing_consent():
    r = client.post(
        "/api/hiring/screen",
        json=_screen_payload(consent_confirmed=False),
        headers={"x-forwarded-for": "10.0.0.1"},
    )
    assert r.status_code == 422
    assert "consent" in r.json()["detail"].lower() or "agreed" in r.json()["detail"].lower()


def test_screening_rejects_malformed_phone():
    r = client.post(
        "/api/hiring/screen",
        json=_screen_payload(mobile_number="not-a-phone-number"),
        headers={"x-forwarded-for": "10.0.0.2"},
    )
    assert r.status_code == 422
    assert "phone" in r.json()["detail"].lower()


def test_screening_places_call_when_valid(monkeypatch):
    monkeypatch.setattr("api.index.HIRING_AGENT_ID", "agent-hiring-test")
    with patch("api._hunar.create_call", return_value={"id": "call-1", "status": "PENDING"}) as mock_call:
        r = client.post(
            "/api/hiring/screen",
            json=_screen_payload(),
            headers={"x-forwarded-for": "10.0.0.3"},
        )
    assert r.status_code == 200
    assert r.json()["id"] == "call-1"
    mock_call.assert_called_once()


def test_screening_requires_agent_configured(monkeypatch):
    monkeypatch.setattr("api.index.HIRING_AGENT_ID", "")
    r = client.post(
        "/api/hiring/screen",
        json=_screen_payload(),
        headers={"x-forwarded-for": "10.0.0.4"},
    )
    assert r.status_code == 500


def test_screening_rate_limited_after_five_requests(monkeypatch):
    monkeypatch.setattr("api.index.HIRING_AGENT_ID", "agent-hiring-test")
    ip = "10.0.0.5"
    with patch("api._hunar.create_call", return_value={"id": "call-x", "status": "PENDING"}):
        for _ in range(5):
            r = client.post(
                "/api/hiring/screen",
                json=_screen_payload(),
                headers={"x-forwarded-for": ip},
            )
            assert r.status_code == 200
        blocked = client.post(
            "/api/hiring/screen",
            json=_screen_payload(),
            headers={"x-forwarded-for": ip},
        )
    assert blocked.status_code == 429


def test_people_search_rejects_too_short_jd():
    r = client.post(
        "/api/people/search",
        json={"job_description": "hi"},
        headers={"x-forwarded-for": "10.0.1.1"},
    )
    assert r.status_code == 422


def test_people_search_normalizes_real_shaped_pdl_response():
    fake_pdl_response = {
        "data": [
            {
                "id": "abc123",
                "full_name": "test person",
                "job_title": "backend engineer",
                "job_company_name": "acme corp",
                # PDL sends the literal bool `True` (not a string) for
                # fields redacted on this plan tier -- the normalizer must
                # not crash on this, and must not surface "True" as a value.
                "location_name": True,
                "location_locality": True,
                "location_region": True,
                "location_country": "united states",
                "skills": True,
                "linkedin_url": "linkedin.com/in/testperson",
            }
        ],
        "total": 1,
    }
    with patch("api._pdl.search_people", return_value=fake_pdl_response):
        r = client.post(
            "/api/people/search",
            json={"job_description": "Looking for a Backend Engineer with Python experience."},
            headers={"x-forwarded-for": "10.0.1.2"},
        )
    assert r.status_code == 200
    candidate = r.json()["candidates"][0]
    assert candidate["name"] == "Test Person"
    assert candidate["location"] == "United States"
    assert candidate["skills"] == []
    assert "mobile_phone" not in candidate
    assert "phone_numbers" not in candidate
    assert "work_email" not in candidate


def test_reachout_rejects_missing_consent():
    r = client.post(
        "/api/people/reachout",
        json=_reachout_payload(consent_confirmed=False),
        headers={"x-forwarded-for": "10.0.2.1"},
    )
    assert r.status_code == 422


def test_reachout_rejects_malformed_phone():
    r = client.post(
        "/api/people/reachout",
        json=_reachout_payload(phone_number="12345"),
        headers={"x-forwarded-for": "10.0.2.2"},
    )
    assert r.status_code == 422


def test_reachout_places_call_then_dedupes_immediate_retry(monkeypatch):
    monkeypatch.setattr("api.index.REACHOUT_AGENT_ID", "agent-reachout-test")
    with patch("api._hunar.create_call", return_value={"id": "call-2", "status": "PENDING"}):
        first = client.post(
            "/api/people/reachout",
            json=_reachout_payload(candidate_id="pdl-dedupe-test"),
            headers={"x-forwarded-for": "10.0.2.3"},
        )
        second = client.post(
            "/api/people/reachout",
            json=_reachout_payload(candidate_id="pdl-dedupe-test"),
            headers={"x-forwarded-for": "10.0.2.3"},
        )
    assert first.status_code == 200
    assert second.status_code == 409
