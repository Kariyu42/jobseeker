from datetime import datetime, timedelta, timezone

from fetcher.dedupe import dedupe
from fetcher.main import merge_history, process, title_ok
from fetcher.normalize import fmt_salary, job, salary_max, strip_html, to_iso
from fetcher.score import score

NOW = datetime(2026, 11, 27, tzinfo=timezone.utc)
CFG = {
    "me": {"home_country": "France", "work_authorization": ["EU"], "timezone_min": -1, "timezone_max": 4, "level": "mid"},
    "skills": {"kubernetes": 3, "terraform": 3, "aws": 2, "python": 1},
    "title_include": ["devops", r"\bsre\b", "platform engineer"],
    "title_exclude": ["sales"],
    "max_age_days": 30,
}


def mk(title="DevOps Engineer", company="Acme", desc="", days=1, loc="Europe", source="t", key=None):
    return job(source=source, key=key or title + company + source, title=title, company=company, url="https://x/" + title,
               posted_at=(NOW - timedelta(days=days)).isoformat(), location=loc, description=desc)


def test_score_rewards_skills_and_freshness():
    good = mk(desc="Kubernetes, Terraform and AWS daily", days=1)
    good["eligibility"] = "eligible"
    weak = mk(title="DevOps Engineer", desc="Windows Server", days=20)
    weak["eligibility"] = "eligible"
    assert score(good, CFG, NOW)[0] > score(weak, CFG, NOW)[0] + 30
    assert set(score(good, CFG, NOW)[1]) == {"kubernetes", "terraform", "aws"}


def test_not_eligible_is_buried():
    j = mk(desc="Kubernetes Terraform AWS")
    j["eligibility"] = "not_eligible"
    assert score(j, CFG, NOW)[0] < 60


def test_title_filter():
    assert title_ok("Senior SRE", CFG)
    assert title_ok("Platform Engineer (Kubernetes)", CFG)
    assert not title_ok("DevOps Sales Lead", CFG)
    assert not title_ok("Frontend Developer", CFG)
    assert not title_ok("Presales engineer", CFG)


def test_dedupe_merges_across_boards():
    a = mk(title="Senior DevOps Engineer (Remote)", company="Acme Inc.", source="remotive")
    b = mk(title="Sr. DevOps Engineer", company="ACME", source="remoteok")
    c = mk(title="Platform Engineer", company="Acme", source="remoteok")
    out = dedupe([a, b, c])
    assert len(out) == 2
    assert sorted(out[0]["sources"]) == ["remoteok", "remotive"]


def test_process_filters_age_and_title():
    raw = [mk(days=1), mk(title="Sales Manager"), mk(title="SRE", days=45)]
    out = process(raw, CFG, NOW)
    assert [j["title"] for j in out] == ["DevOps Engineer"]
    assert out[0]["eligibility"] == "eligible"


def test_merge_history_keeps_first_seen_and_marks_inactive():
    fresh1 = process([mk(days=1), mk(title="SRE", days=2)], CFG, NOW)
    for j in fresh1:
        j.pop("_fulltext")
    prev = {"jobs": merge_history(fresh1, {}, CFG, NOW)}
    later = NOW + timedelta(hours=6)
    fresh2 = process([mk(days=1)], CFG, later)
    merged = {j["title"]: j for j in merge_history(fresh2, prev, CFG, later)}
    assert merged["DevOps Engineer"]["first_seen"] == NOW.isoformat()
    assert merged["DevOps Engineer"]["active"] is True
    assert merged["SRE"]["active"] is False


def test_helpers():
    assert strip_html("<p>Hi&amp;<b>there</b></p>") == "Hi& there"
    assert to_iso(1700000000).startswith("2023-11-14")
    assert to_iso("Mon, 02 Jan 2026 10:00:00 +0000").startswith("2026-01-02")
    assert to_iso("2026-01-02 10:00:00").startswith("2026-01-02T10:00")
    assert fmt_salary(90000, 120000, "USD") == "$90k–$120k"
    assert salary_max("$90k–$120k") == 120000
    assert salary_max("€70.000 - €85.000") == 85000


def test_kept_old_jobs_are_reclassified_with_current_rules():
    old = {"jobs": [{**process([mk(loc="Germany")], CFG, NOW)[0], "where": None, "elig_reason": "stale"}]}
    old["jobs"][0].pop("_fulltext", None)
    old["jobs"][0]["first_seen"] = NOW.isoformat()
    merged = merge_history([], old, CFG, NOW + timedelta(hours=6))
    assert merged[0]["where"] == "must_move" and "Germany" in merged[0]["elig_reason"]
