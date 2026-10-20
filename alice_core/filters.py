"""Snippet Gate A. No LLM. Steal red/green flags from JobScraper true_remote_filter."""

from __future__ import annotations

import re

from alice_core.engine_config import blocked_phrases, exclude_companies, pay_band
from alice_core.schemas import Listing

RED_FLAGS = [
    r"\bus\b only",
    r"\bunited states\b only",
    r"must reside in (?:the )?us",
    r"must live in",
    r"onsite only",
    r"no remote",
    r"us citizen",
    r"w2 only",
    r"security clearance",
    r"cleared candidates",
    r"unpaid",
    r"equity only",
    r"\b200\+?\s*(?:people|employees)",
    r"fortune 500",
]

FAANG_COMPANIES = (
    "google",
    "alphabet",
    "meta",
    "facebook",
    "amazon",
    "apple",
    "netflix",
    "microsoft",
    "nvidia",
)

GREEN_WORLDWIDE = [
    r"work from anywhere",
    r"anywhere in the world",
    r"worldwide",
    r"global team",
    r"distributed team",
    r"digital nomad",
    r"visa",
]


def _hourly_from_blob(blob: str) -> float | None:
    hourly = re.search(
        r"\$?\s*(\d{2,3})\s*(?:-|–|to)?\s*\$?\s*(\d{2,3})?\s*(?:usd\s*)?(?:/|per)?\s*h(?:r|our)",
        blob,
    )
    yearly = re.search(r"\$?\s*(\d{2,3})\s*k(?:\s*(?:-|–|to)\s*\$?\s*(\d{2,3})\s*k)?", blob)
    if hourly:
        lo = float(hourly.group(1))
        hi = float(hourly.group(2) or lo)
        return (lo + hi) / 2
    if yearly:
        lo = float(yearly.group(1)) * 1000 / 2080
        hi = float(yearly.group(2) or yearly.group(1)) * 1000 / 2080
        return (lo + hi) / 2
    return None


def snippet_gate(listing: Listing) -> tuple[bool, str]:
    blob = " ".join(
        [listing.title, listing.company, listing.location, listing.snippet, listing.pay_text]
    ).lower()
    company = listing.company.lower().strip()
    banned = exclude_companies()
    if company in FAANG_COMPANIES or any(f == company or company.startswith(f + " ") for f in FAANG_COMPANIES):
        return False, "snippet red flag: FAANG-scale employer"
    if any(company == b or b in company for b in banned):
        return False, f"snippet red flag: excluded company {listing.company}"
    for flag in RED_FLAGS:
        if re.search(flag, blob):
            return False, f"snippet red flag: {flag}"
    for phrase in blocked_phrases():
        token = phrase.strip().lower()
        if token and token in blob:
            return False, f"snippet red flag: {phrase}"
    pay = _hourly_from_blob(blob)
    floor, ceil = pay_band()
    if pay is not None and not (floor <= pay <= ceil):
        return False, f"snippet red flag: pay ${pay:.0f}/hr outside ${floor:.0f}–{ceil:.0f}"
    return True, "pass"
