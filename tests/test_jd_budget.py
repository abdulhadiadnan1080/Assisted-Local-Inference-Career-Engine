from alice_core import db
from alice_core.crawl import fetch_jd
from tests.conftest import good_listing


def test_budget_caps_new_fetches(monkeypatch):
    listing = good_listing(
        10,
        description="short",
        snippet="short worldwide $50/hr 8 people",
    )
    monkeypatch.setattr("alice_core.crawl.get_text", lambda *a, **k: "FULL JD " * 80)
    monkeypatch.setattr(db, "jd_budget_remaining", lambda cap=80: 0)
    text, counted = fetch_jd("remoteok", listing)
    assert counted is False
    assert "FULL JD" not in text


def test_cache_does_not_consume(monkeypatch):
    url = "https://budget.example.test/job"
    listing = good_listing(11, description="x", source_url=url, apply_url=url)
    db.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    db.cache_payload(url, "cached body " * 50)
    before = db.jd_budget_remaining()
    text, counted = fetch_jd("remoteok", listing)
    assert counted is False
    assert "cached body" in text
    assert db.jd_budget_remaining() == before


def test_consume_persists_per_day():
    start = db.jd_budget_remaining(cap=80)
    db.consume_jd_fetch()
    assert db.jd_budget_remaining(cap=80) == start - 1
