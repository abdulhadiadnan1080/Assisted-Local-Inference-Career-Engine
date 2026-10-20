from __future__ import annotations

import re
from typing import Optional

from alice_core.engine_config import load as load_engine, max_headcount, pay_band, threshold as score_threshold
from alice_core.schemas import HardFilterExtract, JobEvaluation, Listing

WEIGHTS = dict(
    skills=0.35,
    experience=0.25,
    location=0.15,
    trajectory=0.15,
    culture=0.10,
)

FAANG = (
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


def _weights() -> dict[str, float]:
    try:
        return load_engine()["scoring"]["weightFractions"]
    except Exception:
        return WEIGHTS


def composite_score(e: JobEvaluation) -> float:
    w = _weights()
    return round(
        e.score_skills * w["skills"]
        + e.score_experience * w["experience"]
        + e.score_location * w["location"]
        + e.score_trajectory * w["trajectory"]
        + e.score_culture * w["culture"],
        2,
    )


def recommendation(score: float) -> str:
    return "PROCEED" if score >= score_threshold() else "ARCHIVE"


def _text(listing: Listing) -> str:
    return " ".join(
        [
            listing.title,
            listing.company,
            listing.location,
            listing.snippet,
            listing.description,
            listing.pay_text,
        ]
    ).lower()


def extract_hard_heuristic(listing: Listing) -> HardFilterExtract:
    blob = _text(listing)
    evidence: list[str] = []

    size_bucket: str = "unknown"
    headcount: Optional[int] = None
    m = re.search(r"\b(\d{1,4})\s*(?:people|employees|headcount|person team)\b", blob)
    if m:
        headcount = int(m.group(1))
        size_bucket = "lt_20" if headcount < max_headcount() else "ge_20"
        evidence.append(f"headcount {headcount}")
    elif any(w in blob for w in ("enterprise", "fortune 500", "200+", "1000+", "multinational")):
        size_bucket = "ge_20"
        evidence.append("enterprise language")
    elif any(w in blob for w in ("seed", "pre-seed", "tiny team", "founding engineer", "early-stage")):
        size_bucket = "lt_20"
        evidence.append("early-stage language")
    if listing.company.lower() in FAANG or any(f in listing.company.lower() for f in FAANG):
        size_bucket = "ge_20"
        evidence.append("FAANG-scale employer")

    international: str = "unknown"
    if any(
        w in blob
        for w in (
            "worldwide",
            "anywhere",
            "work from anywhere",
            "international",
            "visa",
            "no country lock",
            "distributed",
            "remote - global",
        )
    ):
        international = "yes"
        evidence.append("worldwide/remote language")
    if any(
        w in blob
        for w in (
            "us only",
            "united states only",
            "must live in",
            "must reside",
            "onsite only",
            "no remote",
            "hybrid in-office",
        )
    ):
        international = "no"
        evidence.append("geo lock language")

    pay_hourly: Optional[float] = None
    band: str = "unknown"
    hourly = re.search(r"\$?\s*(\d{2,3})\s*(?:-|–|to)?\s*\$?\s*(\d{2,3})?\s*(?:usd\s*)?(?:/|per)?\s*h(?:r|our)", blob)
    yearly = re.search(r"\$?\s*(\d{2,3})\s*k(?:\s*(?:-|–|to)\s*\$?\s*(\d{2,3})\s*k)?", blob)
    if hourly:
        lo = float(hourly.group(1))
        hi = float(hourly.group(2) or lo)
        pay_hourly = (lo + hi) / 2
    elif yearly:
        lo = float(yearly.group(1)) * 1000 / 2080
        hi = float(yearly.group(2) or yearly.group(1)) * 1000 / 2080
        pay_hourly = (lo + hi) / 2
    if pay_hourly is not None:
        evidence.append(f"pay ~${pay_hourly:.0f}/hr")
        floor, ceil = pay_band()
        band = "in_band" if floor <= pay_hourly <= ceil else "out_of_band"
    if any(w in blob for w in ("unpaid", "equity only", "exposure")):
        band = "out_of_band"
        evidence.append("unpaid/equity-only")

    return HardFilterExtract(
        size_headcount=headcount,
        size_bucket=size_bucket,  # type: ignore[arg-type]
        international_hire=international,  # type: ignore[arg-type]
        pay_hourly_usd=pay_hourly,
        pay_band=band,  # type: ignore[arg-type]
        evidence=evidence or ["heuristic extract"],
    )


def score_heuristic(listing: Listing, profile: dict) -> JobEvaluation:
    blob = _text(listing)
    skills = [s.lower() for s in _profile_skills(profile)]
    hit = sum(1 for s in skills if s and s in blob)
    skill_ratio = hit / max(len(skills), 1)
    score_skills = round(1.0 + min(4.0, skill_ratio * 6.0), 1)

    years = float(profile.get("summary_foundation", {}).get("years_of_experience") or 4)
    seniority = 3.5
    if any(w in listing.title.lower() for w in ("staff", "principal", "director")):
        seniority = 2.5 if years < 8 else 4.0
    elif any(w in listing.title.lower() for w in ("senior", "lead")):
        seniority = 4.0 if years >= 4 else 3.0
    elif any(w in listing.title.lower() for w in ("junior", "intern")):
        seniority = 2.0

    loc = 4.5 if listing.is_remote or "remote" in blob or "worldwide" in blob else 2.5
    traj = 4.0 if any(w in blob for w in ("founding", "0 to 1", "ai", "inference", "agent")) else 3.2
    culture = 3.8 if any(w in blob for w in ("small team", "seed", "startup")) else 3.2

    really = []
    for token in ("python", "fastapi", "mlx", "inference", "distributed", "rust"):
        if token in blob:
            really.append(f"Need demonstrated {token} work")
    if not really:
        really = ["Ship production software in a small remote team", "Own a slice of the stack", "Communicate in writing"]

    return JobEvaluation(
        score_skills=max(1.0, min(5.0, score_skills)),
        score_experience=max(1.0, min(5.0, seniority)),
        score_location=max(1.0, min(5.0, loc)),
        score_trajectory=max(1.0, min(5.0, traj)),
        score_culture=max(1.0, min(5.0, culture)),
        key_strengths=[s for s in skills[:4] if s in blob] or ["remote delivery"],
        critical_gaps=["unknown company size"] if "headcount" not in blob else [],
        really_need=really[:4],
    )


def _profile_skills(profile: dict) -> list[str]:
    skills = profile.get("skills") or {}
    out: list[str] = []
    for key in ("languages", "frameworks", "infrastructure"):
        out.extend(skills.get(key) or [])
    return out


def hard_fail(h: HardFilterExtract) -> bool:
    cap = max_headcount()
    if h.size_headcount is not None and h.size_headcount >= cap:
        return True
    if h.size_bucket == "ge_20" and h.size_headcount is None:
        return True
    return h.international_hire == "no" or h.pay_band == "out_of_band"


def hard_unknown(h: HardFilterExtract) -> bool:
    return h.size_bucket == "unknown" or h.pay_band == "unknown"


HARD_SYSTEM = """You extract hard hiring constraints from a job posting.
Return only fields that appear in the text. If size or pay is not stated, use unknown.
Never invent headcount, pay, or emails. Do not compute a composite score.
size_bucket: lt_20 if headcount < 20 or early-stage/seed founding team language;
ge_20 if 20+ people, enterprise, FAANG; else unknown.
international_hire: yes if worldwide/anywhere/visa/distributed; no if US-only/onsite/must live in;
else unknown.
pay_band: in_band if $40-60/hr or $80k-$125k/year; out_of_band if clearly outside or unpaid; else unknown.
"""

SCORE_SYSTEM = """You score fit against the candidate profile on five dimensions from 1.0 to 5.0:
skills, experience, location, trajectory, culture.
Also list key_strengths, critical_gaps, and 3-4 really_need hiring problems the company has.
Do not return a composite score. Do not return a recommendation.
"""


def extract_hard(listing: Listing) -> HardFilterExtract:
    from alice_core.llm import scoring_model_name, structured

    floor, ceil = pay_band()
    cap = max_headcount()
    user = (
        f"Title: {listing.title}\nCompany: {listing.company}\n"
        f"Location: {listing.location}\nPay text: {listing.pay_text}\n\n"
        f"{listing.description or listing.snippet}"
    )
    system = (
        HARD_SYSTEM
        + f"\nOperator pay band is ${floor:.0f}-{ceil:.0f}/hr. "
        + f"size_bucket lt_20 if headcount < {cap} or early-stage; ge_20 if {cap}+ or FAANG."
    )
    try:
        return structured(scoring_model_name(), HardFilterExtract, system, user)
    except Exception:
        return extract_hard_heuristic(listing)


def score_job(listing: Listing, profile: dict) -> JobEvaluation:
    from alice_core.llm import scoring_model_name, structured

    skills = ", ".join(_profile_skills(profile))
    user = (
        f"Profile skills: {skills}\nYears: "
        f"{profile.get('summary_foundation', {}).get('years_of_experience', 4)}\n"
        f"Title: {listing.title}\nCompany: {listing.company}\n"
        f"{listing.description or listing.snippet}"
    )
    try:
        return structured(scoring_model_name(), JobEvaluation, SCORE_SYSTEM, user)
    except Exception:
        return score_heuristic(listing, profile)
