from __future__ import annotations

from pathlib import Path

import pytest

from alice_core import db
from alice_core.schemas import Listing


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(db, "CACHE_DIR", tmp_path / "data" / "cache")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "data" / "alice.db")
    monkeypatch.setattr("alice_core.crawl.jitter", lambda: None)
    monkeypatch.setattr("alice_core.tailor.ARTIFACTS", tmp_path / "artifacts")
    # Tests stay on heuristics. Live Ollama is for the dashboard, not pytest.
    monkeypatch.setattr("alice_core.llm.ollama_reachable", lambda: False)
    (tmp_path / "data" / "cache").mkdir(parents=True)
    (tmp_path / "artifacts").mkdir(parents=True)
    db.init_db()
    yield


def good_listing(i: int = 1, **kwargs) -> Listing:
    company = kwargs.pop("company", f"TinyCo {i}")
    url = kwargs.pop("source_url", f"https://jobs.example.test/{i}")
    defaults = dict(
        source="fixture",
        title="Senior Python engineer",
        company=company,
        location="Worldwide",
        apply_url=url,
        source_url=url,
        snippet="8 people, remote worldwide, $50/hr, Python FastAPI.",
        description=(
            "We are 8 people, fully remote, worldwide. Pay is $50/hr USD. "
            "Visa-friendly. Seed small team. Python, FastAPI, MLX, inference. "
            "Distributed team, work from anywhere. Founding engineer energy. "
            "Own a slice of the stack and write things down. "
            "No enterprise process theater. Eight people on a single product."
        ),
        pay_text="$50/hr",
        is_remote=True,
    )
    defaults.update(kwargs)
    return Listing(**defaults)
