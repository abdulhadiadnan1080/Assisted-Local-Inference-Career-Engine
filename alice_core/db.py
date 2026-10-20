from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from alice_core.schemas import LEGAL_TRANSITIONS, Listing

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "alice.db"


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = _connect()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            identity_hash TEXT NOT NULL UNIQUE,
            content_hash TEXT NOT NULL,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            is_remote INTEGER DEFAULT 1,
            apply_url TEXT,
            source_url TEXT NOT NULL,
            description_raw TEXT,
            company_blurb TEXT,
            status TEXT NOT NULL DEFAULT 'DISCOVERED',
            shown_on DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS hard_filters (
            job_id TEXT PRIMARY KEY,
            size_headcount INTEGER,
            size_bucket TEXT,
            international_hire TEXT,
            pay_hourly_usd REAL,
            pay_band TEXT,
            evidence_json TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS evaluations (
            job_id TEXT PRIMARY KEY,
            score_skills REAL NOT NULL,
            score_experience REAL NOT NULL,
            score_location REAL NOT NULL,
            score_trajectory REAL NOT NULL,
            score_culture REAL NOT NULL,
            composite_score REAL NOT NULL,
            key_strengths TEXT NOT NULL,
            critical_gaps TEXT NOT NULL,
            really_need TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS posters (
            job_id TEXT PRIMARY KEY,
            poster_name TEXT,
            poster_title TEXT,
            poster_email TEXT,
            email_found INTEGER NOT NULL DEFAULT 0,
            evidence TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS tailored_resumes (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            typst_source TEXT NOT NULL,
            pdf_path TEXT NOT NULL,
            highlighted_changes TEXT NOT NULL,
            is_verified_grounded INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS outreach_drafts (
            id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            body_text TEXT NOT NULL,
            gmail_draft_id TEXT,
            is_sent INTEGER DEFAULT 0,
            sent_at TIMESTAMP,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS daily_batches (
            id TEXT PRIMARY KEY,
            batch_date DATE NOT NULL UNIQUE,
            job_ids TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS source_circuits (
            source TEXT PRIMARY KEY,
            paused_until TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS budgets (
            day DATE PRIMARY KEY,
            jd_fetches INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            running INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        INSERT OR IGNORE INTO pipeline_runs (id, running) VALUES (1, 0);
        INSERT OR IGNORE INTO settings (key, value) VALUES ('live_crawl', '0');
        """
    )
    conn.commit()
    conn.close()


def identity_hash(listing: Listing) -> str:
    if listing.source_url:
        key = listing.source_url.strip().lower()
    else:
        key = "|".join(
            [listing.source, listing.company, listing.title, listing.location]
        ).lower()
    return hashlib.sha256(key.encode()).hexdigest()


def content_hash(listing: Listing) -> str:
    body = listing.description or listing.snippet
    return hashlib.sha256(body.encode()).hexdigest()


def upsert_listing(listing: Listing, status: str = "DISCOVERED") -> tuple[str, bool]:
    """Return (job_id, skip_reeval)."""
    init_db()
    ident = identity_hash(listing)
    chash = content_hash(listing)
    conn = _connect()
    row = conn.execute("SELECT * FROM jobs WHERE identity_hash = ?", (ident,)).fetchone()
    now = datetime.utcnow().isoformat(timespec="seconds")
    if row:
        skip = row["content_hash"] == chash
        conn.execute(
            """
            UPDATE jobs SET title=?, company=?, location=?, apply_url=?, source_url=?,
                description_raw=?, content_hash=?, updated_at=?
            WHERE id=?
            """,
            (
                listing.title,
                listing.company,
                listing.location,
                listing.apply_url,
                listing.source_url,
                listing.description or listing.snippet,
                chash,
                now,
                row["id"],
            ),
        )
        conn.commit()
        conn.close()
        return row["id"], skip
    job_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO jobs (id, identity_hash, content_hash, source, title, company, location,
            is_remote, apply_url, source_url, description_raw, status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job_id,
            ident,
            chash,
            listing.source,
            listing.title,
            listing.company,
            listing.location,
            1 if listing.is_remote else 0,
            listing.apply_url,
            listing.source_url,
            listing.description or listing.snippet,
            status,
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return job_id, False


def set_status(job_id: str, new_status: str) -> None:
    conn = _connect()
    row = conn.execute("SELECT status, shown_on FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        conn.close()
        raise KeyError(job_id)
    old = row["status"]
    if new_status != old and new_status not in LEGAL_TRANSITIONS.get(old, set()):
        conn.close()
        raise ValueError(f"illegal transition {old} -> {new_status}")
    if new_status == "READY" and not row["shown_on"]:
        conn.close()
        raise ValueError("READY requires shown_on")
    conn.execute(
        "UPDATE jobs SET status=?, updated_at=? WHERE id=?",
        (new_status, datetime.utcnow().isoformat(timespec="seconds"), job_id),
    )
    conn.commit()
    conn.close()


def archive(job_id: str, reason: str = "") -> None:
    conn = _connect()
    row = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    if row and row["status"] != "ARCHIVED":
        try:
            set_status(job_id, "ARCHIVED")
        except ValueError:
            conn = _connect()
            conn.execute(
                "UPDATE jobs SET status='ARCHIVED', updated_at=? WHERE id=?",
                (datetime.utcnow().isoformat(timespec="seconds"), job_id),
            )
            conn.commit()
            conn.close()
    if reason:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (CACHE_DIR / f"{job_id}.reason.txt").write_text(reason)


def save_hard(job_id: str, payload: dict[str, Any]) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT OR REPLACE INTO hard_filters
        (job_id, size_headcount, size_bucket, international_hire, pay_hourly_usd, pay_band, evidence_json)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            job_id,
            payload.get("size_headcount"),
            payload.get("size_bucket"),
            payload.get("international_hire"),
            payload.get("pay_hourly_usd"),
            payload.get("pay_band"),
            json.dumps(payload.get("evidence") or []),
        ),
    )
    conn.commit()
    conn.close()


def save_eval(job_id: str, payload: dict[str, Any]) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT OR REPLACE INTO evaluations
        (job_id, score_skills, score_experience, score_location, score_trajectory, score_culture,
         composite_score, key_strengths, critical_gaps, really_need, recommendation, evaluated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            job_id,
            payload["score_skills"],
            payload["score_experience"],
            payload["score_location"],
            payload["score_trajectory"],
            payload["score_culture"],
            payload["composite_score"],
            json.dumps(payload.get("key_strengths") or []),
            json.dumps(payload.get("critical_gaps") or []),
            json.dumps(payload.get("really_need") or []),
            payload["recommendation"],
            datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


def save_poster(job_id: str, payload: dict[str, Any]) -> None:
    conn = _connect()
    email = payload.get("poster_email")
    conn.execute(
        """
        INSERT OR REPLACE INTO posters
        (job_id, poster_name, poster_title, poster_email, email_found, evidence)
        VALUES (?,?,?,?,?,?)
        """,
        (
            job_id,
            payload.get("poster_name"),
            payload.get("poster_title"),
            email,
            1 if email else 0,
            payload.get("evidence") or "",
        ),
    )
    conn.commit()
    conn.close()


def save_resume(job_id: str, typst_source: str, pdf_path: str, grounded: bool, changes: list[str]) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO tailored_resumes (id, job_id, typst_source, pdf_path, highlighted_changes, is_verified_grounded)
        VALUES (?,?,?,?,?,?)
        """,
        (str(uuid.uuid4()), job_id, typst_source, pdf_path, json.dumps(changes), 1 if grounded else 0),
    )
    conn.commit()
    conn.close()


def save_draft(job_id: str, subject: str, body: str, gmail_draft_id: Optional[str] = None) -> str:
    conn = _connect()
    draft_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO outreach_drafts (id, job_id, subject, body_text, gmail_draft_id)
        VALUES (?,?,?,?,?)
        """,
        (draft_id, job_id, subject, body, gmail_draft_id),
    )
    conn.commit()
    conn.close()
    return draft_id


def update_draft(job_id: str, subject: str, body: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE outreach_drafts SET subject=?, body_text=? WHERE job_id=? AND is_sent=0",
        (subject, body, job_id),
    )
    conn.commit()
    conn.close()


def mark_draft_sent(job_id: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE outreach_drafts SET is_sent=1, sent_at=? WHERE job_id=?",
        (datetime.utcnow().isoformat(timespec="seconds"), job_id),
    )
    conn.commit()
    conn.close()


def circuit_open(source: str) -> bool:
    conn = _connect()
    row = conn.execute(
        "SELECT paused_until FROM source_circuits WHERE source=?", (source,)
    ).fetchone()
    conn.close()
    if not row or not row["paused_until"]:
        return False
    try:
        until = datetime.fromisoformat(row["paused_until"])
    except ValueError:
        return False
    return datetime.utcnow() < until


def trip_circuit(source: str, hours: int = 24) -> None:
    until = (datetime.utcnow() + timedelta(hours=hours)).isoformat(timespec="seconds")
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO source_circuits (source, paused_until) VALUES (?,?)",
        (source, until),
    )
    conn.commit()
    conn.close()


def jd_budget_remaining(cap: int | None = None) -> int:
    if cap is None:
        from alice_core.engine_config import jd_cap

        cap = jd_cap()
    today = date.today().isoformat()
    conn = _connect()
    row = conn.execute("SELECT jd_fetches FROM budgets WHERE day=?", (today,)).fetchone()
    conn.close()
    used = row["jd_fetches"] if row else 0
    return max(0, cap - used)


def consume_jd_fetch() -> None:
    today = date.today().isoformat()
    conn = _connect()
    conn.execute(
        """
        INSERT INTO budgets (day, jd_fetches) VALUES (?, 1)
        ON CONFLICT(day) DO UPDATE SET jd_fetches = jd_fetches + 1
        """,
        (today,),
    )
    conn.commit()
    conn.close()


def cache_payload(url: str, body: str) -> Path:
    name = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = CACHE_DIR / f"{name}.json"
    path.write_text(body)
    return path


def fetch_backlog_rows() -> list[sqlite3.Row]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT j.*, e.composite_score, p.email_found
        FROM jobs j
        JOIN evaluations e ON e.job_id = j.id
        JOIN hard_filters hf ON hf.job_id = j.id
        LEFT JOIN posters p ON p.job_id = j.id
        WHERE j.status = 'BACKLOG' AND j.shown_on IS NULL
          AND hf.size_bucket = 'lt_20'
          AND hf.international_hire = 'yes'
          AND hf.pay_band = 'in_band'
        """
    ).fetchall()
    conn.close()
    return list(rows)


def stamp_shown(job_ids: list[str], today: date) -> None:
    conn = _connect()
    now = datetime.utcnow().isoformat(timespec="seconds")
    for job_id in job_ids:
        conn.execute(
            "UPDATE jobs SET shown_on=?, status='READY', updated_at=? WHERE id=?",
            (today.isoformat(), now, job_id),
        )
    conn.commit()
    conn.close()


def write_daily_batch(today: date, job_ids: list[str]) -> None:
    conn = _connect()
    conn.execute(
        "INSERT OR REPLACE INTO daily_batches (id, batch_date, job_ids) VALUES (?,?,?)",
        (today.isoformat(), today.isoformat(), json.dumps(job_ids)),
    )
    conn.commit()
    conn.close()


def existing_batch(today: date) -> Optional[list[str]]:
    conn = _connect()
    row = conn.execute(
        "SELECT job_ids FROM daily_batches WHERE batch_date=?", (today.isoformat(),)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return json.loads(row["job_ids"])


def job_row(job_id: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    conn.close()
    return row


def try_begin_run() -> bool:
    conn = _connect()
    row = conn.execute("SELECT running FROM pipeline_runs WHERE id=1").fetchone()
    if row and row["running"]:
        conn.close()
        return False
    conn.execute(
        "UPDATE pipeline_runs SET running=1, started_at=? WHERE id=1",
        (datetime.utcnow().isoformat(timespec="seconds"),),
    )
    conn.commit()
    conn.close()
    return True


def end_run() -> None:
    conn = _connect()
    conn.execute("UPDATE pipeline_runs SET running=0 WHERE id=1")
    conn.commit()
    conn.close()


def counts() -> dict[str, int]:
    conn = _connect()
    out = {}
    for status in (
        "BACKLOG",
        "READY",
        "NEEDS_REVIEW",
        "ARCHIVED",
        "APPLIED",
        "SENT",
        "BOTH",
        "SKIPPED",
    ):
        out[status] = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE status=?", (status,)
        ).fetchone()["n"]
    conn.close()
    return out


def card_query(where: str, params: tuple = ()) -> list[dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        f"""
        SELECT j.*, hf.size_headcount, hf.size_bucket, hf.international_hire, hf.pay_hourly_usd, hf.pay_band,
               e.score_skills, e.score_experience, e.score_location, e.score_trajectory,
               e.score_culture, e.composite_score, e.really_need,
               p.poster_name, p.poster_title, p.poster_email, p.email_found,
               d.subject, d.body_text, d.gmail_draft_id,
               r.pdf_path
        FROM jobs j
        LEFT JOIN hard_filters hf ON hf.job_id = j.id
        LEFT JOIN evaluations e ON e.job_id = j.id
        LEFT JOIN posters p ON p.job_id = j.id
        LEFT JOIN outreach_drafts d ON d.id = (
            SELECT id FROM outreach_drafts WHERE job_id = j.id ORDER BY rowid DESC LIMIT 1
        )
        LEFT JOIN tailored_resumes r ON r.id = (
            SELECT id FROM tailored_resumes WHERE job_id = j.id ORDER BY created_at DESC LIMIT 1
        )
        WHERE {where}
        ORDER BY e.composite_score DESC, j.updated_at DESC
        """,
        params,
    ).fetchall()
    conn.close()
    cards = []
    for row in rows:
        item = dict(row)
        if item.get("really_need"):
            try:
                item["really_need"] = json.loads(item["really_need"])
            except json.JSONDecodeError:
                item["really_need"] = []
        else:
            item["really_need"] = []
        item["email_found"] = bool(item.get("email_found"))
        item["gmail_ready"] = bool(item.get("gmail_draft_id"))
        cards.append(item)
    return cards


def mark_applied(job_id: str) -> None:
    row = job_row(job_id)
    if not row:
        raise KeyError(job_id)
    if row["status"] == "SENT":
        set_status(job_id, "BOTH")
    elif row["status"] == "APPLIED":
        return
    else:
        set_status(job_id, "APPLIED")


def mark_sent(job_id: str) -> None:
    row = job_row(job_id)
    if not row:
        raise KeyError(job_id)
    if row["status"] == "APPLIED":
        set_status(job_id, "BOTH")
    elif row["status"] == "BOTH":
        return
    else:
        set_status(job_id, "SENT")


def mark_skipped(job_id: str) -> None:
    row = job_row(job_id)
    if not row:
        raise KeyError(job_id)
    if row["status"] in {"SKIPPED", "BOTH"}:
        return
    set_status(job_id, "SKIPPED")


def latest_draft(job_id: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM outreach_drafts WHERE job_id=? ORDER BY rowid DESC LIMIT 1",
        (job_id,),
    ).fetchone()
    conn.close()
    return row


def set_gmail_draft_id(job_id: str, gmail_draft_id: str) -> None:
    conn = _connect()
    conn.execute(
        """
        UPDATE outreach_drafts SET gmail_draft_id=?
        WHERE id = (SELECT id FROM outreach_drafts WHERE job_id=? ORDER BY rowid DESC LIMIT 1)
        """,
        (gmail_draft_id, job_id),
    )
    conn.commit()
    conn.close()


def hard_row(job_id: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute("SELECT * FROM hard_filters WHERE job_id=?", (job_id,)).fetchone()
    conn.close()
    return row


def eval_row(job_id: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute("SELECT * FROM evaluations WHERE job_id=?", (job_id,)).fetchone()
    conn.close()
    return row


def listing_from_job(row: sqlite3.Row) -> Listing:
    return Listing(
        source=row["source"],
        title=row["title"],
        company=row["company"],
        location=row["location"] or "",
        apply_url=row["apply_url"] or "",
        source_url=row["source_url"],
        snippet=(row["description_raw"] or "")[:400],
        description=row["description_raw"] or "",
        is_remote=bool(row["is_remote"]),
    )


def is_running() -> bool:
    conn = _connect()
    row = conn.execute("SELECT running FROM pipeline_runs WHERE id=1").fetchone()
    conn.close()
    return bool(row and row["running"])


def force_status(job_id: str, status: str) -> None:
    conn = _connect()
    conn.execute(
        "UPDATE jobs SET status=?, updated_at=? WHERE id=?",
        (status, datetime.utcnow().isoformat(timespec="seconds"), job_id),
    )
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    init_db()
    conn = _connect()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    init_db()
    conn = _connect()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def live_crawl_enabled() -> bool:
    return get_setting("live_crawl", "0") == "1"


def set_live_crawl(enabled: bool) -> None:
    set_setting("live_crawl", "1" if enabled else "0")


def reset_runtime() -> None:
    """Wipe SQLite and the crawl cache. Live crawl stays off."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    if CACHE_DIR.exists():
        for path in CACHE_DIR.iterdir():
            if path.is_file():
                path.unlink()
    init_db()
    set_live_crawl(False)
