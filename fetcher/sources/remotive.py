from ..normalize import job

URL = "https://remotive.com/api/remote-jobs?category=devops"


def parse(data) -> list[dict]:
    return [
        job(
            source="remotive",
            key=r.get("id"),
            title=r.get("title", ""),
            company=r.get("company_name", ""),
            url=r.get("url", ""),
            posted_at=r.get("publication_date"),
            tags=r.get("tags"),
            salary=r.get("salary", ""),
            location=r.get("candidate_required_location", ""),
            description=r.get("description", ""),
            job_type=r.get("job_type", ""),
        )
        for r in data.get("jobs", [])
    ]


def fetch(http) -> list[dict]:
    return parse(http.get_json(URL))
