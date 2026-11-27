"""Arbeitnow: Europe-heavy board. Only remote postings are kept."""
from ..location import find_countries
from ..normalize import job

URL = "https://www.arbeitnow.com/api/job-board-api?page={page}"
PAGES = 4


def parse(data) -> list[dict]:
    out = []
    for r in data.get("data", []):
        if not r.get("remote"):
            continue
        loc = (r.get("location") or "").strip()
        # Arbeitnow is a German board: "Homeoffice"/blank remote roles are remote-in-Germany.
        if not find_countries(loc):
            loc = f"Germany ({loc})" if loc else "Germany"
        out.append(job(
            source="arbeitnow",
            key=r.get("slug"),
            title=r.get("title", ""),
            company=r.get("company_name", ""),
            url=r.get("url", ""),
            posted_at=r.get("created_at"),
            tags=r.get("tags", []) + r.get("job_types", []),
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
