from alice_core.filters import snippet_gate
from alice_core.schemas import Listing


def test_us_only_archives():
    listing = Listing(
        source="t",
        title="Eng",
        company="Acme",
        location="US only",
        source_url="https://x.test/1",
        snippet="Must reside in the US. Onsite only.",
    )
    ok, reason = snippet_gate(listing)
    assert ok is False
    assert "red flag" in reason


def test_unknown_pay_does_not_archive():
    listing = Listing(
        source="t",
        title="Eng",
        company="Seedling",
        location="Worldwide",
        source_url="https://x.test/2",
        snippet="Tiny remote team, work from anywhere.",
    )
    ok, _ = snippet_gate(listing)
    assert ok is True


def test_out_of_band_pay():
    listing = Listing(
        source="t",
        title="Eng",
        company="Seedling",
        location="Worldwide",
        source_url="https://x.test/3",
        snippet="Worldwide remote $25/hr",
        pay_text="$25/hr",
    )
    ok, reason = snippet_gate(listing)
    assert ok is False
    assert "pay" in reason


def test_faang_company():
    listing = Listing(
        source="t",
        title="Eng",
        company="Google",
        location="Remote",
        source_url="https://x.test/4",
        snippet="Remote worldwide $50/hr",
    )
    ok, _ = snippet_gate(listing)
    assert ok is False


def test_filters_have_no_llm():
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "alice_core" / "filters.py").read_text()
    assert "ollama" not in src.lower()
    assert "instructor" not in src.lower()
    assert "structured(" not in src
