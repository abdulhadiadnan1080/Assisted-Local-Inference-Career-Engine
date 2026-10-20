"""Remotive public remote software-dev API."""

from __future__ import annotations

from alice_core.crawl import get_json
from alice_core.schemas import Listing

API = "https://remotive.com/api/remote-jobs"


def parse_payload(data: object) -> list[Listing]:
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return []
    out: list[Listing] = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        loc = str(item.get("candidate_required_location") or "")
        title = str(item.get("title") or "")
        url = str(item.get("url") or item.get("url") or "")
        if not title or not url:
            continue
        desc = str(item.get("description") or "")
        out.append(
            Listing(
                source="remotive",
                title=title,
                company=str(item.get("company_name") or ""),
                location=loc or "Remote",
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                pay_text=str(item.get("salary") or ""),
                is_remote=True,
            )
        )
    return out


def pull() -> list[Listing]:
    data, _ = get_json("remotive", API, params={"category": "software-dev"})
    return parse_payload(data)
