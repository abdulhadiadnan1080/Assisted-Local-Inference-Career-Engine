from alice_core import db
from alice_core.pipeline import request_stop, run
from tests.conftest import good_listing


def test_stop_skips_remaining_listings(monkeypatch):
    seen: list[str] = []

    def fake(listing, profile, tailor=True, force=False, stage=None):
        seen.append(listing.company)
        if len(seen) == 1:
            request_stop()
        return "ARCHIVED"

    monkeypatch.setattr("alice_core.pipeline.process_listing", fake)
    result = run(listings=[good_listing(i) for i in range(1, 6)], tailor=False)
    assert result["ok"] is True
    assert result.get("stopped") is True
    assert len(seen) == 1
    assert db.is_running() is False
