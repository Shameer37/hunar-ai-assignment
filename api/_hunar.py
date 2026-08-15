"""Thin client for the Hunar Voice Agents API.

Docs: https://api.voice.hunar.ai/docs/external/
Auth: X-API-Key header. The key itself is only ever read from the
HUNAR_API_KEY environment variable -- never hardcode it here.
"""

import os

import httpx
from fastapi import HTTPException

HUNAR_BASE_URL = "https://api.voice.hunar.ai/external/v1"


def _headers() -> dict:
    api_key = os.environ.get("HUNAR_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="HUNAR_API_KEY is not configured on the server.",
        )
    return {"X-API-Key": api_key, "Content-Type": "application/json"}


def _raise_for_status(r: httpx.Response) -> None:
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)


def create_agent(payload: dict) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.post(f"{HUNAR_BASE_URL}/agents/", headers=_headers(), json=payload)
    _raise_for_status(r)
    return r.json()


def list_agents(params: dict | None = None) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{HUNAR_BASE_URL}/agents/", headers=_headers(), params=params or {})
    _raise_for_status(r)
    return r.json()


def create_call(payload: dict) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.post(f"{HUNAR_BASE_URL}/calls/", headers=_headers(), json=payload)
    _raise_for_status(r)
    return r.json()


def get_call(call_id: str) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{HUNAR_BASE_URL}/calls/{call_id}/", headers=_headers())
    _raise_for_status(r)
    return r.json()


def list_calls(params: dict | None = None) -> dict:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{HUNAR_BASE_URL}/calls/", headers=_headers(), params=params or {})
    _raise_for_status(r)
    return r.json()
