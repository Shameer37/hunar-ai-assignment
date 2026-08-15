"""Client for Apollo.io's real People Search API. No mocking, no fallback.

Endpoint and auth confirmed against Apollo's live docs during development:
  POST https://api.apollo.io/api/v1/mixed_people/api_search
  Header: x-api-key

That endpoint costs 0 Apollo credits per their docs, but *access* to it
depends on the calling account's plan -- Apollo returns a 403 with
error_code "API_INACCESSIBLE" for accounts without API access on their
plan. search_people() surfaces that (and every other failure mode) as a
clean HTTPException instead of ever returning fake candidates.
"""

import os

import httpx
from fastapi import HTTPException

APOLLO_SEARCH_URL = "https://api.apollo.io/api/v1/mixed_people/api_search"


def _headers() -> dict:
    api_key = os.environ.get("APOLLO_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="APOLLO_API_KEY is not configured on the server.",
        )
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


def _extract_apollo_message(r: httpx.Response) -> str | None:
    try:
        data = r.json()
    except ValueError:
        return None
    return data.get("error") or data.get("message")


def search_people(payload: dict) -> dict:
    headers = _headers()
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(APOLLO_SEARCH_URL, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Apollo API timed out. Please try again.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Apollo API is currently unreachable.")

    if r.status_code == 401:
        raise HTTPException(
            status_code=502,
            detail="Apollo authentication failed. Check that APOLLO_API_KEY is valid.",
        )
    if r.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="Apollo API rate limit exceeded. Please try again shortly.",
        )
    if r.status_code == 403:
        message = _extract_apollo_message(r) or "Apollo denied access to the People Search API for this account."
        raise HTTPException(status_code=502, detail=f"Apollo API access denied: {message}")
    if r.status_code >= 500:
        raise HTTPException(
            status_code=502,
            detail="Apollo API is currently unavailable. Please try again later.",
        )
    if r.status_code >= 400:
        message = _extract_apollo_message(r) or r.text[:300]
        raise HTTPException(status_code=502, detail=f"Apollo API error: {message}")

    return r.json()
