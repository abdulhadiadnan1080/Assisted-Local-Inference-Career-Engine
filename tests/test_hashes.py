from datetime import date

from alice_core import db
from tests.conftest import good_listing


def test_same_url_upserts_same_row():
    listing = good_listing(1)
    a, skip_a = db.upsert_listing(listing)
    b, skip_b = db.upsert_listing(listing)
    assert a == b
    assert skip_a is False
    assert skip_b is True


def test_content_change_allows_rescore_keeps_shown_on():
    listing = good_listing(2)
    job_id, _ = db.upsert_listing(listing)
    db.stamp_shown([job_id], date.today())
    row = db.job_row(job_id)
    shown = row["shown_on"]
    changed = listing.model_copy(update={"description": listing.description + " more detail"})
    again, skip = db.upsert_listing(changed)
    assert again == job_id
    assert skip is False
    assert db.job_row(job_id)["shown_on"] == shown
