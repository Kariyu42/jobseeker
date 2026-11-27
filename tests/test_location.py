import pytest

from fetcher.location import classify, find_countries
from fetcher.normalize import job

ME = {"home_country": "France", "work_authorization": ["EU"], "would_live_in": ["Portugal"],
      "timezone_min": -1, "timezone_max": 4, "level": "mid"}


def mk(location="", desc="", location_list=None, timezones=None):
    return job(source="t", key=location + desc, title="DevOps Engineer", company="Acme", url="https://x",
               location=location, description=desc, location_list=location_list, timezones=timezones)


@pytest.mark.parametrize("loc,desc,elig", [
    ("Worldwide", "", "eligible"),
    ("Anywhere in the World", "", "eligible"),
    ("Europe", "", "eligible"),
    ("EMEA", "", "eligible"),
    ("Remote - EU", "", "eligible"),
    ("France", "", "eligible"),
    ("Spain, Portugal", "", "eligible"),
    ("Berlin, Germany", "", "eligible"),
    ("USA Only", "", "not_eligible"),
    ("United States", "", "not_eligible"),
    ("US, Canada", "", "not_eligible"),
    ("North America", "", "not_eligible"),
    ("LATAM", "", "not_eligible"),
    ("India", "", "not_eligible"),
    ("United Kingdom", "", "not_eligible"),
    ("Remote", "Candidates must be authorized to work in the US.", "not_eligible"),
    ("Worldwide", "This role requires an active security clearance.", "not_eligible"),
    ("Remote", "You must reside in Canada.", "not_eligible"),
    ("Remote", "", "unclear"),
    ("", "We pay via Deel as a contractor.", "unclear"),
    ("UTC-8 to UTC-5", "", "not_eligible"),
    ("Remote (UTC+0 to UTC+3)", "", "eligible"),
    ("Latin America", "", "not_eligible"),
    ("Remote", "You must live in the EU or UK.", "unclear"),
    ("Europe", "You must be based in Germany or Spain.", "eligible"),
])
def test_eligibility(loc, desc, elig):
    r = classify(mk(loc, desc), ME)
    assert r["eligibility"] == elig, (loc, desc, r)


def test_structured_timezones():
    assert classify(mk("Worldwide", timezones=[-8, -7, -6, -5]), ME)["eligibility"] == "not_eligible"
    assert classify(mk("Worldwide", timezones=[0, 1, 2]), ME)["eligibility"] == "eligible"


def test_structured_location_list():
    r = classify(mk("Germany, Netherlands", location_list=["Germany", "Netherlands"]), ME)
    assert r["eligibility"] == "eligible"


def test_us_terms_inside_region_are_flagged_unclear():
    r = classify(mk("Europe", "Benefits include 401k matching."), ME)
    assert r["eligibility"] == "unclear"


def test_us_resident_user():
    me = {"home_country": "United States", "work_authorization": [], "timezone_min": -8, "timezone_max": -4}
    assert classify(mk("USA Only"), me)["eligibility"] == "eligible"


def test_aliases_dont_overmatch():
    assert find_countries("Latin America") == set()
    assert find_countries("North America") == set()
    assert "united states" in find_countries("Remote, USA")


def test_fractional_timezones():
    r = classify(mk("Worldwide", timezones=[5.5]), ME)
    assert r["eligibility"] == "not_eligible" and "UTC+5.5" in r["reason"]
    r = classify(mk("Europe", timezones=[0, 1.0, 2]), ME)
    assert r["eligibility"] == "eligible" and "UTC+0 to UTC+2" in r["reason"]
