"""RemoteOK public JSON. First array element is metadata."""

from __future__ import annotations

from alice_core.crawl import get_json
from alice_core.schemas import Listing

API = "https://remoteok.com/api"


def parse_payload(data: object) -> list[Listing]:
    if not isinstance(data, list):
        return []
    rows = [item for item in data[1:] if isinstance(item, dict)]
    out: list[Listing] = []
    for item in rows:
        title = str(item.get("position") or item.get("title") or "")
        company = str(item.get("company") or "")
        url = str(item.get("url") or item.get("apply_url") or "")
        if not title or not url:
            continue
        desc = str(item.get("description") or "")
        salary = str(item.get("salary") or "")
        if item.get("salary_min") or item.get("salary_max"):
            salary = salary or f"${item.get('salary_min', '')}-${item.get('salary_max', '')}"
        out.append(
            Listing(
                source="remoteok",
                title=title,
                company=company,
                location=str(item.get("location") or "Worldwide"),
                apply_url=str(item.get("apply_url") or url),
                source_url=url,
                snippet=desc[:400],
                description=desc,
                pay_text=salary,
                is_remote=True,
            )
        )
    return out


def pull() -> list[Listing]:
    data, _ = get_json("remoteok", API, headers={"Accept": "application/json"})
    return parse_payload(data)
