from ..normalize import job

URL = "https://www.workingnomads.com/api/exposed_jobs/"


def parse(data) -> list[dict]:
    out = []
    for r in data:
        cat = (r.get("category_name") or "").lower()
        if cat and not any(k in cat for k in ("devops", "sysadmin", "system", "development")):
            continue
        out.append(job(
            source="workingnomads",
            key=r.get("url"),
            title=r.get("title", ""),
            company=r.get("company_name", ""),
            url=r.get("url", ""),
            posted_at=r.get("pub_date"),
            tags=r.get("tags", ""),
            location=r.get("location", ""),
            description=r.get("description", ""),
        ))
    return out


def fetch(http) -> list[dict]:
    return parse(http.get_json(URL))
