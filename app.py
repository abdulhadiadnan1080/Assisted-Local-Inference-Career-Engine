"""ALICE local dashboard. Binds 127.0.0.1:8471. SQLite is the source of truth."""

from __future__ import annotations

import os
import sys
import threading
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HOST = "127.0.0.1"
PORT = int(os.environ.get("ALICE_PORT", "8471"))
if PORT == 8000:
    raise RuntimeError("ALICE never binds port 8000")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from alice_core import db
from alice_core.mailer import gmail_connected, send_draft
from alice_core.pipeline import pipeline_busy, promote, request_stop, run, seed_demo
from alice_core.webapi import router as api_router

FRONTEND_PORT = int(os.environ.get("ALICE_FRONTEND_PORT", "8472"))

app = FastAPI(title="ALICE", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://127.0.0.1:{FRONTEND_PORT}", f"http://localhost:{FRONTEND_PORT}"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(api_router)
templates = Jinja2Templates(directory=str(ROOT / "templates"))
static = ROOT / "static"
static.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static)), name="static")

db.init_db()
# Restarted process cannot inherit the previous worker; leftover flag stuck Automate on Running.
db.end_run()


class DraftBody(BaseModel):
    subject: str
    body_text: str


def _page(request: Request, view: str, where: str, params: tuple = ()):
    cards = db.card_query(where, params)
    stats = db.counts()
    today = date.today().isoformat()
    return templates.TemplateResponse(
        "board.html",
        {
            "request": request,
            "view": view,
            "cards": cards,
            "stats": stats,
            "today": today,
            "gmail": gmail_connected(),
            "running": db.is_running(),
            "listen": f"{HOST}:{PORT}",
            "live_crawl": db.live_crawl_enabled(),
        },
    )


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def today_board(request: Request):
    today = date.today().isoformat()
    return _page(
        request,
        "today",
        "j.shown_on = ? AND j.status IN ('READY','APPLIED','SENT','BOTH')",
        (today,),
    )


@app.get("/review")
def review_board(request: Request):
    return _page(request, "review", "j.status = 'NEEDS_REVIEW'")


@app.get("/backlog")
def backlog_board(request: Request):
    return _page(request, "backlog", "j.status = 'BACKLOG'")


@app.get("/history")
def history_board(request: Request):
    return _page(request, "history", "j.status IN ('APPLIED','SENT','BOTH','SKIPPED')")


@app.post("/api/pipeline/run")
def pipeline_run():
    if not db.live_crawl_enabled():
        return JSONResponse({"ok": False, "reason": "live crawl is off"}, status_code=403)
    if pipeline_busy():
        return JSONResponse({"ok": False, "reason": "already running"}, status_code=409)

    def worker():
        run()

    threading.Thread(target=worker, daemon=True).start()
    return {"ok": True, "started": True}


@app.post("/api/pipeline/stop")
def pipeline_stop():
    request_stop()
    db.end_run()
    return {"ok": True, "running": False, "stopped": True}


class LiveCrawlBody(BaseModel):
    enabled: bool


@app.post("/api/settings/live-crawl")
def set_live_crawl(body: LiveCrawlBody):
    db.set_live_crawl(body.enabled)
    return {"ok": True, "live_crawl": db.live_crawl_enabled()}


@app.get("/api/pipeline/status")
def pipeline_status():
    return {"running": db.is_running(), "counts": db.counts()}


@app.post("/api/demo/seed")
def demo_seed():
    ids = seed_demo(date.today(), 15)
    return {"ok": True, "today": ids, "count": len(ids)}


@app.post("/api/jobs/{job_id}/apply")
def apply_job(job_id: str):
    row = db.job_row(job_id)
    if not row:
        raise HTTPException(404, "unknown job")
    db.mark_applied(job_id)
    return {"ok": True, "apply_url": row["apply_url"], "status": "APPLIED"}


@app.post("/api/jobs/{job_id}/send")
def send_job(job_id: str):
    row = db.job_row(job_id)
    if not row:
        raise HTTPException(404, "unknown job")
    cards = db.card_query("j.id = ?", (job_id,))
    card = cards[0] if cards else {}
    if not card.get("email_found"):
        raise HTTPException(400, "no email — Apply only")
    draft = db.latest_draft(job_id)
    if not draft:
        raise HTTPException(400, "no draft")
    if not gmail_connected() or not draft["gmail_draft_id"]:
        raise HTTPException(400, "connect Gmail")
    send_draft(draft["gmail_draft_id"])
    db.mark_draft_sent(job_id)
    db.mark_sent(job_id)
    return {"ok": True, "status": "SENT"}


@app.post("/api/jobs/{job_id}/skip")
def skip_job(job_id: str):
    if not db.job_row(job_id):
        raise HTTPException(404, "unknown job")
    db.mark_skipped(job_id)
    return {"ok": True, "status": "SKIPPED"}


@app.post("/api/jobs/{job_id}/draft")
def save_draft(job_id: str, body: DraftBody):
    if not db.job_row(job_id):
        raise HTTPException(404, "unknown job")
    db.update_draft(job_id, body.subject, body.body_text)
    return {"ok": True}


@app.post("/api/jobs/{job_id}/promote")
def promote_job(job_id: str):
    if not db.job_row(job_id):
        raise HTTPException(404, "unknown job")
    status = promote(job_id)
    return {"ok": True, "status": status}


@app.get("/artifacts/{job_id}")
def artifact(job_id: str):
    cards = db.card_query("j.id = ?", (job_id,))
    if not cards or not cards[0].get("pdf_path"):
        raise HTTPException(404, "no pdf")
    path = Path(cards[0]["pdf_path"])
    if not path.exists():
        raise HTTPException(404, "no pdf")
    return FileResponse(path, media_type="application/pdf")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)
