"""The per-country rules file must stay complete and sourced."""
import json
from pathlib import Path

from fetcher.location import EU_EEA

DATA = json.loads((Path(__file__).resolve().parent.parent / "docs" / "countries.json").read_text())


def test_every_eu_eea_country_and_common_destinations_are_covered():
    expected = (EU_EEA - {"czech republic"}) | {"united kingdom", "united states", "canada"}  # alias of czechia
    assert expected <= set(DATA["countries"]), expected - set(DATA["countries"])


def test_every_entry_has_rules_and_an_official_source():
    for key, c in DATA["countries"].items():
        for field in ("name", "group", "right_to_work", "register", "sources"):
            assert c.get(field), f"{key} missing {field}"
        assert c["sources"] and all(s["url"].startswith("https://") for s in c["sources"]), key


def test_common_sections_present():
    for sec in ("eu_move", "stay_in_france"):
        assert DATA["common"][sec]["points"] and DATA["common"][sec]["sources"]
    assert DATA["reviewed"] and DATA["disclaimer"]
