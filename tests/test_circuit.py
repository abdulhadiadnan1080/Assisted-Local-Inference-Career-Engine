from datetime import datetime, timedelta

import pytest

from alice_core import db
from alice_core.crawl import HttpTripped, enabled_sources, get_text


def test_enabled_sources_excludes_junk():
    names = enabled_sources()
    for banned in ("twitter", "wellfound", "glassdoor"):
        assert banned not in names
    assert "jobspy" in names


def test_429_trips_one_source(monkeypatch):
    class Resp:
        status_code = 429
        text = "slow down"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("alice_core.crawl.httpx.get", lambda *a, **k: Resp())
    with pytest.raises(HttpTripped):
        get_text("remoteok", "https://circuit.example.test/429")
    assert db.circuit_open("remoteok")
    assert not db.circuit_open("remotive")
    row = db._connect().execute(
        "SELECT paused_until FROM source_circuits WHERE source='remoteok'"
    ).fetchone()
    until = datetime.fromisoformat(row["paused_until"])
    assert until > datetime.utcnow() + timedelta(hours=23)


def test_403_same_as_429(monkeypatch):
    class Resp:
        status_code = 403
        text = "no"

        def raise_for_status(self):
            return None

    monkeypatch.setattr("alice_core.crawl.httpx.get", lambda *a, **k: Resp())
    with pytest.raises(HttpTripped):
        get_text("himalayas", "https://circuit.example.test/403")
    assert db.circuit_open("himalayas")
