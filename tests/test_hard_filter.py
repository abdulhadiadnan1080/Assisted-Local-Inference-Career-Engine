from alice_core.evaluator import extract_hard_heuristic, hard_fail, hard_unknown
from alice_core.schemas import Listing


def test_ge20_archives():
    listing = Listing(
        source="t",
        title="Eng",
        company="BigCo",
        source_url="https://x.test/h1",
        description="Enterprise fortune 500 team of 200 people. $50/hr worldwide.",
    )
    h = extract_hard_heuristic(listing)
    assert h.size_bucket == "ge_20"
    assert hard_fail(h)


def test_unknown_size_or_pay_needs_review():
    listing = Listing(
        source="t",
        title="Eng",
        company="Mystery",
        source_url="https://x.test/h2",
        description="Remote worldwide. Come join us.",
    )
    h = extract_hard_heuristic(listing)
    assert h.size_bucket == "unknown" or h.pay_band == "unknown"
    assert hard_unknown(h)
    assert not hard_fail(h)


def test_in_band_tiny_international():
    listing = Listing(
        source="t",
        title="Founding engineer",
        company="Seedling",
        source_url="https://x.test/h3",
        description="We are 8 people, work from anywhere worldwide. $50/hr USD. Visa ok.",
        pay_text="$50/hr",
    )
    h = extract_hard_heuristic(listing)
    assert h.size_bucket == "lt_20"
    assert h.international_hire == "yes"
    assert h.pay_band == "in_band"
    assert not hard_fail(h)
    assert not hard_unknown(h)
