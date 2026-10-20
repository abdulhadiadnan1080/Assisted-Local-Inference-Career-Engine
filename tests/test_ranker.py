from datetime import date, timedelta

from alice_core import db
from alice_core.ranker import select_daily_fifteen
from tests.conftest import good_listing


def _backlog(n: int, score: float, email: bool, i: int) -> str:
    listing = good_listing(i)
    job_id, _ = db.upsert_listing(listing, status="DISCOVERED")
    db.force_status(job_id, "BACKLOG")
    db.save_hard(
        job_id,
        {
            "size_headcount": 8,
            "size_bucket": "lt_20",
            "international_hire": "yes",
            "pay_hourly_usd": 50,
            "pay_band": "in_band",
            "evidence": ["fixture"],
        },
    )
    db.save_eval(
        job_id,
        {
            "score_skills": 4,
            "score_experience": 4,
            "score_location": 4,
            "score_trajectory": 4,
            "score_culture": 4,
            "composite_score": score,
            "key_strengths": [],
            "critical_gaps": [],
            "really_need": ["x"],
            "recommendation": "PROCEED",
        },
    )
    db.save_poster(job_id, {"poster_email": "a@b.test" if email else None, "evidence": "t"})
    return job_id


def test_top_fifteen_shown_once():
    today = date(2026, 9, 8)
    ids = [_backlog(20, 4.0 + (i * 0.01), email=(i % 2 == 0), i=100 + i) for i in range(20)]
    first = select_daily_fifteen(today)
    assert len(first) == 15
    second = select_daily_fifteen(today)
    assert second == first
    leftovers = set(ids) - set(first)
    assert leftovers
    for job_id in first:
        assert db.job_row(job_id)["shown_on"] == today.isoformat()
        assert db.job_row(job_id)["status"] == "READY"
    tomorrow = select_daily_fifteen(today + timedelta(days=1))
    assert set(tomorrow).isdisjoint(first)
    assert set(tomorrow) <= leftovers
