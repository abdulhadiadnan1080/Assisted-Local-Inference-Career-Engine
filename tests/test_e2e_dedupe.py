from datetime import date, timedelta

from alice_core.pipeline import run
from alice_core.ranker import select_daily_fifteen
from tests.conftest import good_listing


def test_two_runs_same_day_same_fifteen():
    today = date(2026, 9, 8)
    listings = [good_listing(i) for i in range(20, 40)]
    first = run(listings=listings, today=today, tailor=False)
    assert first["ok"]
    assert len(first["today"]) == 15
    second = run(listings=listings, today=today, tailor=False)
    assert second["today"] == first["today"]
    tomorrow = select_daily_fifteen(today + timedelta(days=1))
    assert set(tomorrow).isdisjoint(set(first["today"]))
