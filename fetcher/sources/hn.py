"""Hacker News "Ask HN: Who is hiring?" — latest monthly thread, REMOTE posts only.

Posts are free-form, conventionally: "Company | Role | Location | REMOTE | ...".
"""
import re

from ..normalize import strip_html, job

LATEST = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=10"
ITEM = "https://hn.algolia.com/api/v1/items/{id}"
REMOTE_RE = re.compile(r"\bremote\b", re.I)
ROLE_RE = re.compile(r"devops|\bsre\b|site reliability|platform|infrastructure|\binfra\b|cloud|kubernetes|reliability", re.I)
NOT_REMOTE_RE = re.compile(r"\bno remote\b|\bnot remote\b|\bonsite only\b|\bon-site only\b", re.I)


def latest_thread_id(data) -> str | None:
    for h in data.get("hits", []):
        if "who is hiring" in (h.get("title") or "").lower():
            return h.get("objectID")
    return None


def parse_thread(data) -> list[dict]:
    out = []
    for c in data.get("children", []):
        text = c.get("text") or ""
        if not text:
            continue
        plain = strip_html(text)
        first = strip_html(text.split("<p>")[0])
        if not REMOTE_RE.search(first) or NOT_REMOTE_RE.search(plain) or not ROLE_RE.search(plain):
            continue
        parts = [p.strip() for p in first.split("|")]
        company = parts[0][:80] if parts else "HN"
        role = next((p for p in parts[1:] if ROLE_RE.search(p)), None)
        if not role:
            m = ROLE_RE.search(plain)
            role = f"{m.group(0).title()} role (see post)" if m else "Engineering"
        loc = " | ".join(p for p in parts[1:] if p != role)[:200]
        out.append(job(
            source="hackernews",
            key=c.get("id"),
            title=role[:150],
            company=company,
            url=f"https://news.ycombinator.com/item?id={c.get('id')}",
            posted_at=c.get("created_at_i") or c.get("created_at"),
            tags=["hn"],
            location=loc,
            description=text,
        ))
    return out


def fetch(http) -> list[dict]:
    tid = latest_thread_id(http.get_json(LATEST))
    if not tid:
        return []
    return parse_thread(http.get_json(ITEM.format(id=tid)))
