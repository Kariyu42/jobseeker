from ..normalize import fmt_salary, job

URL = "https://jobicy.com/api/v2/remote-jobs?count=100&tag={tag}"
TAGS = ["devops", "sre", "kubernetes", "cloud"]


def parse(data) -> list[dict]:
    out = []
    for r in data.get("jobs", []):
        jt = r.get("jobType")
        out.append(job(
            source="jobicy",
            key=r.get("id") or r.get("url"),
            title=r.get("jobTitle", ""),
            company=r.get("companyName", ""),
            url=r.get("url", ""),
            posted_at=r.get("pubDate"),
            tags=(r.get("jobIndustry") or []) + ([r["jobLevel"]] if r.get("jobLevel") else []),
            salary=fmt_salary(r.get("annualSalaryMin") or r.get("salaryMin"),
                              r.get("annualSalaryMax") or r.get("salaryMax"), r.get("salaryCurrency")),
            location=r.get("jobGeo", ""),
            description=r.get("jobDescription") or r.get("jobExcerpt", ""),
            job_type=", ".join(jt) if isinstance(jt, list) else (jt or ""),
        ))
    return out


def fetch(http) -> list[dict]:
    out = []
    for tag in TAGS:
        out += parse(http.get_json(URL.format(tag=tag)))
    return out
