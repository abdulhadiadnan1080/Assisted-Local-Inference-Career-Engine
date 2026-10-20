"""Daily top 15. shown_on is forever."""

from __future__ import annotations

from datetime import date, datetime

from alice_core import db
from alice_core.engine_config import daily_release, per_company


def _created_ts(row) -> float:
    raw = row["created_at"]
    if not raw:
        return 0.0
    try:
        return datetime.fromisoformat(str(raw)).timestamp()
    except ValueError:
        return 0.0


def select_daily_fifteen(today: date | None = None) -> list[str]:
    today = today or date.today()
    existing = db.existing_batch(today)
    if existing is not None:
        return existing
    rows = db.fetch_backlog_rows()
    ranked = sorted(
        rows,
        key=lambda r: (
            -(r["composite_score"] or 0),
            0 if r["email_found"] else 1,
            -_created_ts(r),
        ),
    )
    cap = per_company()
    limit = daily_release()
    chosen: list = []
    seen_company: dict[str, int] = {}
    for row in ranked:
        company = (row["company"] or "").lower()
        if seen_company.get(company, 0) >= cap:
            continue
        chosen.append(row)
        seen_company[company] = seen_company.get(company, 0) + 1
        if len(chosen) >= limit:
            break
    ids = [r["id"] for r in chosen]
    if ids:
        db.stamp_shown(ids, today)
        db.write_daily_batch(today, ids)
    else:
        db.write_daily_batch(today, [])
    return ids
