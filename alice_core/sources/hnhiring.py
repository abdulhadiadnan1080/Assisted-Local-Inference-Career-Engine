"""HN Who's Hiring via Algolia. Not Launch HN funding."""

from __future__ import annotations

import calendar
import html
import re
from datetime import date

from alice_core.crawl import get_json
from alice_core.schemas import Listing

ALGOLIA_STORY = "https://hn.algolia.com/api/v1/search_by_date"
ALGOLIA_COMMENTS = "https://hn.algolia.com/api/v1/search"
HEADER_SPLIT = re.compile(r"[\u2013\u2014\u2012\u2010|\-•·]+")


def _plain(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw or "", flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def parse_comment(hit: dict) -> Listing | None:
    raw = hit.get("comment_text") or hit.get("text") or ""
    plain = _plain(str(raw))
    if not plain:
        return None
    first = plain.split(". ")[0][:200]
    parts = [p.strip() for p in HEADER_SPLIT.split(first) if p.strip()]
    company = parts[0] if parts else ""
    title = parts[1] if len(parts) > 1 else "Software engineer"
    loc = parts[2] if len(parts) > 2 else "Remote"
    object_id = str(hit.get("objectID") or "")
    url = str(hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}")
    remote = bool(re.search(r"\bremote\b", plain, re.I))
    return Listing(
        source="hnhiring",
        title=title,
        company=company or (hit.get("author") or "HN"),
        location=loc,
        apply_url=url,
        source_url=url,
        snippet=plain[:400],
        description=plain,
        is_remote=remote or "remote" in loc.lower(),
        extra={"object_id": object_id, "author": hit.get("author")},
    )


def parse_comments(payload: object) -> list[Listing]:
    hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(hits, list):
        return []
    out: list[Listing] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        listing = parse_comment(hit)
        if listing:
            out.append(listing)
    return out


def current_thread_title() -> str:
    today = date.today()
    month = calendar.month_name[today.month]
    return f"Ask HN: Who is hiring? ({month} {today.year})"


def pull() -> list[Listing]:
    stories, _ = get_json(
        "hnhiring",
        ALGOLIA_STORY,
        params={"query": "Ask HN: Who is hiring", "tags": "story", "hitsPerPage": 5},
    )
    hits = stories.get("hits") if isinstance(stories, dict) else []
    story_id = None
    for hit in hits or []:
        title = str(hit.get("title") or "")
        if "Who is hiring" in title:
            story_id = hit.get("objectID") or hit.get("story_id")
            break
    if not story_id:
        return []
    comments, _ = get_json(
        "hnhiring",
        ALGOLIA_COMMENTS,
        params={"tags": f"comment,story_{story_id}", "hitsPerPage": 50},
    )
    return parse_comments(comments)
