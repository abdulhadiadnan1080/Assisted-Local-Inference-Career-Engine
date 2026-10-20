"""JSON API for the React frontend. Same SQLite source of truth as the Jinja board."""

from __future__ import annotations

import json
import re
import threading
import uuid
from datetime import date, datetime
from typing import Any, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from alice_core import db, engine_config
from alice_core.profile import load_profile
from alice_core.schemas import Listing

router = APIRouter(prefix="/api")

ARTIFACTS = db.ROOT / "artifacts" / "resumes"
BRIEFING_STATUSES = "('READY','APPLIED','SENT','BOTH')"

# The frontend speaks a smaller vocabulary than the state machine.
STATUS_MAP = {
    "READY": "ready",
    "APPLIED": "applied",
    "SENT": "sent",
    "BOTH": "applied",
    "NEEDS_REVIEW": "review",
    "BACKLOG": "new",
    "ARCHIVED": "archived",
    "SKIPPED": "skipped",
}


# ---------------------------------------------------------------- serializing


def _pay(card: dict[str, Any]) -> str:
    rate = card.get("pay_hourly_usd")
    if not rate:
        return "Unknown"
    return f"${rate:.0f}/hr"


def _size(card: dict[str, Any]) -> str:
    head = card.get("size_headcount")
    if head:
        return f"{head} people"
    bucket = card.get("size_bucket")
    if bucket == "lt_20":
        return "Under 20"
    if bucket == "ge_20":
        return "20 or more"
    return "Unknown"


def _posted(card: dict[str, Any]) -> str:
    raw = card.get("created_at") or card.get("updated_at") or ""
    try:
        stamp = datetime.fromisoformat(str(raw).replace("Z", ""))
    except ValueError:
        return str(raw)[:16]
    if stamp.date() == date.today():
        return f"Today, {stamp.strftime('%H:%M')}"
    return stamp.strftime("%d %b, %H:%M")


def _profile_resume(job_id: str, card: dict[str, Any]) -> dict[str, Any]:
    """Prefer the compiled artifact. Fall back to the master profile."""
    path = ARTIFACTS / job_id / "resume.json"
    if path.exists():
        try:
            payload = json.loads(path.read_text())
            bullets: list[str] = []
            for role in payload.get("experience") or []:
                bullets.extend(role.get("bullets") or [])
            return {
                "fileName": f"{(payload.get('name') or 'resume').replace(' ', '-')}.pdf",
                "headline": payload.get("headline") or card.get("title") or "",
                "summary": payload.get("summary") or "",
                "skills": payload.get("skills") or [],
                "bullets": bullets[:6],
            }
        except (json.JSONDecodeError, OSError):
            pass

    profile = load_profile()
    candidate = profile.get("candidate") or {}
    skills = profile.get("skills") or {}
    flat = [*(skills.get("languages") or []), *(skills.get("frameworks") or []), *(skills.get("infrastructure") or [])]
    bullets = []
    for role in profile.get("experience") or []:
        for bullet in role.get("bullets") or []:
            bullets.append(bullet if isinstance(bullet, str) else str(bullet.get("text") or ""))
    return {
        "fileName": f"{(candidate.get('full_name') or 'resume').replace(' ', '-')}.pdf",
        "headline": candidate.get("headline") or card.get("title") or "",
        "summary": (profile.get("summary_foundation") or {}).get("summary") or "",
        "skills": flat[:12],
        "bullets": bullets[:6],
        "pending": True,
    }


def job_json(card: dict[str, Any]) -> dict[str, Any]:
    job_id = card["id"]
    status = card.get("status") or "DISCOVERED"
    scores = {
        "skills": card.get("score_skills") or 0,
        "experience": card.get("score_experience") or 0,
        "location": card.get("score_location") or 0,
        "trajectory": card.get("score_trajectory") or 0,
        "culture": card.get("score_culture") or 0,
        "composite": card.get("composite_score") or 0,
    }
    return {
        "id": job_id,
        "company": card.get("company") or "",
        "title": card.get("title") or "",
        "location": card.get("location") or "",
        "source": card.get("source") or "",
        "pay": _pay(card),
        "size": _size(card),
        "international": card.get("international_hire") == "yes",
        "applyUrl": card.get("apply_url") or card.get("source_url") or "",
        "sourceUrl": card.get("source_url") or "",
        "status": STATUS_MAP.get(status, "new"),
        "rawStatus": status,
        "posted": _posted(card),
        "snippet": (card.get("description_raw") or "")[:220],
        "description": card.get("description_raw") or "",
        "need": card.get("really_need") or [],
        "scores": scores,
        "resume": _profile_resume(job_id, card),
        "letter": {
            "to": card.get("poster_email"),
            "toName": card.get("poster_name"),
            "subject": card.get("subject") or "",
            "body": card.get("body_text") or "",
            "gmailDraft": bool(card.get("gmail_ready")),
            "sent": status in {"SENT", "BOTH"},
        },
        "briefing": bool(card.get("shown_on")) and status in {"READY", "APPLIED", "SENT", "BOTH"},
        "pdfUrl": f"/artifacts/{job_id}" if card.get("pdf_path") else None,
    }


