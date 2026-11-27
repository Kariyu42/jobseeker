"""Merge the same job posted on several boards."""
from __future__ import annotations

import re

_NOISE = {"remote", "fully", "full", "time", "contract", "m", "f", "d", "w", "h", "x", "100", "anywhere", "worldwide"}
_CO_SUFFIX = re.compile(r"\b(inc|llc|ltd|gmbh|sas|sa|bv|ag|corp|corporation|co|limited|plc|oy|ab)\b\.?", re.I)


def norm(text: str) -> str:
    t = re.sub(r"\(.*?\)|\[.*?\]", " ", text.lower())
    t = re.sub(r"\bsr\b\.?", "senior", t)
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return " ".join(w for w in t.split() if w not in _NOISE)


def key(job: dict) -> str:
    company = " ".join(re.sub(r"[^a-z0-9 ]", " ", _CO_SUFFIX.sub(" ", job["company"].lower())).split())
    return f"{company}|{norm(job['title'])}"


def dedupe(jobs: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for j in jobs:
        k = key(j)
        if k not in merged:
            merged[k] = j
            continue
        m = merged[k]
        m["sources"] = sorted(set(m["sources"]) | set(j["sources"]))
        # keep the richer record's fields where ours are empty
        for f in ("salary", "location", "description", "posted_at"):
            if not m.get(f) and j.get(f):
                m[f] = j[f]
        if len(j.get("_fulltext", "")) > len(m.get("_fulltext", "")):
            m["_fulltext"] = j["_fulltext"]
        m["location_list"] = sorted(set(m.get("location_list", [])) | set(j.get("location_list", [])))
        m["timezones"] = sorted(set(m.get("timezones", [])) | set(j.get("timezones", [])))
        m["tags"] = sorted(set(m["tags"]) | set(j["tags"]))[:20]
        # earliest posting date wins
        if j.get("posted_at") and m.get("posted_at") and j["posted_at"] < m["posted_at"]:
            m["posted_at"] = j["posted_at"]
    return list(merged.values())
