"""Arbeitnow: Europe-heavy board. Only remote postings are kept."""
from ..normalize import job

URL = "https://www.arbeitnow.com/api/job-board-api?page={page}"
PAGES = 4


def parse(data) -> list[dict]:
    out = []
    for r in data.get("data", []):
        if not r.get("remote"):
            continue
        loc = r.get("location", "")
        out.append(job(
            source="arbeitnow",
            key=r.get("slug"),
            title=r.get("title", ""),
            company=r.get("company_name", ""),
            url=r.get("url", ""),
            posted_at=r.get("created_at"),
            tags=r.get("tags", []) + r.get("job_types", []),
            # Arbeitnow remote roles are typically remote within the listed country
            location=loc,
            description=r.get("description", ""),
            job_type=", ".join(r.get("job_types", [])),
        ))
    return out


def fetch(http) -> list[dict]:
    out = []
    for page in range(1, PAGES + 1):
        data = http.get_json(URL.format(page=page))
        out += parse(data)
        if not (data.get("links") or {}).get("next"):
            break
    return out
