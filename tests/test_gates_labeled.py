import json
from pathlib import Path

from alice_core.evaluator import (
    composite_score,
    extract_hard_heuristic,
    hard_fail,
    hard_unknown,
    recommendation,
    score_heuristic,
)
from alice_core.filters import snippet_gate
from alice_core.profile import load_profile
from alice_core.schemas import Listing

FIXTURE = Path(__file__).parent / "fixtures" / "labeled_listings.json"


def test_labeled_gate_a():
    rows = json.loads(FIXTURE.read_text())
    assert len(rows) >= 50
    profile = load_profile()
    for row in rows:
        listing = Listing(**row["listing"])
        expected = row["gate_a"]
        ok, _ = snippet_gate(listing)
        if expected == "snippet_archive":
            assert ok is False, row["id"]
            continue
        h = extract_hard_heuristic(listing)
        if expected == "archive":
            assert hard_fail(h), (row["id"], h)
        elif expected == "review":
            assert not hard_fail(h)
            assert hard_unknown(h), (row["id"], h)
        elif expected == "pass":
            assert ok
            assert not hard_fail(h)
            assert not hard_unknown(h)
            ev = score_heuristic(listing, profile)
            rec = recommendation(composite_score(ev))
            if row.get("gate_b"):
                assert rec == row["gate_b"]
