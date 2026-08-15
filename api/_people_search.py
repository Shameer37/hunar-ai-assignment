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
    "full stack": ["Full Stack Engineer", "Full Stack Developer"],
    "ml": ["Machine Learning Engineer", "ML Engineer", "Data Scientist", "AI Engineer"],
    "devops": ["DevOps Engineer", "Site Reliability Engineer", "Infrastructure Engineer"],
    "product": ["Product Manager", "Product Owner"],
    "backend": ["Backend Engineer", "Software Engineer", "Backend Developer"],
    "frontend": ["Frontend Engineer", "Frontend Developer", "UI Engineer"],
}

# Checked in this order (dict order below), NOT alphabetically or by
# insertion convenience: "full stack" must be checked before "backend" /
# "frontend" because a full-stack JD almost always also contains the words
# "backend" and "frontend" (e.g. "comfortable with both backend and
# frontend"), which would otherwise false-match the more generic bucket
# first and misclassify the role. General rule: more specific/compound
# buckets first, generic single-discipline buckets last.
_ROLE_KEYWORDS = {
    "full stack": ["full stack", "fullstack", "full-stack"],
    "ml": ["machine learning", "ml engineer", "llm", "ai engineer", "data scientist"],
    "devops": ["devops", "sre", "infrastructure", "kubernetes"],
    "product": ["product manager", "product owner"],
    "backend": ["backend", "server-side", "api developer", "django", "fastapi"],
    "frontend": ["frontend", "react", "next.js", "ui developer"],
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


def _skills(person: dict) -> list[str]:
    # Like location_*, `skills` can come back as the redaction placeholder
    # `True` (a bool, not a list) instead of being omitted -- `True or []`
    # would evaluate to `True`, and iterating a bool raises TypeError.
    raw = person.get("skills")
    if not isinstance(raw, list):
        return []
    return [s for s in raw if _str(s)][:8]


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
        "skills": _skills(person),
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
        # Kept small deliberately: PDL's `search` credit pool is a separate,
        # much smaller bucket than the enrichment/purchased pool, and a
        # request for more results than remain in that pool is rejected
        # outright (0 partial results) rather than truncated -- see the
        # account-capacity note in README.
        "size": 5,
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
