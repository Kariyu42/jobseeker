"""Common job schema + text helpers shared by every source."""
from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

SNIPPET_LEN = 1500

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_BLOCK_RE = re.compile(r"</?(p|br|li|ul|ol|div|h\d)[^>]*>", re.I)


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = _BLOCK_RE.sub(" \n ", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def to_iso(value) -> str | None:
    """Accept epoch seconds, ISO strings, 'YYYY-MM-DD HH:MM:SS' or RFC-822 dates."""
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            ts = float(value)
            if ts > 1e12:  # milliseconds
                ts /= 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        s = str(value).strip()
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            dt = parsedate_to_datetime(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, OverflowError):
        return None


def fmt_salary(lo=None, hi=None, currency: str | None = None, raw: str | None = None) -> str:
    def num(v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        return v if v > 0 else None

    lo, hi = num(lo), num(hi)
    cur = (currency or "").upper()
    sym = {"USD": "$", "EUR": "€", "GBP": "£"}.get(cur, (cur + " ") if cur else "")

    def k(v):
        return f"{sym}{round(v / 1000)}k" if v >= 1000 else f"{sym}{int(v)}"

    if lo and hi and lo != hi:
        return f"{k(lo)}–{k(hi)}"
    if lo or hi:
        return k(lo or hi)
    return (raw or "").strip()


_SAL_NUM_RE = re.compile(r"(\d{2,3})(?:[.,]\d{3}|\s?k)", re.I)


def salary_max(salary: str) -> int | None:
    """Rough upper bound of a salary string, in units (e.g. 120000)."""
    if not salary:
        return None
    nums = [int(m.group(1)) * 1000 for m in _SAL_NUM_RE.finditer(salary)]
    return max(nums) if nums else None


def make_id(source: str, key: str) -> str:
    return hashlib.sha1(f"{source}:{key}".encode()).hexdigest()[:12]


def job(
    *,
    source: str,
    key: str,
    title: str,
    company: str,
    url: str,
    posted_at=None,
    tags=None,
    salary: str = "",
    location: str = "",
    location_list=None,
    timezones=None,
    description: str = "",
    job_type: str = "",
) -> dict:
    """Build a normalized job dict. Every source must go through this."""
    desc = strip_html(description)
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]
    return {
        "id": make_id(source, str(key)),
        "title": strip_html(title)[:200],
        "company": strip_html(company)[:120] or "Unknown",
        "url": url,
        "source": source,
        "sources": [source],
        "posted_at": to_iso(posted_at),
        "tags": sorted({str(t).strip().lower() for t in (tags or []) if str(t).strip()})[:20],
        "salary": salary or "",
        "location": strip_html(location)[:300],
        "location_list": [str(x) for x in (location_list or []) if x],
        "timezones": list(timezones or []),
        "job_type": job_type or "",
        "description": desc[:SNIPPET_LEN],
        # full text is only used during scoring/classification, then dropped
        "_fulltext": desc,
    }
