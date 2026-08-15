"""Run once (locally) after putting HUNAR_API_KEY in .env:

    python scripts/setup_agents.py

Creates the two Hunar voice agents this app uses and prints the IDs to
paste into .env (HIRING_AGENT_ID, REACHOUT_AGENT_ID) and into the same
variables in your Vercel project's Environment Variables.

This script never prints the API key itself -- only the resulting agent
IDs, which are not secret.
"""

import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

HUNAR_API_KEY = os.environ.get("HUNAR_API_KEY", "")
HUNAR_BASE_URL = "https://api.voice.hunar.ai/external/v1"

HIRING_AGENT = {
    "name": "AI Hiring Screener",
    "language": "ENGLISH",
    "voice_persona": "NEHA",
    "persona_name": "Neha",
    "agent_prompt": (
        "You are Neha, a warm and professional AI recruiting screener calling "
        "on behalf of {company} about a {job_role} opening. Confirm you're "
        "speaking with the right person, briefly explain why you're calling, "
        "then ask about: total years of relevant experience, current role and "
        "notice period, current and expected CTC/salary, and earliest "
        "availability for a follow-up interview. Keep the tone conversational, "
        "one question at a time, and thank them for their time at the end."
    ),
    "objective": (
        "Conduct a brief initial phone screen for the {job_role} role at "
        "{company} and collect enough structured information for a recruiter "
        "to decide whether to move the candidate to the next round."
    ),
    "introduction": (
        "Hi! This is {persona_name}, an AI recruiting assistant calling from "
        "{company} regarding the {job_role} position. Do you have a couple of "
        "minutes to chat?"
    ),
    "result_prompt": (
        "From the conversation, extract: years_of_experience, current_role, "
        "notice_period, current_ctc, expected_ctc, availability, and a short "
        "one-line recommendation on fit."
    ),
    "result_schema": {
        "years_of_experience": "",
        "current_role": "",
        "notice_period": "",
        "current_ctc": "",
        "expected_ctc": "",
        "availability": "",
        "recommendation": "",
    },
}

REACHOUT_AGENT = {
    "name": "Candidate Reachout Agent",
    "language": "ENGLISH",
    "voice_persona": "ROY",
    "persona_name": "Roy",
    "agent_prompt": (
        "You are Roy, a friendly AI recruiting assistant calling a potential "
        "candidate about a {job_title} opening at {company}. Here is a short "
        "summary of the role: {jd_summary}. Introduce yourself, briefly "
        "describe the role, and gauge interest. If they're interested, ask "
        "about their current notice period and expected compensation, and "
        "whether they'd be open to a follow-up call with the recruiter. Be "
        "respectful if they're not interested or want to be called back later."
    ),
    "objective": (
        "Gauge interest from a sourced candidate for the {job_title} role at "
        "{company} and capture enough information for a recruiter to "
        "prioritize follow-up."
    ),
    "introduction": (
        "Hi! This is {persona_name}, an AI recruiting assistant calling on "
        "behalf of {company} about a {job_title} opportunity we think could "
        "be a great fit for you. Is now an okay time for a quick chat?"
    ),
    "result_prompt": (
        "From the conversation, extract: interested (Yes/No/Maybe), "
        "notice_period, expected_ctc, best_callback_time, and a short summary "
        "of how the conversation went."
    ),
    "result_schema": {
        "interested": "",
        "notice_period": "",
        "expected_ctc": "",
        "best_callback_time": "",
        "summary": "",
    },
}


def create_agent(payload: dict) -> str:
    with httpx.Client(timeout=30) as client:
        r = client.post(
            f"{HUNAR_BASE_URL}/agents/",
            headers={"X-API-Key": HUNAR_API_KEY, "Content-Type": "application/json"},
            json=payload,
        )
    if r.status_code >= 400:
        print(f"Failed to create agent '{payload['name']}': {r.status_code} {r.text}")
        sys.exit(1)
    data = r.json()
    print(f"Created agent '{payload['name']}' -> id={data['id']}")
    return data["id"]


def main():
    if not HUNAR_API_KEY:
        print("HUNAR_API_KEY is not set. Put it in .env first (see .env.example).")
        sys.exit(1)

    hiring_id = create_agent(HIRING_AGENT)
    reachout_id = create_agent(REACHOUT_AGENT)

    print("\nAdd these to .env and to your Vercel project's Environment Variables:\n")
    print(f"HIRING_AGENT_ID={hiring_id}")
    print(f"REACHOUT_AGENT_ID={reachout_id}")


if __name__ == "__main__":
    main()
