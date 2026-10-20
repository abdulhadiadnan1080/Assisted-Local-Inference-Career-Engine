"""We Work Remotely programming RSS. No HTML crawl as the engine."""

from __future__ import annotations

from alice_core.crawl import get_text
from alice_core.schemas import Listing

FEED = "https://weworkremotely.com/categories/remote-programming-jobs.rss"


def parse_rss(body: str) -> list[Listing]:
    import feedparser

    parsed = feedparser.parse(body)
    out: list[Listing] = []
    for entry in parsed.entries:
        title_text = str(entry.get("title") or "")
        link = str(entry.get("link") or "")
        desc = str(entry.get("summary") or entry.get("description") or "")
        if not link:
            continue
        parts = title_text.split(": ", 1)
        company = parts[0] if len(parts) > 1 else ""
        title = parts[1] if len(parts) > 1 else title_text
        out.append(
            Listing(
                source="wwr",
                title=title or title_text,
                company=company,
                location="Worldwide",
                apply_url=link,
                source_url=link,
                snippet=desc[:400],
                description=desc,
                is_remote=True,
            )
        )
    return out


def pull() -> list[Listing]:
    body = get_text("wwr", FEED)
    return parse_rss(body)
