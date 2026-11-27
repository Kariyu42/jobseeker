"""End-to-end run with fake sources (no network)."""
import json
from datetime import datetime, timedelta, timezone

from fetcher import main, sources
from fetcher.normalize import job


def fake_jobs():
    t = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    mk = lambda **k: job(source="fake", url="https://example.com/" + k["key"], posted_at=t, **k)
    return [
        mk(key="1", title="DevOps Engineer", company="Acme", location="Europe", description="Kubernetes Terraform AWS"),
        mk(key="2", title="Senior SRE", company="Beta", location="USA only", description="k8s"),
        mk(key="3", title="Platform Engineer", company="Gamma", location="Remote", description="must be authorized to work in the US"),
        mk(key="4", title="Marketing Lead", company="Delta", location="Worldwide"),
    ]


def test_run_end_to_end(tmp_path, monkeypatch):
    def boom(http):
        raise RuntimeError("site down")

    monkeypatch.setattr(sources, "ALL", {"fake": lambda http: fake_jobs(), "broken": boom})
    out = tmp_path / "jobs.json"
    data = main.run(out_path=out)
    saved = json.loads(out.read_text())
    assert saved["sources"]["broken"]["error"].startswith("RuntimeError")
    assert saved["sources"]["fake"]["kept"] == 3
    by = {j["company"]: j for j in saved["jobs"]}
    assert by["Acme"]["eligibility"] == "eligible"
    assert by["Beta"]["eligibility"] == "not_eligible"
    assert by["Gamma"]["eligibility"] == "not_eligible"
    assert "_fulltext" not in by["Acme"]
    assert saved["jobs"][0]["company"] == "Acme"  # best score first
    # second run keeps first_seen
    data2 = main.run(out_path=out)
    assert {j["id"]: j["first_seen"] for j in data2["jobs"]} == {j["id"]: j["first_seen"] for j in data["jobs"]}


def test_failed_board_keeps_jobs_active_and_total_outage_writes_nothing(tmp_path, monkeypatch):
    out = tmp_path / "jobs.json"
    monkeypatch.setattr(sources, "ALL", {"fake": lambda http: fake_jobs()})
    main.run(out_path=out)
    before = out.read_text()

    def boom(http):
        raise RuntimeError("down")

    monkeypatch.setattr(sources, "ALL", {"fake": boom})
    assert main.run(out_path=out).get("failed")
    assert out.read_text() == before

    monkeypatch.setattr(sources, "ALL", {"fake": boom, "other": lambda http: []})
    data = main.run(out_path=out)
    assert data["jobs"] and all(j["active"] for j in data["jobs"])
