"""Real Apollo.io People Search integration for Task 2.

No mock fallback: if Apollo is unreachable, denies access, or rate-limits,
search_candidates() raises a clean HTTPException (see api/_apollo.py) that
the frontend displays -- it never silently substitutes fake candidates.
"""

import re

from fastapi import HTTPException

from . import _apollo as apollo

# Lightweight JD -> Apollo search-criteria mapping. Reused from the original
# role-bucket heuristic; now feeds Apollo's person_titles/q_keywords instead
# of just labeling mock data.
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


def _extract_search_criteria(job_description: str) -> tuple[str, list[str], str]:
    """Returns (role_bucket_label, apollo_person_titles, apollo_q_keywords)."""
    text = job_description.lower()
    for role, keywords in _ROLE_KEYWORDS.items():
        if any(k in text for k in keywords):
            return role, _ROLE_TITLES[role], keywords[0]

    words = re.findall(r"[a-zA-Z]{4,}", text)
    fallback_title = words[0].title() if words else "Engineer"
    return fallback_title, [fallback_title], fallback_title


def _full_name(person: dict) -> str:
    first = person.get("first_name") or ""
    last = person.get("last_name") or person.get("last_name_obfuscated") or ""
    name = f"{first} {last}".strip()
    return name or "Unnamed candidate"


def _location(person: dict) -> str:
    parts = [person.get("city"), person.get("state"), person.get("country")]
    return ", ".join(p for p in parts if p) or "Unknown"


def _normalize(person: dict) -> dict:
    org = person.get("organization") or {}
    return {
        "id": f"apollo-{person.get('id')}",
        "apollo_id": person.get("id"),
        "name": _full_name(person),
        "title": person.get("title") or "Unknown title",
        "company": org.get("name") or "Unknown company",
        "location": _location(person),
        "skills": person.get("functions") or person.get("departments") or [],
        "linkedin_url": person.get("linkedin_url"),
        "source": "apollo",
    }


def search_candidates(job_description: str) -> dict:
    if len(job_description.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="Please provide a more complete job description (at least a sentence).",
        )

    role_bucket, person_titles, q_keywords = _extract_search_criteria(job_description)

    payload = {
        "person_titles": person_titles,
        "q_keywords": q_keywords,
        "page": 1,
        "per_page": 10,
    }
    data = apollo.search_people(payload)
    people = data.get("people", [])
    candidates = [_normalize(p) for p in people]

    message = None
    if not candidates:
        message = "No candidates found on Apollo for this job description. Try different wording."

    return {
        "query_role": role_bucket,
        "source": "apollo",
        "total_entries": data.get("total_entries", len(candidates)),
        "message": message,
        "candidates": candidates,
    }
