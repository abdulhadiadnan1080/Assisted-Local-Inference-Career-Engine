import pytest

from alice_core import db
from tests.conftest import good_listing


def test_illegal_and_ready_requires_shown_on():
    job_id, _ = db.upsert_listing(good_listing(3))
    with pytest.raises(ValueError):
        db.set_status(job_id, "READY")
    db.set_status(job_id, "SNIPPET_FILTERED")
    db.set_status(job_id, "JD_FETCHED")
    db.set_status(job_id, "ARCHIVED")
    with pytest.raises(ValueError):
        db.set_status(job_id, "READY")
    with pytest.raises(ValueError):
        db.set_status(job_id, "BACKLOG")


def test_skipped_never_ready():
    job_id, _ = db.upsert_listing(good_listing(4))
    db.set_status(job_id, "SNIPPET_FILTERED")
    db.set_status(job_id, "JD_FETCHED")
    db.set_status(job_id, "BACKLOG")
    db.stamp_shown([job_id], __import__("datetime").date.today())
    db.set_status(job_id, "SKIPPED")
    with pytest.raises(ValueError):
        db.set_status(job_id, "READY")
