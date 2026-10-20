"""Green/red probes for the dashboard. Network pings do not go through the crawler, so they never trip a circuit."""

from __future__ import annotations

import importlib
import shutil
from typing import Any, Callable

import httpx

from alice_core import db, engine_config
from alice_core.mailer import credentials_path, gmail_connected, token_path
from alice_core.profile import load_profile
from alice_core.schemas import Listing

ProbeFn = Callable[[], dict[str, Any]]


def _ok(detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": "ok", "detail": detail, **extra}


def _fail(detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": "fail", "detail": detail, **extra}


def _warn(detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": "warn", "detail": detail, **extra}


def probe_sqlite() -> dict[str, Any]:
    db.init_db()
    counts = db.counts()
    return _ok(f"SQLite at {db.DB_PATH.name} · {sum(counts.values())} jobs")


def probe_setup_roundtrip() -> dict[str, Any]:
    cfg = engine_config.load()
    lo, hi = engine_config.pay_band()
    return _ok(
        f"pay ${lo:.0f}–{hi:.0f}/hr · under {engine_config.max_headcount()} people · "
        f"release {engine_config.daily_release()} · threshold {engine_config.threshold()}"
        f" · {len(cfg['engine']['sources'])} sources"
    )


def probe_ui_backend() -> dict[str, Any]:
    return _ok("API process is serving this response")


def probe_ollama() -> dict[str, Any]:
    host = engine_config.ollama_host().rstrip("/")
    try:
        resp = httpx.get(f"{host}/api/tags", timeout=2.0)
        if resp.status_code != 200:
            return _fail(f"Ollama HTTP {resp.status_code} at {host}")
        names = [m.get("name") for m in resp.json().get("models", [])]
        return _ok(f"reachable · {len(names)} models", installed=names)
    except Exception as exc:
        return _fail(f"not reachable at {host}: {exc}")


def _ping_model(model: str) -> dict[str, Any]:
    host = engine_config.ollama_host().rstrip("/")
    tags = probe_ollama()
    if tags["status"] != "ok":
        return tags
    installed = tags.get("installed") or []
    if model not in installed and not any(model in str(n) for n in installed):
        return _fail(f"{model} is not installed. Run: ollama pull {model}")
    try:
        resp = httpx.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": "ok", "stream": False, "keep_alive": "0", "options": {"num_predict": 1}},
            timeout=45.0,
        )
        if resp.status_code != 200:
            return _fail(f"{model} HTTP {resp.status_code}")
        text = (resp.json().get("response") or "").strip()
        return _ok(f"{model} answered" + (f": {text[:40]}" if text else ""))
    except Exception as exc:
        return _fail(f"{model} did not generate: {exc}")


def probe_hermes() -> dict[str, Any]:
    return _ping_model(engine_config.scoring_model())


def probe_gemma() -> dict[str, Any]:
    return _ping_model(engine_config.writing_model())


def probe_instructor() -> dict[str, Any]:
    try:
        import instructor  # noqa: F401
        import openai  # noqa: F401
    except Exception as exc:
        return _fail(f"structured output client missing: {exc}")
    return _ok("instructor + openai client import")


def probe_typst() -> dict[str, Any]:
    path = shutil.which("typst")
    if not path:
        return _fail("typst is not on PATH — CVs stay JSON/text until `brew install typst`")
    return _ok(path)


def probe_gmail() -> dict[str, Any]:
    creds = credentials_path()
    token = token_path()
    if gmail_connected():
        return _ok(f"token at {token.name}")
    if creds.exists():
        return _warn(f"credentials.json present, no token yet — complete OAuth once")
    return _fail(f"no Gmail credentials at {creds}")


def probe_profile() -> dict[str, Any]:
    from pathlib import Path

    from alice_core.profile import PROFILE_PATH

    data = load_profile()
    name = (data.get("candidate") or {}).get("full_name") or "unnamed"
    using_example = not Path(PROFILE_PATH).exists()
    if using_example:
        return _warn(f"using example profile ({name}) — copy master_profile.example.yaml")
    return _ok(f"master profile for {name}")


def probe_cv_tailor() -> dict[str, Any]:
    from alice_core.tailor import _heuristic_tailor, audit_output

    listing = Listing(
        source="probe",
        title="Python engineer",
        company="Probe Co",
        source_url="https://example.test/probe",
        description="Python FastAPI SQLite for a small remote team.",
    )
    drafted = _heuristic_tailor(listing, ["Ship FastAPI"], load_profile())
    audited = audit_output(drafted, load_profile())
    if not audited.tailored_summary:
        return _fail("tailor produced an empty summary")
    return _ok(f"heuristic tailor produced {len(audited.bullets)} grounded bullets")


def probe_gate_a() -> dict[str, Any]:
    from alice_core.evaluator import extract_hard_heuristic, hard_fail

    listing = Listing(
        source="probe",
        title="Senior Python engineer",
        company="TinyCo",
        location="Worldwide",
        source_url="https://example.test/gate",
        snippet="8 people, remote worldwide, $50/hr, Python FastAPI.",
        description="We are 8 people, fully remote, worldwide. Pay is $50/hr USD.",
        pay_text="$50/hr",
    )
    hard = extract_hard_heuristic(listing)
    if hard_fail(hard):
        return _fail(f"good listing failed Gate A: {hard.evidence}")
    return _ok(f"Gate A extracts {hard.size_bucket}, {hard.pay_band}, hires {hard.international_hire}")


def probe_jobspy_import() -> dict[str, Any]:
    enabled = "jobspy" in engine_config.enabled_source_ids()
    try:
        importlib.import_module("jobspy")
    except Exception as exc:
        if enabled:
            return _fail(f"JobSpy enabled but python-jobspy is missing: {exc}")
        return _warn("python-jobspy not installed · LinkedIn/Indeed off")
    return _ok("python-jobspy importable")


def _ping_url(url: str) -> dict[str, Any]:
    try:
        resp = httpx.get(url, timeout=8.0, follow_redirects=True, headers={"User-Agent": "ALICE/0.1 diagnostics"})
        code = resp.status_code
        if code in {200, 201}:
            return _ok(f"HTTP {code}")
        if code in {401, 403, 429}:
            return _warn(f"HTTP {code} — board reachable but guarded")
        return _fail(f"HTTP {code}")
    except Exception as exc:
        return _fail(str(exc))


def _source_probe(source_id: str) -> ProbeFn:
    def run() -> dict[str, Any]:
        meta = next((row for row in engine_config.SOURCE_CATALOG if row[0] == source_id), None)
        enabled = source_id in engine_config.enabled_source_ids()
        if source_id == "jobspy":
            inner = probe_jobspy_import()
            inner["enabled"] = enabled
            return inner
        if not meta or not meta[2]:
            return _fail("no probe URL")
        if db.circuit_open(source_id):
            return _warn("circuit open from a previous 429/403")
        result = _ping_url(meta[2])
        result["enabled"] = enabled
        if not enabled and result["status"] == "ok":
            result["detail"] += " · source is switched off in Setup"
        return result

    run.__name__ = f"probe_{source_id}"
    return run


CHECKS: list[dict[str, Any]] = [
    {"id": "backend", "group": "Core", "title": "API / UI connection", "fn": probe_ui_backend},
    {"id": "sqlite", "group": "Core", "title": "SQLite", "fn": probe_sqlite},
    {"id": "setup", "group": "Core", "title": "Setup drives the engine", "fn": probe_setup_roundtrip},
    {"id": "profile", "group": "Core", "title": "Master profile", "fn": probe_profile},
    {"id": "gate_a", "group": "Core", "title": "Gate A heuristics", "fn": probe_gate_a},
    {"id": "ollama", "group": "Models", "title": "Ollama", "fn": probe_ollama},
    {"id": "instructor", "group": "Models", "title": "Instructor client", "fn": probe_instructor},
    {"id": "hermes", "group": "Models", "title": "Hermes (scoring)", "fn": probe_hermes},
    {"id": "gemma", "group": "Models", "title": "Gemma (writing)", "fn": probe_gemma},
    {"id": "typst", "group": "Paper", "title": "Typst PDF compiler", "fn": probe_typst},
    {"id": "cv", "group": "Paper", "title": "CV tailoring", "fn": probe_cv_tailor},
    {"id": "gmail", "group": "Mail", "title": "Gmail API", "fn": probe_gmail},
    {"id": "jobspy", "group": "Boards", "title": "JobSpy (LinkedIn / Indeed)", "fn": probe_jobspy_import},
]

for _sid, _label, _url in engine_config.SOURCE_CATALOG:
    if _sid == "jobspy":
        continue
    CHECKS.append({"id": f"src_{_sid}", "group": "Boards", "title": _label, "fn": _source_probe(_sid)})


def catalog() -> list[dict[str, str]]:
    return [{"id": c["id"], "group": c["group"], "title": c["title"]} for c in CHECKS]


def run_one(check_id: str) -> dict[str, Any]:
    match = next((c for c in CHECKS if c["id"] == check_id), None)
    if not match:
        return {"id": check_id, "title": check_id, "group": "Unknown", "status": "fail", "detail": "unknown check"}
    try:
        result = match["fn"]()
    except Exception as exc:
        result = _fail(str(exc))
    return {"id": match["id"], "title": match["title"], "group": match["group"], **result}


def run_all(ids: list[str] | None = None) -> list[dict[str, Any]]:
    wanted = ids or [c["id"] for c in CHECKS]
    return [run_one(check_id) for check_id in wanted]
