"""Orchestrator. Human Apply/Send stay in the dashboard. Worker never sends mail or submits forms."""

from __future__ import annotations

import threading
from datetime import date
from typing import Callable, Iterable

from alice_core import db
from alice_core.crawl import fetch_jd, pull_all
from alice_core.evaluator import (
    composite_score,
    extract_hard,
    hard_fail,
    hard_unknown,
    recommendation,
    score_job,
)
from alice_core.filters import snippet_gate
from alice_core.poster import resolve_poster
from alice_core.profile import load_profile
from alice_core.ranker import select_daily_fifteen
from alice_core.schemas import Listing
from alice_core.tailor import compile_typst, tailor_and_audit, write_email

_stop = threading.Event()
_in_flight = False
_gate = threading.Lock()


def request_stop() -> None:
    _stop.set()


def stop_requested() -> bool:
    return _stop.is_set()


def pipeline_busy() -> bool:
    return _in_flight or db.is_running()


StageFn = Callable[[str, str, str], None]


def _noop_stage(name: str, state: str, detail: str) -> None:
    return None


def process_listing(
    listing: Listing,
    profile: dict,
    tailor: bool = True,
    force: bool = False,
    on_stage: StageFn | None = None,
) -> str:
    stage = on_stage or _noop_stage
    job_id, skip = db.upsert_listing(listing, status="DISCOVERED")
    if skip and not force:
        row = db.job_row(job_id)
        stage("read", "skip", "already seen, not reprocessing")
        return row["status"] if row else "DISCOVERED"
    stage("read", "ok", f"{listing.title} at {listing.company}")

    ok, reason = snippet_gate(listing)
    if not ok:
        try:
            db.set_status(job_id, "SNIPPET_FILTERED")
        except ValueError:
            pass
        db.archive(job_id, reason)
        stage("snippet", "fail", reason)
        return "ARCHIVED"
    stage("snippet", "ok", "no obvious disqualifier")

    try:
        db.set_status(job_id, "SNIPPET_FILTERED")
    except ValueError:
        pass

    try:
        text, _counted = fetch_jd(listing.source, listing)
    except Exception:
        text = listing.description or listing.snippet
    if text:
        listing = listing.model_copy(update={"description": text})
        db.upsert_listing(listing)
        try:
            db.set_status(job_id, "JD_FETCHED")
        except ValueError:
            pass
        stage("fetch", "ok", f"{len(text)} characters of description")
    elif db.jd_budget_remaining() <= 0 and len(listing.description or "") < 400:
        stage("fetch", "fail", "daily fetch budget exhausted")
        return "SNIPPET_FILTERED"
    else:
        stage("fetch", "skip", "no description available")

    hard = extract_hard(listing)
    db.save_hard(job_id, hard.model_dump())
    if hard_fail(hard):
        db.archive(job_id, "hard filter fail: " + ",".join(hard.evidence))
        stage("gate_a", "fail", "; ".join(hard.evidence) or "outside hard parameters")
        return "ARCHIVED"
    if hard_unknown(hard):
        db.force_status(job_id, "NEEDS_REVIEW")
        stage("gate_a", "skip", "size or pay unknown, held for review")
        return "NEEDS_REVIEW"
    stage("gate_a", "ok", f"{hard.size_bucket}, {hard.pay_band}, hires {hard.international_hire}")

    ev = score_job(listing, profile)
    comp = composite_score(ev)
    rec = recommendation(comp)
    db.save_eval(
        job_id,
        {
            **ev.model_dump(),
            "composite_score": comp,
            "recommendation": rec,
        },
    )
    from alice_core.engine_config import threshold as score_threshold

    if rec != "PROCEED":
        cut = score_threshold()
        db.archive(job_id, f"composite {comp} < {cut}")
        stage("gate_b", "fail", f"composite {comp} below {cut}")
        return "ARCHIVED"
    stage("gate_b", "ok", f"composite {comp}")

    poster = resolve_poster(listing)
    db.save_poster(job_id, poster.model_dump())
    stage(
        "poster",
        "ok" if poster.poster_email else "skip",
        poster.poster_email or "no public address, apply only",
    )

    if tailor:
        tailored = tailor_and_audit(listing, ev.really_need, profile)
        _typ, pdf_path, _g = compile_typst(job_id, listing, tailored, profile)
        stage("tailor", "ok", f"{len(tailored.bullets)} bullets grounded in the profile")
        draft = write_email(listing, poster.poster_name, ev.really_need, profile)
        gmail_id = None
        try:
            from alice_core.mailer import create_draft

            gmail_id = create_draft(poster.poster_email or "", draft.subject, draft.body_text, pdf_path)
        except Exception:
            gmail_id = None
        db.save_draft(job_id, draft.subject, draft.body_text, gmail_id)
        stage("draft", "ok" if gmail_id else "skip", "saved to Gmail" if gmail_id else "saved locally, Gmail not connected")
    else:
        stage("tailor", "skip", "tailoring disabled for this run")
        stage("draft", "skip", "no letter written")

    db.force_status(job_id, "BACKLOG")
    return "BACKLOG"


