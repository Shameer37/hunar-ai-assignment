import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import _hunar as hunar
from ._people_search import search_candidates

# Local dev convenience only -- on Vercel, env vars come from the project's
# Environment Variables settings instead, and this is a no-op there.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="Hunar AI Hiring Assignment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Explicit handlers so every error path returns JSON, regardless of how
# Vercel's Python runtime wraps this ASGI app -- observed in production
# that an HTTPException raised deep in a call chain (after a real outbound
# HTTP request) could otherwise surface as a bare "Internal Server Error"
# plain-text response instead of Starlette's normal JSON error body.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."},
    )

HIRING_AGENT_ID = os.environ.get("HIRING_AGENT_ID", "")
REACHOUT_AGENT_ID = os.environ.get("REACHOUT_AGENT_ID", "")

# Best-effort duplicate-reachout guard. Deliberately in-memory (not a
# database -- see README) so it only protects within a single warm
# serverless instance; the real, reliable guard is client-side (the
# frontend disables "Reach Out" once a candidate has an active/completed
# call, persisted in localStorage).
_recent_reachouts: dict[str, float] = {}
_DUPLICATE_WINDOW_SECONDS = 60


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "hunar_key_configured": bool(os.environ.get("HUNAR_API_KEY")),
        "hiring_agent_configured": bool(HIRING_AGENT_ID),
        "reachout_agent_configured": bool(REACHOUT_AGENT_ID),
        "apollo_key_configured": bool(os.environ.get("APOLLO_API_KEY")),
    }


# ---------------------------------------------------------------------------
# Task 1: AI Hiring Assistant (voice screening call)
# ---------------------------------------------------------------------------


class ScreeningRequest(BaseModel):
    candidate_name: str
    mobile_number: str = Field(..., description="E.164 format, e.g. +919876543210")
    job_role: str
    company: str = "Our Company"


@app.post("/api/hiring/screen")
def start_screening_call(req: ScreeningRequest):
    if not HIRING_AGENT_ID:
        raise HTTPException(
            status_code=500,
            detail="HIRING_AGENT_ID not configured. Run scripts/setup_agents.py first.",
        )
    payload = {
        "agent_id": HIRING_AGENT_ID,
        "callee_name": req.candidate_name,
        "mobile_number": req.mobile_number,
        "custom_data": {
            "job_role": req.job_role,
            "company": req.company,
        },
    }
    return hunar.create_call(payload)


# ---------------------------------------------------------------------------
# Shared: poll a call's status / transcript / structured result
# ---------------------------------------------------------------------------


@app.get("/api/calls/{call_id}")
def get_call(call_id: str):
    return hunar.get_call(call_id)


# ---------------------------------------------------------------------------
# Task 2: People Search & Reachout
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    job_description: str


@app.post("/api/people/search")
def people_search(req: SearchRequest):
    if not req.job_description.strip():
        raise HTTPException(status_code=422, detail="job_description is required")
    return search_candidates(req.job_description)


# Voice reachout is ALWAYS single-candidate and requires an explicit,
# human-confirmed test/consenting phone number. It deliberately does not
# accept a candidate's Apollo-sourced phone/contact data at all -- Apollo's
# search response doesn't even include one (see api/_people_search.py) -- so
# there is no code path that can end up auto-dialing a number obtained from
# people-search results.
_PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class ReachoutRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1)
    candidate_name: str = Field(..., min_length=1)
    candidate_title: str = ""
    job_description: str = ""
    job_title: str = "Open Role"
    company: str = "Our Company"
    phone_number: str = Field(..., min_length=1)
    consent_confirmed: bool


@app.post("/api/people/reachout")
def people_reachout(req: ReachoutRequest):
    if not REACHOUT_AGENT_ID:
        raise HTTPException(
            status_code=500,
            detail="REACHOUT_AGENT_ID not configured. Run scripts/setup_agents.py first.",
        )
    if not req.consent_confirmed:
        raise HTTPException(
            status_code=422,
            detail="You must confirm this is a test/consenting number before starting the call.",
        )
    phone = req.phone_number.strip()
    if not _PHONE_RE.match(phone):
        raise HTTPException(
            status_code=422,
            detail="Enter a valid phone number in E.164 format, e.g. +919876543210.",
        )

    dedupe_key = f"{req.candidate_id}:{phone}"
    now = time.time()
    last_attempt = _recent_reachouts.get(dedupe_key)
    if last_attempt and (now - last_attempt) < _DUPLICATE_WINDOW_SECONDS:
        raise HTTPException(
            status_code=409,
            detail="A reachout call for this candidate and number was just started. Please wait a minute before retrying.",
        )

    payload = {
        "agent_id": REACHOUT_AGENT_ID,
        "callee_name": req.candidate_name,
        "mobile_number": phone,
        "custom_data": {
            "job_title": req.job_title,
            "company": req.company,
            "jd_summary": req.job_description[:500],
            "candidate_title": req.candidate_title,
        },
        "request_id": f"{req.candidate_id}-{int(now)}",
    }
    call = hunar.create_call(payload)
    _recent_reachouts[dedupe_key] = now

    return {
        "candidate_id": req.candidate_id,
        "candidate_name": req.candidate_name,
        "call_id": call.get("id"),
        "status": call.get("status", "PENDING"),
    }
