"""We Work Remotely RSS (DevOps & Sysadmin category)."""
import xml.etree.ElementTree as ET

from ..normalize import job

URL = "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"


def parse(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out = []
    for it in root.iter("item"):
        g = lambda tag: (it.findtext(tag) or "").strip()
        raw_title = g("title")
        company, _, title = raw_title.partition(":")
        if not title:
            company, title = "", raw_title
        out.append(job(
            source="weworkremotely",
            key=g("guid") or g("link"),
            title=title.strip(),
            company=company.strip(),
            url=g("link"),
            posted_at=g("pubDate"),
            tags=[c.text for c in it.findall("category") if c.text],
            location=g("region") or g("country"),
            description=g("description"),
            job_type=g("type"),
        ))
    return out


def fetch(http) -> list[dict]:
    return parse(http.get_text(URL))
