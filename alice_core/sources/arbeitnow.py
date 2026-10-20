"""Arbeitnow public job-board API."""

from __future__ import annotations

from alice_core.crawl import get_json
from alice_core.schemas import Listing

API = "https://www.arbeitnow.com/api/job-board-api"


def parse_payload(data: object) -> list[Listing]:
    jobs = data.get("data") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return []
    out: list[Listing] = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        url = str(item.get("url") or "")
        if not title or not url:
            continue
        desc = str(item.get("description") or "")
        out.append(
            Listing(
                source="arbeitnow",
                title=title,
                company=str(item.get("company_name") or ""),
                location=str(item.get("location") or ""),
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                pay_text="",
                is_remote=bool(item.get("remote", False)),
                extra={"visa_sponsorship": item.get("visa_sponsorship", False)},
            )
        )
    return out


def pull() -> list[Listing]:
    data, _ = get_json("arbeitnow", API, params={"remote": "true"})
    return parse_payload(data)
