"""People-search provider.

This currently returns realistic mock candidates so the JD -> candidates ->
voice-reachout -> dashboard flow can be demoed end to end without a live
People Data Labs / Apollo.io / Proxycurl / Coresignal key.

To go live: implement `search_candidates(job_description)` to call your
chosen provider (e.g. PDL's Person Search API) using keywords extracted from
the JD, and return the same shape this mock returns -- nothing else in the
app needs to change.
"""

import re

_MOCK_POOL = [
    {
        "id": "cand-1",
        "name": "Ananya Rao",
        "title": "Senior Backend Engineer",
        "company": "Zylker Cloud",
        "location": "Bengaluru, India",
        "mobile_number": "+919876500001",
        "email": "ananya.rao@example.com",
        "skills": ["Python", "FastAPI", "PostgreSQL", "AWS"],
    },
    {
        "id": "cand-2",
        "name": "Rohan Mehta",
        "title": "Full Stack Developer",
        "company": "Initech Labs",
        "location": "Pune, India",
        "mobile_number": "+919876500002",
        "email": "rohan.mehta@example.com",
        "skills": ["TypeScript", "React", "Next.js", "Node.js"],
    },
    {
        "id": "cand-3",
        "name": "Sara Iqbal",
        "title": "Machine Learning Engineer",
        "company": "Northwind Analytics",
        "location": "Hyderabad, India",
        "mobile_number": "+919876500003",
        "email": "sara.iqbal@example.com",
        "skills": ["PyTorch", "LLMs", "MLOps", "Python"],
    },
    {
        "id": "cand-4",
        "name": "Vikram Singh",
        "title": "DevOps Engineer",
        "company": "Globex Systems",
        "location": "Gurugram, India",
        "mobile_number": "+919876500004",
        "email": "vikram.singh@example.com",
        "skills": ["Kubernetes", "Terraform", "CI/CD", "AWS"],
    },
    {
        "id": "cand-5",
        "name": "Priya Nair",
        "title": "Product Manager",
        "company": "Soylent Corp",
        "location": "Chennai, India",
        "mobile_number": "+919876500005",
        "email": "priya.nair@example.com",
        "skills": ["Roadmapping", "SQL", "A/B Testing", "Agile"],
    },
]

_ROLE_KEYWORDS = {
    "backend": ["backend", "server-side", "api developer", "django", "fastapi"],
    "frontend": ["frontend", "react", "next.js", "ui developer"],
    "full stack": ["full stack", "fullstack", "full-stack"],
    "ml": ["machine learning", "ml engineer", "llm", "ai engineer", "data scientist"],
    "devops": ["devops", "sre", "infrastructure", "kubernetes"],
    "product": ["product manager", "product owner"],
}


def _guess_role(job_description: str) -> str:
    text = job_description.lower()
    for role, keywords in _ROLE_KEYWORDS.items():
        if any(k in text for k in keywords):
            return role
    words = re.findall(r"[a-zA-Z]{4,}", text)
    return words[0].title() if words else "General"


def search_candidates(job_description: str) -> dict:
    role_guess = _guess_role(job_description)
    return {
        "query_role": role_guess,
        "source": "mock",
        "note": (
            "Demo data. Swap search_candidates() in api/_people_search.py for a "
            "live PDL / Apollo.io / Proxycurl / Coresignal call to go live -- "
            "response shape is already compatible."
        ),
        "candidates": _MOCK_POOL,
    }
