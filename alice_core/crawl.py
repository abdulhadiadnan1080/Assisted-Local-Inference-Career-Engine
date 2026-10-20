"""Shared HTTP, jitter, circuit breaker, JD budget. $0 public boards only."""

from __future__ import annotations

import random
import threading
import time
from typing import Callable

import httpx

from alice_core import db
from alice_core.schemas import Listing

USER_AGENT = "ALICE/0.1 (local career engine; +http://127.0.0.1:8471)"
FORBIDDEN_SOURCES = frozenset({"twitter", "wellfound", "glassdoor", "zip_recruiter", "google"})
DEFAULT_SOURCES = (
    "remoteok",
    "remotive",
    "arbeitnow",
    "himalayas",
    "wwr",
    "hnhiring",
    "ats_boards",
    "jobspy",
)

_gate = threading.Semaphore(2)


class CircuitOpen(RuntimeError):
    def __init__(self, source: str):
        super().__init__(source)
        self.source = source


class HttpTripped(RuntimeError):
    def __init__(self, source: str, status: int):
        super().__init__(f"{source} HTTP {status}")
        self.source = source
        self.status = status


def enabled_sources() -> list[str]:
    from alice_core.engine_config import enabled_source_ids

    names = enabled_source_ids()
    return [n for n in names if n not in FORBIDDEN_SOURCES]


def jitter() -> None:
    time.sleep(random.uniform(1.0, 2.0))


def get_json(source: str, url: str, params: dict | None = None, headers: dict | None = None) -> tuple[object, str]:
    text = get_text(source, url, params=params, headers=headers)
    import json

    return json.loads(text), text


def get_text(
    source: str,
    url: str,
    params: dict | None = None,
    headers: dict | None = None,
    count_as_jd: bool = False,
) -> str:
    if db.circuit_open(source):
        raise CircuitOpen(source)
    cache_key = url if not params else f"{url}?{sorted(params.items())}"
    cached = _read_cache(cache_key)
    if cached is not None:
        return cached
    if count_as_jd and db.jd_budget_remaining() <= 0:
        raise RuntimeError("jd budget exhausted")
    hdrs = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    with _gate:
        jitter()
        try:
            resp = httpx.get(url, params=params, headers=hdrs, timeout=20, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{source} network: {exc}") from exc
    if resp.status_code in {429, 403}:
        db.trip_circuit(source, hours=24)
        raise HttpTripped(source, resp.status_code)
    resp.raise_for_status()
    body = resp.text
    db.cache_payload(cache_key, body)
    if count_as_jd:
        db.consume_jd_fetch()
    return body


def _read_cache(url: str) -> str | None:
    import hashlib

    name = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = db.CACHE_DIR / f"{name}.json"
    if path.exists():
        return path.read_text()
    return None


def fetch_jd(source: str, listing: Listing) -> tuple[str, bool]:
    """Return (text, counted_against_budget). Cache hits do not count."""
    existing = listing.description or ""
    if len(existing) >= 200:
        return existing, False
    url = listing.source_url or listing.apply_url
    if not url:
        return existing, False
    cache_hit = _read_cache(url)
    if cache_hit is not None:
        return cache_hit, False
    if db.jd_budget_remaining() <= 0:
        return existing, False
    text = get_text(source, url, count_as_jd=True)
    return text or existing, True


def pull_all(names: list[str] | None = None) -> list[Listing]:
    if not db.live_crawl_enabled():
        return []
    from alice_core.sources import pullers

    out: list[Listing] = []
    for name in names or enabled_sources():
        if name in FORBIDDEN_SOURCES:
            continue
        if db.circuit_open(name):
            continue
        fn: Callable[[], list[Listing]] | None = pullers.get(name)
        if not fn:
            continue
        try:
            out.extend(fn())
        except (CircuitOpen, HttpTripped):
            continue
        except Exception:
            continue
    return out
