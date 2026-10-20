import json
from pathlib import Path

from alice_core.profile import load_profile
from alice_core.schemas import ResumeTailorOutput, TailoredBullet
from alice_core.tailor import audit_output

FIXTURE = Path(__file__).parent / "fixtures" / "hallucinations.json"


def test_ungrounded_tools_reverted():
    profile = load_profile()
    rows = json.loads(FIXTURE.read_text())
    original = "Built a local FastAPI control plane over SQLite for a 6-person product team."
    drafted = ResumeTailorOutput(
        tailored_summary=rows[0]["summary"],
        optimized_skills=rows[0]["skills"],
        bullets=[
            TailoredBullet(
                original_text=original,
                rewritten_text=rows[0]["bullet"],
                grounded_in_truth=True,
            )
        ],
    )
    audited = audit_output(drafted, profile)
    text = " ".join(b.rewritten_text for b in audited.bullets).lower()
    assert "kubernetes" not in text
    assert "hadoop" not in text
    assert audited.bullets[0].rewritten_text == original
    assert audited.bullets[0].grounded_in_truth is False