# -------------------------------------------------------------------- reading


def _view_clause(view: str) -> tuple[str, tuple]:
    today = date.today().isoformat()
    if view == "briefing":
        return f"j.shown_on = ? AND j.status IN {BRIEFING_STATUSES}", (today,)
    if view == "intake":
        return (
            "j.status NOT IN ('DISCOVERED') AND "
            f"NOT (j.shown_on = ? AND j.status IN {BRIEFING_STATUSES})",
            (today,),
        )
    if view == "review":
        return "j.status = 'NEEDS_REVIEW'", ()
    if view == "backlog":
        return "j.status = 'BACKLOG'", ()
    if view == "history":
        return "j.status IN ('APPLIED','SENT','BOTH','SKIPPED')", ()
    if view == "all":
        return "1=1", ()
    raise HTTPException(400, f"unknown view: {view}")


@router.get("/jobs")
def list_jobs(view: str = "briefing", limit: int = 200):
    where, params = _view_clause(view)
    cards = db.card_query(where, params)[: min(max(limit, 1), 2000)]
    return {"ok": True, "view": view, "count": len(cards), "jobs": [job_json(c) for c in cards]}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    cards = db.card_query("j.id = ?", (job_id,))
    if not cards:
        raise HTTPException(404, "unknown job")
    return {"ok": True, "job": job_json(cards[0])}


def _ollama_probe() -> dict[str, Any]:
    scoring = engine_config.scoring_model()
    writing = engine_config.writing_model()
    host = engine_config.ollama_host().rstrip("/")
    try:
        import httpx

        resp = httpx.get(f"{host}/api/tags", timeout=0.6)
        names = [m.get("name") for m in resp.json().get("models", [])] if resp.status_code == 200 else []
    except Exception:
        return {"reachable": False, "installed": [], "scoring": scoring, "writing": writing}
    return {
        "reachable": True,
        "installed": names,
        "scoring": scoring,
        "writing": writing,
        "ready": scoring in names and writing in names,
    }


@router.get("/state")
def state():
    from alice_core.mailer import gmail_connected

    profile = load_profile()
    candidate = profile.get("candidate") or {}
    return {
        "ok": True,
        "today": date.today().isoformat(),
        "liveCrawl": db.live_crawl_enabled(),
        "running": db.is_running(),
        "gmail": gmail_connected(),
        "jdBudget": db.jd_budget_remaining(),
        "counts": db.counts(),
        "ollama": _ollama_probe(),
        "candidate": {
            "name": candidate.get("full_name") or "Operator",
            "headline": candidate.get("headline") or "",
            "email": candidate.get("email") or "",
        },
    }


@router.get("/sources")
def sources():
    enabled = set(engine_config.enabled_source_ids())
    out = []
    for sid, label, _url in engine_config.SOURCE_CATALOG:
        out.append(
            {
                "id": sid,
                "name": label,
                "enabled": sid in enabled,
                "paused": db.circuit_open(sid),
            }
        )
    return {"ok": True, "sources": out}


# -------------------------------------------------------------------- config


@router.get("/config")
def get_config():
    return {"ok": True, "config": engine_config.load()}


@router.post("/config")
def save_config(body: dict):
    saved = engine_config.save(body)
    return {"ok": True, "saved": True, "config": saved}


class SourceToggle(BaseModel):
    id: str
    enabled: bool


@router.post("/sources")
def set_sources(body: SourceToggle):
    cfg = engine_config.load()
    current = list(cfg["engine"]["sources"])
    if body.enabled and body.id not in current:
        current.append(body.id)
    if not body.enabled:
        current = [s for s in current if s != body.id]
    cfg["engine"]["sources"] = current
    engine_config.save(cfg)
    return sources()


class DiagnosticsBody(BaseModel):
    ids: Optional[list[str]] = None


@router.get("/diagnostics")
def diagnostics_catalog():
    from alice_core.diagnostics import catalog

    return {"ok": True, "checks": catalog()}


