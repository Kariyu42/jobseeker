"""Work out *where a remote job actually lets you live*, and whether you qualify.

Most "100% remote" postings quietly hire only in one country or timezone band.
This module reads the structured location fields plus the job text and returns:

    scope:       worldwide | europe | countries | americas | asia_pacific | unknown
    eligibility: eligible | unclear | not_eligible
    reason:      short human explanation shown in the app
"""
from __future__ import annotations

import re

EU_EEA = {
    "austria", "belgium", "bulgaria", "croatia", "cyprus", "czechia", "czech republic",
    "denmark", "estonia", "finland", "france", "germany", "greece", "hungary", "ireland",
    "italy", "latvia", "lithuania", "luxembourg", "malta", "netherlands", "poland",
    "portugal", "romania", "slovakia", "slovenia", "spain", "sweden",
    "iceland", "liechtenstein", "norway", "switzerland",
}
OTHER_EUROPE = {
    "united kingdom", "serbia", "ukraine", "bosnia", "montenegro", "albania",
    "north macedonia", "moldova", "georgia", "armenia", "turkey", "belarus",
}
AMERICAS = {
    "united states", "canada", "mexico", "brazil", "argentina", "colombia", "chile",
    "peru", "uruguay", "costa rica", "ecuador", "guatemala", "venezuela",
}
APAC = {
    "india", "australia", "new zealand", "singapore", "philippines", "japan", "indonesia",
    "vietnam", "malaysia", "thailand", "pakistan", "bangladesh", "china", "south korea",
    "hong kong", "taiwan", "sri lanka", "nepal",
}
MEA = {
    "israel", "south africa", "nigeria", "kenya", "egypt", "morocco", "tunisia",
    "united arab emirates", "saudi arabia", "ghana",
}
ALL_COUNTRIES = EU_EEA | OTHER_EUROPE | AMERICAS | APAC | MEA

ALIASES = {
    r"\bu\.?s\.?a?\.?\b": "united states",
    r"(?<!north )(?<!latin )(?<!south )(?<!central )\bamerica\b": "united states",
    r"\bunited states of america\b": "united states",
    r"\bu\.?k\.?\b": "united kingdom",
    r"\bgreat britain\b|\bengland\b|\bscotland\b|\bwales\b|\bbritain\b": "united kingdom",
    r"\bdeutschland\b": "germany",
    r"\bespa[ñn]a\b": "spain",
    r"\bthe netherlands\b|\bholland\b": "netherlands",
    r"\buae\b|\bdubai\b": "united arab emirates",
    r"\bczech\b": "czechia",
    r"\bberlin\b|\bmunich\b|\bm[üu]nchen\b|\bhamburg\b|\bfrankfurt\b|\bcologne\b|\bk[öo]ln\b": "germany",
    r"\bparis\b|\blyon\b": "france",
    r"\blondon\b|\bmanchester\b": "united kingdom",
    r"\bamsterdam\b|\brotterdam\b": "netherlands",
    r"\bmadrid\b|\bbarcelona\b": "spain",
    r"\blisbon\b|\bporto\b": "portugal",
    r"\bnew york\b|\bsan francisco\b|\bcalifornia\b|\btexas\b|\bseattle\b|\bboston\b|\bchicago\b": "united states",
    r"\btoronto\b|\bvancouver\b|\bmontreal\b": "canada",
    r"\bbangalore\b|\bbengaluru\b|\bmumbai\b|\bdelhi\b|\bhyderabad\b|\bpune\b": "india",
}

# region keyword -> set of countries it covers (None = everywhere)
REGIONS = {
    "worldwide": None,
    "europe": EU_EEA | OTHER_EUROPE,
    "eu": EU_EEA,
    "emea": EU_EEA | OTHER_EUROPE | MEA,
    "americas": AMERICAS,
    "north america": {"united states", "canada", "mexico"},
    "latam": AMERICAS - {"united states", "canada"},
    "apac": APAC,
    "asia": APAC,
}