def promote(job_id: str) -> str:
    """Tailor a NEEDS_REVIEW job. Does not invent size. Does not auto-READY."""
    row = db.job_row(job_id)
    if not row:
        raise KeyError(job_id)
    listing = db.listing_from_job(row)
    profile = load_profile()
    hard = extract_hard(listing)
    db.save_hard(job_id, hard.model_dump())
    if hard_fail(hard):
        db.archive(job_id, "promoted but hard-fail")
        return "ARCHIVED"
    if hard_unknown(hard):
        ev = score_job(listing, profile)
        comp = composite_score(ev)
        db.save_eval(job_id, {**ev.model_dump(), "composite_score": comp, "recommendation": recommendation(comp)})
        poster = resolve_poster(listing)
        db.save_poster(job_id, poster.model_dump())
        tailored = tailor_and_audit(listing, ev.really_need, profile)
        compile_typst(job_id, listing, tailored, profile)
        draft = write_email(listing, poster.poster_name, ev.really_need, profile)
        db.save_draft(job_id, draft.subject, draft.body_text, None)
        db.force_status(job_id, "NEEDS_REVIEW")
        return "NEEDS_REVIEW"
    return process_listing(listing, profile, tailor=True)


def run(
    listings: Iterable[Listing] | None = None,
    today: date | None = None,
    pull: Callable[[], list[Listing]] | None = None,
    tailor: bool = True,
) -> dict:
    global _in_flight
    with _gate:
        if _in_flight or not db.try_begin_run():
            return {"ok": False, "reason": "already running"}
        _in_flight = True
        _stop.clear()
    try:
        db.init_db()
        if listings is None and pull is None and not db.live_crawl_enabled():
            return {"ok": False, "reason": "live crawl is off", "today": [], "count": 0}
        profile = load_profile()
        items = list(listings) if listings is not None else (pull() if pull else pull_all())
        tallies: dict[str, int] = {}
        for item in items:
            if _stop.is_set():
                break
            status = process_listing(item, profile, tailor=tailor)
            tallies[status] = tallies.get(status, 0) + 1
        ready_ids = select_daily_fifteen(today or date.today())
        return {"ok": True, "tallies": tallies, "today": ready_ids, "count": len(ready_ids), "stopped": _stop.is_set()}
    finally:
        with _gate:
            _in_flight = False
            db.end_run()
            _stop.clear()


DEMO = [
    {
        "company": "Lumen Thread",
        "title": "Founding inference engineer",
        "email": "maya@lumenthread.dev",
        "need": ["Own the local-model serving path", "Keep the stack tiny", "Ship weekly with a 6-person team"],
        "pay": 52,
        "skills": 4.6,
    },
    {
        "company": "Paperkite",
        "title": "Senior Python engineer",
        "email": "jon@paperkite.io",
        "need": ["FastAPI services", "SQLite-backed products", "Clear written comms"],
        "pay": 48,
        "skills": 4.4,
    },
    {
        "company": "Northwisp",
        "title": "MLX / on-device engineer",
        "email": None,
        "need": ["Apple Silicon inference", "Quantization tradeoffs", "No cloud fallback"],
        "pay": 55,
        "skills": 4.8,
    },
    {
        "company": "Harborline",
        "title": "Full-stack for a 9-person studio",
        "email": "ada@harborline.co",
        "need": ["Typst or PDF pipelines", "Operator dashboards", "Remote worldwide"],
        "pay": 45,
        "skills": 4.1,
    },
    {
        "company": "Saltbox Labs",
        "title": "Agent runtime engineer",
        "email": "priya@saltbox.labs",
        "need": ["Tool-calling without SaaS", "Eval harnesses", "Human-in-the-loop gates"],
        "pay": 50,
        "skills": 4.5,
    },
]


def seed_demo(today: date | None = None, n: int = 15) -> list[str]:
    """Sample deck so Today is not empty on first boot. Not a live crawl."""
    db.init_db()
    today = today or date.today()
    profile = load_profile()
    ids: list[str] = []
    palette = DEMO * 4
    for i in range(n):
        item = palette[i]
        company = item["company"] if i < 5 else f"{item['company']} {chr(65 + i)}"
        email = item["email"]
        listing = Listing(
            source="demo",
            title=item["title"],
            company=company,
            location="Worldwide",
            apply_url=f"https://jobs.example.test/{i+1}",
            source_url=f"https://jobs.example.test/{i+1}",
            snippet=(
                f"Seed-stage team of 8 people. Remote worldwide. ${item['pay']}/hr. "
                + (f"Contact {email}. " if email else "")
                + " ".join(item["need"])
            ),
            description=(
                f"We are 8 people, fully remote, worldwide. Pay is ${item['pay']}/hr USD. "
                f"Visa-friendly. Seed founding engineer energy. Python, FastAPI, MLX, inference. "
                f"Small team. "
                + (f"Email the poster at {email}. " if email else "No email on the posting. ")
                + " ".join(item["need"])
            ),
            pay_text=f"${item['pay']}/hr",
            is_remote=True,
        )
        process_listing(listing, profile, tailor=True, force=True)
        job_id, _ = db.upsert_listing(listing)
        ids.append(job_id)
    placeholders = ",".join("?" * len(ids))
    conn = db._connect()
    conn.execute(
        f"UPDATE jobs SET shown_on=NULL, status='BACKLOG' WHERE id IN ({placeholders})",
        ids,
    )
    conn.execute("DELETE FROM daily_batches WHERE batch_date=?", (today.isoformat(),))
    conn.commit()
    conn.close()
    return select_daily_fifteen(today)
