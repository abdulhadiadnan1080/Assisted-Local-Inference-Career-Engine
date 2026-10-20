"""Himalayas public /jobs/api/search. No auth header."""

from __future__ import annotations

from alice_core.crawl import get_json
from alice_core.schemas import Listing

API = "https://himalayas.app/jobs/api/search"


def parse_payload(data: object) -> list[Listing]:
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return []
    out: list[Listing] = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "")
        url = str(item.get("applicationLink") or item.get("url") or "")
        if not title or not url:
            continue
        company = item.get("company") or {}
        employer = company.get("name", "") if isinstance(company, dict) else str(company)
        sal_min = item.get("salaryMin") or item.get("salary_min")
        sal_max = item.get("salaryMax") or item.get("salary_max")
        currency = item.get("currency") or item.get("salaryCurrency") or ""
        pay = ""
        if sal_min or sal_max:
            pay = f"{currency} {sal_min or '?'}–{sal_max or '?'}".strip()
        desc = str(item.get("description") or "")
        out.append(
            Listing(
                source="himalayas",
                title=title,
                company=str(employer),
                location="Worldwide",
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                pay_text=pay,
                is_remote=True,
            )
        )
    return out


def pull() -> list[Listing]:
    data, _ = get_json("himalayas", API, params={"q": "software engineer remote"})
    return parse_payload(data)
