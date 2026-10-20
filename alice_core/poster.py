"""Poster extract at $0. Literal emails only. Never invent jobs@ / contact@."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from alice_core.schemas import Listing, PosterExtract

EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
MAILTO_RE = re.compile(r"mailto:([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})", re.I)
NAME_RE = re.compile(
    r"(?:posted by|hiring manager|recruiter|contact)[:\s]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)+)",
    re.I,
)
TEAM_URL_RE = re.compile(
    r"https?://[^\s\"']+(?:team|about|people|company)[^\s\"']*",
    re.I,
)
GUESSED_LOCALS = frozenset({"jobs", "contact", "info", "hr", "hiring", "careers", "apply", "hello"})


def emails_in(text: str) -> list[str]:
    found = [m.group(0) for m in EMAIL_RE.finditer(text or "")]
    found += [m.group(1) for m in MAILTO_RE.finditer(text or "")]
    seen: list[str] = []
    for addr in found:
        low = addr.lower()
        if low not in seen:
            seen.append(low)
    return seen


def never_guess(domain: str) -> None:
    """Do not call. Exists so tests can prove we never synthesize mailboxes."""
    raise RuntimeError("never guess contact addresses")


def literal_only(email: str | None, haystack: str) -> str | None:
    if not email:
        return None
    if email.lower() not in haystack.lower():
        return None
    return email.lower()


def extract_regex(listing: Listing, extra_pages: list[str] | None = None) -> PosterExtract:
    blob = "\n".join(
        [
            listing.description or "",
            listing.snippet or "",
            listing.apply_url or "",
            listing.source_url or "",
            *(extra_pages or []),
        ]
    )
    found = emails_in(blob)
    email = found[0] if found else None
    name = None
    m = NAME_RE.search(blob)
    if m:
        name = m.group(1).strip()
    evidence = f"literal {email}" if email else "no email on posting"
    return PosterExtract(
        poster_name=name,
        poster_title=None,
        poster_email=email,
        evidence=evidence,
    )


def resolve_poster(listing: Listing) -> PosterExtract:
    extra: list[str] = []
    blob = listing.description or listing.snippet or ""
    team = TEAM_URL_RE.search(blob)
    if team:
        url = team.group(0).rstrip(").,")
        try:
            from alice_core.crawl import get_text

            extra.append(get_text(listing.source, url)[:8000])
        except Exception:
            pass
    extracted = extract_regex(listing, extra)
    try:
        from alice_core.llm import scoring_model_name, structured

        hay = blob + "\n".join(extra)
        llm = structured(
            scoring_model_name(),
            PosterExtract,
            "Copy a name, title, and email only if they appear verbatim in the text. "
            "Otherwise null. Never invent jobs@, contact@, or first.last@ from a domain.",
            hay[:6000],
        )
        email = literal_only(llm.poster_email, hay)
        return PosterExtract(
            poster_name=llm.poster_name or extracted.poster_name,
            poster_title=llm.poster_title,
            poster_email=email or extracted.poster_email,
            evidence=llm.evidence or extracted.evidence,
        )
    except Exception:
        return extracted


def domain_of(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.lstrip("www.")
