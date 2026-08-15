import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

HIRING_AGENT_ID = os.environ.get("HIRING_AGENT_ID", "")
REACHOUT_AGENT_ID = os.environ.get("REACHOUT_AGENT_ID", "")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "hunar_key_configured": bool(os.environ.get("HUNAR_API_KEY")),
        "hiring_agent_configured": bool(HIRING_AGENT_ID),
        "reachout_agent_configured": bool(REACHOUT_AGENT_ID),
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


class ReachoutCandidate(BaseModel):
    id: str
    name: str
    mobile_number: str
    title: str = ""


class ReachoutRequest(BaseModel):
    job_description: str
    job_title: str
    company: str = "Our Company"
    candidates: list[ReachoutCandidate]


@app.post("/api/people/reachout")
def people_reachout(req: ReachoutRequest):
    if not REACHOUT_AGENT_ID:
        raise HTTPException(
            status_code=500,
            detail="REACHOUT_AGENT_ID not configured. Run scripts/setup_agents.py first.",
        )
    if not req.candidates:
        raise HTTPException(status_code=422, detail="Select at least one candidate")

    jd_summary = req.job_description[:500]
    results = []
    for c in req.candidates:
        payload = {
            "agent_id": REACHOUT_AGENT_ID,
            "callee_name": c.name,
            "mobile_number": c.mobile_number,
            "custom_data": {
                "job_title": req.job_title,
                "company": req.company,
                "jd_summary": jd_summary,
                "candidate_title": c.title,
            },
            "request_id": c.id,
        }
        try:
            call = hunar.create_call(payload)
            results.append(
                {
                    "candidate_id": c.id,
                    "candidate_name": c.name,
                    "call_id": call.get("id"),
                    "status": call.get("status", "PENDING"),
                }
            )
        except HTTPException as exc:
            results.append(
                {
                    "candidate_id": c.id,
                    "candidate_name": c.name,
                    "error": str(exc.detail),
                }
            )
    return {"results": results}