@router.post("/diagnostics/run")
def diagnostics_run(body: DiagnosticsBody = DiagnosticsBody()):
    from alice_core.diagnostics import run_all

    results = run_all(body.ids)
    ok = sum(1 for r in results if r["status"] == "ok")
    fail = sum(1 for r in results if r["status"] == "fail")
    warn = sum(1 for r in results if r["status"] == "warn")
    return {"ok": True, "results": results, "summary": {"ok": ok, "fail": fail, "warn": warn}}


@router.post("/diagnostics/run/{check_id}")
def diagnostics_one(check_id: str):
    from alice_core.diagnostics import run_one

    return {"ok": True, "result": run_one(check_id)}


# ---------------------------------------------------------------- manual runs

_runs: dict[str, dict[str, Any]] = {}
_runs_lock = threading.Lock()

STAGE_ORDER = ("read", "snippet", "fetch", "gate_a", "gate_b", "poster", "tailor", "draft")


class ManualBody(BaseModel):
    url: str = ""
    text: str = ""
    company: str = ""
    title: str = ""
    tailor: bool = True


ROLE_AT_COMPANY = re.compile(
    r"^\s*(?P<title>[\w/&+.\- ]{3,60}?)\s+at\s+(?P<company>[A-Z][\w&'\-]*(?: [A-Z][\w&'\-]*){0,4})"
)


def _guess(body: ManualBody) -> tuple[str, str]:
    """Best-effort company and title. Explicit fields always win."""
    company = body.company.strip()
    title = body.title.strip()
    first_line = body.text.strip().splitlines()[0].strip() if body.text.strip() else ""

    if first_line and (not company or not title):
        match = ROLE_AT_COMPANY.match(first_line)
        if match:
            title = title or match.group("title").strip()
            company = company or match.group("company").strip(" .,")

    if not company and body.url:
        host = urlparse(body.url).hostname or ""
        parts = [p for p in host.split(".") if p not in {"www", "com", "io", "co", "dev", "org", "net", "ai"}]
        company = (parts[-1] if parts else host).title()

    if not title and first_line:
        # Stop at the first sentence break so a whole paragraph never becomes the title.
        title = re.split(r"[.!?\n]", first_line)[0][:90].strip()

    return company or "Unknown company", title or "Unknown role"


@router.post("/manual/run")
def manual_run(body: ManualBody):
    if not body.url.strip() and not body.text.strip():
        raise HTTPException(400, "give a URL or paste a description")

    run_id = uuid.uuid4().hex[:12]
    company, title = _guess(body)
    source_url = body.url.strip() or f"manual://{run_id}"
    listing = Listing(
        source="manual",
        title=title,
        company=company,
        location="",
        apply_url=body.url.strip(),
        source_url=source_url,
        snippet=body.text.strip()[:400],
        description=body.text.strip(),
    )

    with _runs_lock:
        _runs[run_id] = {
            "id": run_id,
            "stages": [],
            "done": False,
            "outcome": None,
            "error": None,
            "jobId": None,
            "startedAt": datetime.utcnow().isoformat(timespec="seconds"),
        }

    def record(name: str, state: str, detail: str) -> None:
        with _runs_lock:
            _runs[run_id]["stages"].append({"name": name, "state": state, "detail": detail})

    def worker() -> None:
        from alice_core.pipeline import process_listing

        try:
            profile = load_profile()
            outcome = process_listing(listing, profile, tailor=body.tailor, force=True, on_stage=record)
            job_id, _ = db.upsert_listing(listing)
            with _runs_lock:
                _runs[run_id]["outcome"] = outcome
                _runs[run_id]["jobId"] = job_id
        except Exception as exc:  # surfaced to the UI rather than swallowed
            with _runs_lock:
                _runs[run_id]["error"] = str(exc)
        finally:
            with _runs_lock:
                _runs[run_id]["done"] = True

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True, "runId": run_id, "stageOrder": list(STAGE_ORDER)}


@router.get("/manual/{run_id}")
def manual_status(run_id: str):
    with _runs_lock:
        run = _runs.get(run_id)
        snapshot = dict(run) if run else None
        if snapshot:
            snapshot["stages"] = list(run["stages"])
    if not snapshot:
        raise HTTPException(404, "unknown run")
    job: Optional[dict[str, Any]] = None
    if snapshot["done"] and snapshot["jobId"]:
        cards = db.card_query("j.id = ?", (snapshot["jobId"],))
        if cards:
            job = job_json(cards[0])
    return {"ok": True, "run": snapshot, "job": job, "stageOrder": list(STAGE_ORDER)}
