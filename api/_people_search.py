"""Real People Data Labs (PDL) Person Search integration for Task 2.

No mock fallback: if PDL is unreachable, denies access, or rate-limits,
search_candidates() raises a clean HTTPException (see api/_pdl.py) that the
frontend displays -- it never silently substitutes fake candidates.
"""

import re

from fastapi import HTTPException

from . import _pdl as pdl

# Lightweight JD -> PDL search-criteria mapping: turns a free-text JD into a
# small set of job_title phrases we match against with an Elasticsearch
# "should" (OR) query.
_ROLE_TITLES = {
    "backend": ["Backend Engineer", "Software Engineer", "Backend Developer"],
    "frontend": ["Frontend Engineer", "Frontend Developer", "UI Engineer"],
    "full stack": ["Full Stack Engineer", "Full Stack Developer"],
    "ml": ["Machine Learning Engineer", "ML Engineer", "Data Scientist", "AI Engineer"],
    "devops": ["DevOps Engineer", "Site Reliability Engineer", "Infrastructure Engineer"],
    "product": ["Product Manager", "Product Owner"],
}

_ROLE_KEYWORDS = {
    "backend": ["backend", "server-side", "api developer", "django", "fastapi"],
    "frontend": ["frontend", "react", "next.js", "ui developer"],
    "full stack": ["full stack", "fullstack", "full-stack"],
    "ml": ["machine learning", "ml engineer", "llm", "ai engineer", "data scientist"],
    "devops": ["devops", "sre", "infrastructure", "kubernetes"],
    "product": ["product manager", "product owner"],
}


def _extract_search_criteria(job_description: str) -> tuple[str, list[str]]:
    """Returns (role_bucket_label, job_title phrases to search)."""
    text = job_description.lower()
    for role, keywords in _ROLE_KEYWORDS.items():
        if any(k in text for k in keywords):
            return role, _ROLE_TITLES[role]

    words = re.findall(r"[a-zA-Z]{4,}", text)
    fallback_title = words[0].title() if words else "Engineer"
    return fallback_title, [fallback_title]


# PDL returns the literal boolean `true` (never a string) for some fields
# -- notably location_* -- when that field exists but is redacted for the
# calling account's plan tier. Treat anything that isn't a real, non-empty
# string as absent rather than crashing or showing "True".
def _str(value) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _full_name(person: dict) -> str:
    name = _str(person.get("full_name"))
    if name:
        return name.title()
    first = _str(person.get("first_name")) or ""
    last = _str(person.get("last_name")) or ""
    combined = f"{first} {last}".strip()
    return combined.title() if combined else "Unnamed candidate"


def _location(person: dict) -> str:
    name = _str(person.get("location_name"))
    if name:
        return name.title()
    parts = [
        _str(person.get("location_locality")),
        _str(person.get("location_region")),
        _str(person.get("location_country")),
    ]
    joined = ", ".join(p for p in parts if p)
    return joined.title() if joined else "Unknown"


def _linkedin_url(person: dict) -> str | None:
    url = _str(person.get("linkedin_url"))
    if url and not url.startswith("http"):
        return f"https://{url}"
    return url


def _normalize(person: dict) -> dict:
    # Deliberately never reads mobile_phone / phone_numbers / work_email,
    # even though PDL profiles can include them -- see api/_pdl.py.
    return {
        "id": f"pdl-{person.get('id')}",
        "pdl_id": person.get("id"),
        "name": _full_name(person),
        "title": (_str(person.get("job_title")) or "Unknown title").title(),
        "company": (_str(person.get("job_company_name")) or "Unknown company").title(),
        "location": _location(person),
        "skills": [s for s in (person.get("skills") or []) if _str(s)][:8],
        "linkedin_url": _linkedin_url(person),
        "source": "pdl",
    }


def search_candidates(job_description: str) -> dict:
    if len(job_description.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="Please provide a more complete job description (at least a sentence).",
        )

    role_bucket, job_titles = _extract_search_criteria(job_description)

    payload = {
        "query": {
            "bool": {
                "should": [{"match": {"job_title": title}} for title in job_titles],
            }
        },
        "size": 10,
    }
    data = pdl.search_people(payload)
    people = data.get("data", [])
    candidates = [_normalize(p) for p in people]

    message = None
    if not candidates:
        message = "No candidates found on PDL for this job description. Try different wording."

    return {
        "query_role": role_bucket,
        "source": "pdl",
        "total_entries": data.get("total", len(candidates)),
        "message": message,
        "candidates": candidates,
    }