WORLDWIDE_RE = re.compile(
    r"\b(anywhere|worldwide|world ?wide|global(ly)?|international|any (country|location)|"
    r"work from anywhere|location independent|fully distributed)\b",
    re.I,
)
REGION_RES = [
    ("emea", re.compile(r"\bemea\b", re.I)),
    ("eu", re.compile(r"\b(eu|european union|eea)\b", re.I)),
    ("europe", re.compile(r"\b(europe|european|cet|cest|eet|wet)\b", re.I)),
    ("north america", re.compile(r"\bnorth america\b|\b(est|edt|pst|pdt|cst|mst)\b|\b(eastern|pacific|central|mountain) time\b", re.I)),
    ("latam", re.compile(r"\b(latam|latin america|south america)\b", re.I)),
    ("americas", re.compile(r"\bamericas\b", re.I)),
    ("apac", re.compile(r"\b(apac|asia[- ]pacific)\b", re.I)),
    ("asia", re.compile(r"\basia\b", re.I)),
]

# Phrases in the description that betray a hidden country restriction.
US_ONLY_RE = re.compile(
    r"(\b(us|u\.s\.|usa|united states)[- ](only|based|residents?|citizens?|persons?)\b|"
    r"must (be|reside|live|be located|be based)\s+(in|within)\s+the\s+(us|u\.s\.|usa|united states)|"
    r"authori[sz]ed to work in the (us|u\.s\.|united states)|"
    r"\b(within|in) the (continental )?(us|u\.s\.|united states)\b only|"
    r"\bsecurity clearance\b|\b(ts/sci|public trust)\b|\bw-?2\b|\b401\(?k\)?)",
    re.I,
)
RESIDE_RE = re.compile(
    r"(must|need to|required to|should)\s+(be\s+)?(reside|live|be (located|based)|have (the )?right to work)\s+(in|within)\s+(?P<where>[a-z ,]+?)[.;\n)]",
    re.I,
)
CONTRACTOR_RE = re.compile(r"\b(deel|remote\.com|oyster|contractor|b2b|freelance|eor|employer of record)\b", re.I)

_UTC_RE = re.compile(r"\b(?:utc|gmt)\s*([+-−–]\s*\d{1,2})(?::?\d{2})?(?:\s*(?:to|-|–|/)\s*(?:utc|gmt)?\s*([+-−–]\s*\d{1,2}))?", re.I)


def _canon(text: str) -> str:
    t = text.lower()
    for pat, repl in ALIASES.items():
        t = re.sub(pat, repl, t)
    return t


def find_countries(text: str) -> set[str]:
    t = _canon(text)
    return {c for c in ALL_COUNTRIES if re.search(rf"\b{re.escape(c)}\b", t)}


def find_regions(text: str) -> set[str]:
    return {name for name, rx in REGION_RES if rx.search(text)}


def parse_offsets(text: str) -> list[int]:
    out: list[int] = []
    for m in _UTC_RE.finditer(text):
        for g in m.groups():
            if g:
                out.append(int(re.sub(r"[−–\s]", lambda x: "-" if x.group() in "−–" else "", g)))
    return out


def fmt_offset(o: float) -> str:
    return f"{o:+g}"


def tz_range(offsets) -> str:
    lo, hi = min(offsets), max(offsets)
    return f"UTC{fmt_offset(lo)}" if lo == hi else f"UTC{fmt_offset(lo)} to UTC{fmt_offset(hi)}"


def user_countries(me: dict) -> set[str]:
    allowed = set()
    for item in [me.get("home_country", "")] + list(me.get("work_authorization", [])) + list(me.get("would_live_in", [])):
        key = str(item).strip().lower()
        if key in ("eu", "eea", "european union"):
            allowed |= EU_EEA
        elif key:
            allowed |= find_countries(key) or {key}
    return allowed


