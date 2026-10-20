import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_PARTS = {"venv", ".venv", "__pycache__", "tests"}


def _corpus() -> str:
    chunks = []
    for path in ROOT.rglob("*"):
        if any(p in SKIP_PARTS for p in path.parts):
            continue
        if path.suffix not in {".py", ".txt", ".md", ".yaml", ".yml", ".html", ".js"}:
            continue
        chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks)


def test_kill_list():
    text = _corpus()
    assert "mixed_people" not in text
    assert "PIPELINE_STATE" not in text
    assert "hermes-agent" not in text
    assert not re.search(r"""f["']contact@\{""", text)
    assert not re.search(r"""f["']jobs@\{""", text)
    req = (ROOT / "requirements.txt").read_text()
    assert "hermes-agent" not in req
    assert "apollo" not in req.lower()
    assert "hunter" not in req.lower()


def test_composite_not_on_jobevaluation():
    src = (ROOT / "alice_core" / "schemas.py").read_text()
    assert "class JobEvaluation" in src
    block = src.split("class JobEvaluation")[1].split("class ")[0]
    assert "composite_score" not in block
    assert "recommendation" not in block


def test_never_binds_port_8000():
    app = (ROOT / "app.py").read_text()
    readme = (ROOT / "README.md").read_text()
    assert "127.0.0.1:8000" not in app
    assert "port=8000" not in app.replace(" ", "")
    assert "127.0.0.1:8471" in readme
    assert "PORT == 8000" in app
