"""Client for People Data Labs' real Person Search API. No mocking, no fallback.

Endpoint and auth confirmed against PDL's live docs during development:
  POST https://api.peopledatalabs.com/v5/person/search
  Header: X-Api-Key
  Body: {"query": <Elasticsearch bool query>, "size": <int>}

PDL profiles can include mobile_phone / phone_numbers / work_email. This
client (and _people_search.py's normalizer) deliberately never reads or
forwards those fields to the frontend -- voice reachout stays a separate,
explicit, human-confirmed flow (see api/index.py ReachoutRequest), the same
safety design used across the app for any people-search source. search_people() surfaces every PDL
failure mode as a clean HTTPException instead of ever returning fake
candidates.
"""

import os

import httpx
from fastapi import HTTPException

PDL_SEARCH_URL = "https://api.peopledatalabs.com/v5/person/search"


def _headers() -> dict:
    api_key = os.environ.get("PDL_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="PDL_API_KEY is not configured on the server.",
        )
    return {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }


def _extract_pdl_message(r: httpx.Response) -> str | None:
    try:
        data = r.json()
    except ValueError:
        return None
    error = data.get("error")
    if isinstance(error, dict):
        return error.get("message") or error.get("type")
    return None


def search_people(payload: dict) -> dict:
    headers = _headers()
    try:
        with httpx.Client(timeout=20) as client:
            r = client.post(PDL_SEARCH_URL, headers=headers, json=payload)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="PDL API timed out. Please try again.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="PDL API is currently unreachable.")

    if r.status_code == 401:
        raise HTTPException(
            status_code=502,
            detail="PDL authentication failed. Check that PDL_API_KEY is valid.",
        )
    if r.status_code == 402:
        message = _extract_pdl_message(r) or "PDL denied access for this account's plan (insufficient credits or permissions)."
        raise HTTPException(status_code=502, detail=f"PDL API access denied: {message}")
    if r.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="PDL API rate limit exceeded. Please try again shortly.",
        )
    if r.status_code >= 500:
        raise HTTPException(
            status_code=502,
            detail="PDL API is currently unavailable. Please try again later.",
        )
    if r.status_code >= 400:
        message = _extract_pdl_message(r) or r.text[:300]
        raise HTTPException(status_code=502, detail=f"PDL API error: {message}")

    return r.json()
