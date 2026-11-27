from ..normalize import fmt_salary, job

URL = "https://remoteok.com/api"


def parse(data) -> list[dict]:
    out = []
    for r in data:
        if not isinstance(r, dict) or not r.get("position"):
            continue  # first element is a legal notice
        out.append(job(
            source="remoteok",
            key=r.get("id") or r.get("slug"),
            title=r["position"],
            company=r.get("company", ""),
            url=r.get("url") or r.get("apply_url") or f"https://remoteok.com/remote-jobs/{r.get('slug', '')}",
            posted_at=r.get("epoch") or r.get("date"),
            tags=r.get("tags"),
            salary=fmt_salary(r.get("salary_min"), r.get("salary_max"), "USD"),
            location=r.get("location", ""),
            description=r.get("description", ""),
        ))
    return out


def fetch(http) -> list[dict]:
    return parse(http.get_json(URL))
