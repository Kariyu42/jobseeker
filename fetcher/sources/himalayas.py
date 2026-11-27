"""Himalayas: has structured location + timezone restrictions."""
from ..normalize import fmt_salary, job

SEARCH = "https://himalayas.app/jobs/api/search?q={q}&page={page}"
QUERIES = ["devops", "site reliability", "platform engineer", "infrastructure engineer", "cloud engineer"]
PAGES = 2


def parse(data) -> list[dict]:
    out = []
    for r in data.get("jobs", []):
        locs = r.get("locationRestrictions") or []
        locs = [l.get("name", l) if isinstance(l, dict) else l for l in locs]
        tzs = [t for t in (r.get("timezoneRestrictions") or []) if isinstance(t, (int, float))]
        out.append(job(
            source="himalayas",
            key=r.get("guid") or r.get("applicationLink") or r.get("title"),
            title=r.get("title", ""),
            company=r.get("companyName", ""),
            url=r.get("applicationLink") or r.get("guid", ""),
            posted_at=r.get("pubDate"),
            tags=(r.get("categories") or []) + ([r["seniority"]] if isinstance(r.get("seniority"), str) else []),
            salary=fmt_salary(r.get("minSalary"), r.get("maxSalary"), r.get("currency")),
            location=", ".join(locs) if locs else "Worldwide",
            location_list=locs,
            timezones=tzs,
            description=r.get("description") or r.get("excerpt", ""),
            job_type=r.get("employmentType", ""),
        ))
    return out


def fetch(http) -> list[dict]:
    out = []
    for q in QUERIES:
        for page in range(1, PAGES + 1):
            batch = parse(http.get_json(SEARCH.format(q=q.replace(" ", "+"), page=page)))
            out += batch
            if len(batch) < 20:
                break
    return out
