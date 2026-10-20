"""Official Greenhouse / Lever / Ashby board JSON. Slugs from ats_slugs.yaml only."""

from __future__ import annotations

from pathlib import Path

import yaml

from alice_core.crawl import get_json
from alice_core.db import ROOT
from alice_core.schemas import Listing

SLUG_PATH = ROOT / "config" / "ats_slugs.yaml"


def _slugs() -> dict:
    if not SLUG_PATH.exists():
        return {"greenhouse": [], "lever": [], "ashby": []}
    return yaml.safe_load(SLUG_PATH.read_text()) or {}


def parse_greenhouse(slug: str, data: object) -> list[Listing]:
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return []
    out: list[Listing] = []
    for item in jobs:
        title = str(item.get("title") or "")
        url = str(item.get("absolute_url") or "")
        if not title or not url:
            continue
        loc = ""
        location = item.get("location")
        if isinstance(location, dict):
            loc = str(location.get("name") or "")
        company = str(item.get("company_name") or slug)
        desc = str(item.get("content") or "")
        out.append(
            Listing(
                source="ats_boards",
                title=title,
                company=company,
                location=loc,
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                extra={"ats": "greenhouse", "slug": slug},
            )
        )
    return out


def parse_lever(slug: str, data: object) -> list[Listing]:
    jobs = data if isinstance(data, list) else []
    out: list[Listing] = []
    for item in jobs:
        if not isinstance(item, dict):
            continue
        title = str(item.get("text") or "")
        url = str(item.get("hostedUrl") or item.get("applyUrl") or "")
        if not title or not url:
            continue
        cats = item.get("categories") or {}
        loc = str(cats.get("location") or "")
        desc = str((item.get("descriptionPlain") or item.get("description") or ""))
        out.append(
            Listing(
                source="ats_boards",
                title=title,
                company=slug,
                location=loc,
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                extra={"ats": "lever", "slug": slug},
            )
        )
    return out


def parse_ashby(slug: str, data: object) -> list[Listing]:
    jobs = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(jobs, list):
        return []
    out: list[Listing] = []
    for item in jobs:
        title = str(item.get("title") or "")
        url = str(item.get("jobUrl") or item.get("applyUrl") or "")
        if not title or not url:
            continue
        loc = str(item.get("location") or "")
        desc = str(item.get("descriptionHtml") or item.get("descriptionPlain") or "")
        out.append(
            Listing(
                source="ats_boards",
                title=title,
                company=str(item.get("departmentName") or slug),
                location=loc,
                apply_url=url,
                source_url=url,
                snippet=desc[:400],
                description=desc,
                extra={"ats": "ashby", "slug": slug},
            )
        )
    return out


def pull() -> list[Listing]:
    cfg = _slugs()
    out: list[Listing] = []
    for slug in cfg.get("greenhouse") or []:
        data, _ = get_json("ats_boards", f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        out.extend(parse_greenhouse(slug, data))
    for slug in cfg.get("lever") or []:
        data, _ = get_json("ats_boards", f"https://api.lever.co/v0/postings/{slug}")
        out.extend(parse_lever(slug, data))
    for slug in cfg.get("ashby") or []:
        data, _ = get_json("ats_boards", f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        out.extend(parse_ashby(slug, data))
    return out
