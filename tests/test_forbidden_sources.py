from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_worker_never_sends():
    src = (ROOT / "alice_core" / "pipeline.py").read_text()
    assert "drafts.send" not in src
    assert "messages.send" not in src
    assert "send_draft(" not in src
    assert "Easy Apply" not in src or "open" in src.lower()


def test_no_unattended_apply_in_pipeline():
    src = (ROOT / "alice_core" / "pipeline.py").read_text()
    assert "httpx.post" not in src
    assert "workday" not in src.lower()
    app = (ROOT / "app.py").read_text()
    assert "window.open" in (ROOT / "static" / "alice.js").read_text()
    assert "httpx.post" not in app
