from alice_core.evaluator import composite_score, extract_hard_heuristic, hard_fail, recommendation
from alice_core.engine_config import save
from alice_core.filters import snippet_gate
from alice_core.schemas import JobEvaluation, Listing
from tests.conftest import good_listing


def test_defaults_keep_legacy_weights():
    e = JobEvaluation(
        score_skills=5.0,
        score_experience=4.0,
        score_location=3.0,
        score_trajectory=2.0,
        score_culture=1.0,
    )
    assert composite_score(e) == 3.60


def test_saved_pay_band_archives_out_of_range(monkeypatch):
    save({"role": {"payMin": 40, "payMax": 45, "maxHeadcount": 20}})
    listing = good_listing(pay_text="$55/hr", snippet="8 people worldwide $55/hr")
    listing = listing.model_copy(update={"description": listing.description.replace("$50", "$55")})
    ok, reason = snippet_gate(listing)
    assert ok is False
    assert "55" in reason


def test_operator_prompts_persist_and_append():
    from alice_core.engine_config import cv_system_prompt, email_system_prompt, load

    save(
        {
            "prompts": {
                "cvSystem": "Prefer short bullets. British English.",
                "emailSystem": "Ask for a 15-minute call.",
            }
        }
    )
    cfg = load()
    assert "British English" in cfg["prompts"]["cvSystem"]
    assert "15-minute" in cfg["prompts"]["emailSystem"]
    assert "Operator instructions" in cv_system_prompt()
    assert "British English" in cv_system_prompt()
    assert "Ask for a 15-minute call." in email_system_prompt()
    assert "Never add tools" in cv_system_prompt()
    assert "5-8 sentence" in email_system_prompt()


def test_headcount_cap_from_setup():
    save({"role": {"maxHeadcount": 10, "payMin": 40, "payMax": 60}})
    listing = Listing(
        source="t",
        title="Engineer",
        company="Midco",
        source_url="https://example.test/mid",
        description="We are 15 people, fully remote worldwide. Pay is $50/hr USD.",
        pay_text="$50/hr",
        snippet="15 people worldwide $50/hr",
    )
    h = extract_hard_heuristic(listing)
    assert h.size_headcount == 15
    assert hard_fail(h)