def classify(job: dict, me: dict) -> dict:
    """Return {'scope','eligibility','reason','countries','contractor'} for a job."""
    mine = user_countries(me)
    tz_lo, tz_hi = me.get("timezone_min", -1), me.get("timezone_max", 4)
    strict = bool(me.get("strict_country", False))

    loc_fields = " | ".join([job.get("location", "")] + job.get("location_list", []))
    loc_l = loc_fields.lower()
    text = job.get("_fulltext") or job.get("description", "")
    countries = find_countries(loc_fields)
    regions = find_regions(loc_fields)
    worldwide = bool(WORLDWIDE_RE.search(loc_fields)) or loc_l.strip(" |") in ("", "remote", "100% remote", "fully remote")
    explicit_worldwide = bool(WORLDWIDE_RE.search(loc_fields))
    contractor = bool(CONTRACTOR_RE.search(text) or CONTRACTOR_RE.search(job.get("job_type", "")))

    # Timezone checks: structured (Himalayas) then text.
    offsets = [o for o in job.get("timezones", []) if isinstance(o, (int, float))]
    offsets += parse_offsets(loc_fields)
    tz_ok = None
    if offsets:
        tz_ok = any(tz_lo - 1 <= o <= tz_hi + 1 for o in offsets)
        if not tz_ok and len(offsets) >= 2:  # a range like UTC-8 to UTC+3
            tz_ok = min(offsets) <= tz_hi and max(offsets) >= tz_lo

    covered: set[str] = set(countries)
    for r in regions:
        if REGIONS.get(r) is None:
            worldwide = True
        else:
            covered |= REGIONS[r]

    scope = "unknown"
    if explicit_worldwide:
        scope = "worldwide"
    elif regions & {"europe", "eu", "emea"} or (countries and countries <= (EU_EEA | OTHER_EUROPE)):
        scope = "europe" if not countries or len(countries) > 2 or regions else "countries"
    elif countries:
        scope = "countries"
        if countries <= AMERICAS:
            scope = "americas"
        elif countries <= APAC:
            scope = "asia_pacific"
    elif regions & {"north america", "americas", "latam"}:
        scope = "americas"
    elif regions & {"apac", "asia"}:
        scope = "asia_pacific"
    elif worldwide:
        scope = "worldwide"

    us_only_text = bool(US_ONLY_RE.search(text))
    reside = RESIDE_RE.search(text)
    reside_countries: set[str] = set()
    if reside:
        where = reside.group("where")
        reside_countries = find_countries(where)
        for r in find_regions(where):
            reside_countries |= REGIONS.get(r) or set()

    def result(elig, reason):
        return {"scope": scope, "eligibility": elig, "reason": reason,
                "countries": sorted(countries)[:10], "contractor": contractor}

    if tz_ok is False:
        return result("not_eligible", f"Timezone required: {tz_range(offsets)}")
    if reside_countries and not (reside_countries & mine):
        shown = sorted(reside_countries)
        return result("not_eligible", "Must live in " + ", ".join(shown[:3]).title() + ("…" if len(shown) > 3 else ""))

    # Structured restriction lists (e.g. Himalayas) are authoritative: if none of the
    # listed places is one you can work from, the job can't hire you, even when the
    # country is one this module doesn't know by name.
    listed = [x for x in job.get("location_list", []) if x]
    if listed and not explicit_worldwide and not (covered & mine):
        shown = ", ".join(listed[:3]) + ("…" if len(listed) > 3 else "")
        return result("not_eligible", f"Restricted to {shown}")

    if covered:
        if covered & mine:
            if us_only_text and "united states" not in mine:
                return result("unclear", "Lists your region, but text mentions US-only terms")
            hit = sorted(covered & mine)
            if scope == "countries" and strict:
                return result("unclear", "Country-specific: " + ", ".join(hit).title())
            if scope == "countries":
                return result("eligible", "Hires in " + ", ".join(c.title() for c in hit[:3]))
            return result("eligible", "Hires in your region" + (f" ({tz_range(offsets)})" if offsets else ""))
        if not worldwide:
            where = ", ".join(sorted(countries)[:3]).title() or ", ".join(sorted(regions)).upper()
            return result("not_eligible", f"Restricted to {where}")

    if us_only_text and "united states" not in mine:
        return result("not_eligible", "Description says US-only / US work authorization")
    if explicit_worldwide:
        return result("eligible", "Worldwide" + (" · contractor/EOR" if contractor else ""))
    if tz_ok:
        return result("eligible", "Timezone fits you")
    if contractor:
        return result("unclear", "Location not stated · contractor-friendly")
    return result("unclear", "Location not stated — check the posting")
