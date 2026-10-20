from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from alice_core import db
from alice_core.crawl import enabled_sources
from tests.conftest import good_listing

ROOT = Path(__file__).resolve().parents[1]


def test_no_cloud_clients_in_source():
    text = ""
    for path in [ROOT / "app.py", * (ROOT / "alice_core").rglob("*.py")]:
        text += path.read_text(encoding="utf-8", errors="ignore")
    assert "https://api.openai.com" not in text
    assert "api.anthropic.com" not in text
    assert "bedrock-runtime" not in text
    assert "api.apollo.io" not in text
    assert "hunter.io" not in text


def test_apply_never_posts_the_ats():
    import httpx

    from app import app

    posts: list = []
    original = httpx.post

    def wrapped(*args, **kwargs):
        posts.append(args)
        return original(*args, **kwargs)

    httpx.post = wrapped  # type: ignore[method-assign]
    try:
        listing = good_listing(77)
        job_id, _ = db.upsert_listing(listing)
        db.stamp_shown([job_id], date.today())
        client = TestClient(app)
        res = client.post(f"/api/jobs/{job_id}/apply")
        assert res.status_code == 200
        assert res.json()["apply_url"] == listing.apply_url
        assert posts == []
    finally:
        httpx.post = original  # type: ignore[method-assign]


def test_junk_sources_stay_off():
    assert not set(enabled_sources()) & {"twitter", "wellfound", "glassdoor"}
