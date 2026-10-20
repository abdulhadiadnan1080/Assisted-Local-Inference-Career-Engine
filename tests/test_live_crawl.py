from alice_core import db
from alice_core.crawl import pull_all
from alice_core.pipeline import run
from tests.conftest import good_listing


def test_live_crawl_defaults_off():
    assert db.live_crawl_enabled() is False
    assert pull_all() == []
    blocked = run()
    assert blocked["ok"] is False
    assert blocked["reason"] == "live crawl is off"
    assert db.counts()["READY"] == 0


def test_fixture_run_still_works_with_live_off():
    first = run(listings=[good_listing(i) for i in range(1, 4)], tailor=False)
    assert first["ok"] is True
    assert first["count"] >= 1
