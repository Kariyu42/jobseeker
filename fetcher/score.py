"""Keyword fit score (0-100). Free, no AI/API needed."""
from __future__ import annotations

import re
from datetime import datetime, timezone

CORE_TITLE = re.compile(r"devops|devsecops|\bsre\b|site reliability|platform engineer", re.I)
ADJ_TITLE = re.compile(r"cloud|infra|kubernetes|reliability|mlops|observability|release|build", re.I)
SENIOR_RE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|head|architect|director)\b", re.I)
JUNIOR_RE = re.compile(r"\b(junior|jr\.?|graduate|entry|associate|intern|trainee|apprentice)\b", re.I)

LEVELS = {"junior": 0, "mid": 1, "senior": 2, "lead": 3}


def _skill_re(skill: str) -> re.Pattern:
    return re.compile(rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])", re.I)


def matched_skills(job: dict, skills: dict) -> list[str]:
    hay = " ".join([job["title"], " ".join(job.get("tags", [])), job.get("_fulltext") or job.get("description", "")])
    return [s for s in skills if _skill_re(s).search(hay)]


def job_level(title: str) -> int:
    if JUNIOR_RE.search(title):
        return 0
    if re.search(r"\b(staff|principal|lead|head|director)\b", title, re.I):
        return 3
    if SENIOR_RE.search(title):
        return 2
    return 1


def age_days(job: dict, now: datetime | None = None) -> float | None:
    if not job.get("posted_at"):
        return None
    now = now or datetime.now(timezone.utc)
    return (now - datetime.fromisoformat(job["posted_at"])).total_seconds() / 86400


def score(job: dict, cfg: dict, now: datetime | None = None) -> tuple[int, list[str]]:
    skills = cfg.get("skills", {})
    hits = matched_skills(job, skills)
    total_w = sum(skills.values()) or 1
    title_hits = [s for s in hits if _skill_re(s).search(job["title"])]
    # 45 pts: weighted skill coverage, saturating (you rarely match everything)
    w = sum(skills[s] for s in hits) + sum(skills[s] for s in title_hits)
    pts = min(45, round(45 * w / max(8, total_w * 0.35)))

    # 20 pts: title relevance
    if CORE_TITLE.search(job["title"]):
        pts += 20
    elif ADJ_TITLE.search(job["title"]):
        pts += 14
    else:
        pts += 7

    # 10 pts: seniority fit
    want = LEVELS.get(str(cfg.get("me", {}).get("level", "mid")).lower(), 1)
    diff = abs(job_level(job["title"]) - want)
    pts += {0: 10, 1: 5}.get(diff, 0)

    # 15 pts: freshness (applying early is the #1 response-rate lever)
    age = age_days(job, now)
    if age is None:
        pts += 5
    elif age <= 2:
        pts += 15
    elif age <= 7:
        pts += 10
    elif age <= 14:
        pts += 5

    # eligibility
    elig = job.get("eligibility")
    pts += {"eligible": 10, "unclear": 0, "not_eligible": -40}.get(elig, 0)
    if elig == "eligible" and job.get("where") == "must_move":
        pts -= 5  # you can apply, but only by relocating: rank below from-home jobs
    return max(0, min(100, pts)), hits
