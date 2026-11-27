"""Fetch → filter → classify → score → merge with history → docs/jobs.json.

Run:  python -m fetcher.main            (all sources)
      python -m fetcher.main --only remotive,himalayas
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

from . import sources
from .dedupe import dedupe
from .location import classify
from .normalize import salary_max
from .score import age_days, score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "jobs.json"
CONFIG = ROOT / "config.yml"
log = logging.getLogger("jobseeker")


class Http:
    """Tiny polite HTTP client with retries."""

    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (compatible; jobseeker/1.0; personal job search)"

    def _get(self, url: str) -> requests.Response:
        for attempt in range(3):
            try:
                r = self.s.get(url, timeout=30)
                if r.status_code in (429, 502, 503, 504):
                    raise requests.HTTPError(f"{r.status_code}")
                r.raise_for_status()
                return r
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("unreachable")

    def get_json(self, url: str):
        return self._get(url).json()

    def get_text(self, url: str) -> str:
        return self._get(url).text


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text())


def title_ok(title: str, cfg: dict) -> bool:
    inc = cfg.get("title_include", [])
    exc = cfg.get("title_exclude", [])
    return any(re.search(p, title, re.I) for p in inc) and not any(re.search(p, title, re.I) for p in exc)


def process(raw: list[dict], cfg: dict, now: datetime) -> list[dict]:
    max_age = cfg.get("max_age_days", 30)
    min_sal = cfg.get("min_salary", 0) or 0
    kept = []
    for j in raw:
        if not j["title"] or not j["url"] or not title_ok(j["title"], cfg):
            continue
        a = age_days(j, now)
        if a is not None and a > max_age:
            continue
        if min_sal:
            sm = salary_max(j["salary"])
            if sm and sm < min_sal:
                continue
        kept.append(j)
    kept = dedupe(kept)
    out = []
    for j in kept:
        try:  # one odd posting must never break the whole run
            loc = classify(j, cfg.get("me", {}))
            j.update({
                "scope": loc["scope"],
                "eligibility": loc["eligibility"],
                "elig_reason": loc["reason"],
                "contractor": loc["contractor"],
            })
            j["score"], j["skills"] = score(j, cfg, now)
        except Exception as e:
            log.warning("skipped job %r from %s: %s", j.get("title"), j.get("source"), e)
            continue
        out.append(j)
    return out


def merge_history(fresh: list[dict], previous: dict, cfg: dict, now: datetime, failed: set[str] = frozenset()) -> list[dict]:
    """Keep jobs seen in the last max_age_days even if a board dropped them.

    Jobs whose boards all failed this run keep their previous active flag.
    """
    now_s = now.isoformat()
    prev = {j["id"]: j for j in previous.get("jobs", [])}
    cutoff = (now - timedelta(days=cfg.get("max_age_days", 30))).isoformat()
    out = {}
    for j in fresh:
        old = prev.get(j["id"])
        j["first_seen"] = old["first_seen"] if old else now_s
        j["last_seen"] = now_s
        j["active"] = True
        out[j["id"]] = j
    for jid, old in prev.items():
        if jid not in out and (old.get("posted_at") or old["first_seen"]) >= cutoff:
            if not set(old.get("sources", [old.get("source")])) <= failed:
                old["active"] = False  # no longer listed by the board; may be filled
            out[jid] = old
    return sorted(out.values(), key=lambda j: (-j["score"], j.get("posted_at") or ""))


def run(only: list[str] | None = None, out_path: Path = OUT) -> dict:
    cfg = load_config()
    now = datetime.now(timezone.utc)
    http = Http()
    chosen = {k: v for k, v in sources.ALL.items() if not only or k in only}

    def go(item):
        name, fn = item
        t = time.time()
        try:
            res = fn(http)
            log.info("%-15s %4d raw jobs (%.1fs)", name, len(res), time.time() - t)
            return name, res, None
        except Exception as e:  # one broken board must never break the run
            log.warning("%-15s FAILED: %s", name, e)
            return name, [], f"{type(e).__name__}: {e}"[:200]

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(go, chosen.items()))

    raw = [j for _, res, _ in results for j in res]
    fresh = process(raw, cfg, now)
    per_source = {name: {"raw": len(res), "kept": sum(name in j["sources"] for j in fresh), "error": err}
                  for name, res, err in results}

    failed = {name for name, _, err in results if err}
    if failed == set(chosen):
        log.error("every source failed; keeping the existing %s", out_path.name)
        return {"sources": per_source, "jobs": [], "failed": True}

    previous = {}
    if out_path.exists():
        try:
            previous = json.loads(out_path.read_text())
        except json.JSONDecodeError:
            previous = {}
    jobs = merge_history(fresh, previous, cfg, now, failed)
    for j in jobs:
        j.pop("_fulltext", None)

    data = {
        "generated_at": now.isoformat(),
        "previous_run": previous.get("generated_at"),
        "profile": {k: cfg["me"].get(k) for k in ("home_country", "work_authorization", "would_live_in",
                                                  "timezone_min", "timezone_max", "level")},
        "sources": per_source,
        "counts": {e: sum(j["eligibility"] == e for j in jobs) for e in ("eligible", "unclear", "not_eligible")},
        "jobs": jobs,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    log.info("wrote %d jobs (%s) -> %s", len(jobs), data["counts"], out_path)
    return data


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated source names")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    data = run(args.only.split(",") if args.only else None)
    if data.get("failed"):
        sys.exit(1)


if __name__ == "__main__":
    main()
