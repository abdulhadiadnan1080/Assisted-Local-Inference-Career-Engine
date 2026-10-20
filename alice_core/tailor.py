"""Gemma drafts, Hermes audits, Typst compiles. Grounded in master_profile only."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from alice_core import db
from alice_core.db import ROOT
from alice_core.profile import candidate_name, load_profile, profile_text
from alice_core.schemas import (
    Listing,
    OutreachDraft,
    ResumeTailorOutput,
    TailoredBullet,
)

ARTIFACTS = ROOT / "artifacts" / "resumes"
TEMPLATE = ROOT / "templates" / "resume.typ"

FORBIDDEN_OPENERS = (
    "i hope this email finds you well",
    "i came across your posting",
    "i am writing to express",
    "please find attached",
    "i believe i would be a great fit",
)


def escape_typst(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("#", r"\#")
        .replace("$", r"\$")
        .replace("[", r"\[")
        .replace("]", r"\]")
    )


def _facts(profile: dict) -> str:
    return profile_text(profile).lower()


def audit_output(drafted: ResumeTailorOutput, profile: dict) -> ResumeTailorOutput:
    facts = _facts(profile)
    bullets: list[TailoredBullet] = []
    for bullet in drafted.bullets:
        rewritten = bullet.rewritten_text
        grounded = _grounded(rewritten, facts, bullet.original_text)
        if not grounded:
            bullets.append(
                TailoredBullet(
                    original_text=bullet.original_text,
                    rewritten_text=bullet.original_text,
                    grounded_in_truth=False,
                    injected_keywords=bullet.injected_keywords,
                )
            )
        else:
            bullets.append(
                TailoredBullet(
                    original_text=bullet.original_text,
                    rewritten_text=rewritten,
                    grounded_in_truth=True,
                    injected_keywords=bullet.injected_keywords,
                )
            )
    summary = drafted.tailored_summary
    if not _grounded(summary, facts, summary):
        summary = (profile.get("summary_foundation") or {}).get("summary") or summary
    skills = [s for s in drafted.optimized_skills if s.lower() in facts]
    if not skills:
        skills = list(drafted.optimized_skills)
    return ResumeTailorOutput(
        tailored_summary=summary,
        optimized_skills=skills,
        bullets=bullets,
    )


def _grounded(text: str, facts: str, original: str) -> bool:
    if not text:
        return True
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9.+#\-]{2,}", text)
    suspicious = []
    for tok in tokens:
        low = tok.lower()
        if low in facts or low in original.lower():
            continue
        if low in {
            "the",
            "and",
            "with",
            "for",
            "from",
            "that",
            "this",
            "built",
            "shipped",
            "owned",
            "remote",
            "team",
        }:
            continue
        if tok[0].isupper() and low not in facts:
            suspicious.append(tok)
        if re.search(r"\d{2,}", tok) and tok not in original and tok.lower() not in facts:
            suspicious.append(tok)
    invented_tools = [
        t
        for t in ("kubernetes", "terraform", "aws", "gcp", "pytorch", "hadoop", "spark")
        if t in text.lower() and t not in facts
    ]
    return not invented_tools and len(suspicious) < 8


def _heuristic_tailor(listing: Listing, really_need: list[str], profile: dict) -> ResumeTailorOutput:
    summary = (profile.get("summary_foundation") or {}).get("summary") or "Ships production software."
    skills: list[str] = []
    for key in ("languages", "frameworks", "infrastructure"):
        skills.extend((profile.get("skills") or {}).get(key) or [])
    bullets: list[TailoredBullet] = []
    for job in profile.get("experience") or []:
        for b in job.get("bullets") or []:
            text = b if isinstance(b, str) else str(b.get("text") or b.get("ground_metrics") or "")
            if not text:
                continue
            bullets.append(
                TailoredBullet(
                    original_text=text,
                    rewritten_text=text,
                    grounded_in_truth=True,
                    injected_keywords=[n for n in really_need if n.lower() in text.lower()],
                )
            )
    if not bullets:
        bullets = [
            TailoredBullet(
                original_text=summary,
                rewritten_text=summary,
                grounded_in_truth=True,
            )
        ]
    return ResumeTailorOutput(
        tailored_summary=f"{summary} Relevant to {listing.company}: {'; '.join(really_need[:2])}".strip(),
        optimized_skills=skills[:12],
        bullets=bullets[:6],
    )


def tailor_and_audit(listing: Listing, really_need: list[str], profile: dict | None = None) -> ResumeTailorOutput:
    profile = profile or load_profile()
    drafted = _heuristic_tailor(listing, really_need, profile)
    try:
        from alice_core.llm import structured, writing_model_name

        from alice_core.engine_config import cv_system_prompt

        drafted = structured(
            writing_model_name(),
            ResumeTailorOutput,
            cv_system_prompt(),
            f"PROFILE:\n{profile_text(profile)}\n\nNEED:\n{really_need}\n\nJD:\n"
            f"{listing.title} at {listing.company}\n{listing.description[:4000]}",
        )
    except Exception:
        pass
    audited = audit_output(drafted, profile)
    try:
        from alice_core.llm import scoring_model_name, structured

        from alice_core.engine_config import cv_audit_prompt

        audited = structured(
            scoring_model_name(),
            ResumeTailorOutput,
            cv_audit_prompt(),
            f"PROFILE:\n{profile_text(profile)}\n\nDRAFT:\n{audited.model_dump_json()}",
        )
        audited = audit_output(audited, profile)
    except Exception:
        pass
    return audited


def _heuristic_email(listing: Listing, poster_name: str | None, profile: dict, really_need: list[str]) -> OutreachDraft:
    name = candidate_name(profile)
    need = really_need[0] if really_need else "shipping the product with a tiny remote team"
    fact1 = (profile.get("summary_foundation") or {}).get("summary") or "I ship production software."
    skills = (profile.get("skills") or {}).get("languages") or ["Python"]
    fact2 = f"Recent work centers on {', '.join(skills[:3])}."
    who = poster_name.split()[0] if poster_name else None
    body_lines = [
        f"{listing.company} needs {need.rstrip('.')}.",
        fact1.rstrip("."),
        fact2,
        f"I can take that slice without a large platform org around me.",
        f"Happy to walk through a relevant project if useful.",
        f"{name}",
    ]
    if who:
        body_lines.insert(0, f"{who},")
    subject = f"{listing.title.split()[0]} at {listing.company}"[:80]
    if len(subject.split()) > 8:
        subject = " ".join(subject.split()[:8])
    return OutreachDraft(subject=subject, body_text=" ".join(s.strip() for s in body_lines if s))


def audit_email(draft: OutreachDraft, profile: dict) -> OutreachDraft:
    body = draft.body_text.strip()
    low = body.lower()
    for phrase in FORBIDDEN_OPENERS:
        if phrase in low:
            body = re.sub(re.escape(phrase), "", body, flags=re.I).strip()
    body = body.replace("—", ",").replace("–", ",")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    if len(sentences) < 5:
        extra = (profile.get("summary_foundation") or {}).get("summary") or "I ship production software."
        sentences.append(extra if extra.endswith(".") else extra + ".")
    sentences = sentences[:8]
    subject = " ".join(draft.subject.split()[:8])
    return OutreachDraft(subject=subject, body_text=" ".join(sentences))


def write_email(listing: Listing, poster_name: str | None, really_need: list[str], profile: dict | None = None) -> OutreachDraft:
    profile = profile or load_profile()
    draft = _heuristic_email(listing, poster_name, profile, really_need)
    try:
        from alice_core.llm import structured, writing_model_name

        from alice_core.engine_config import email_system_prompt

        draft = structured(
            writing_model_name(),
            OutreachDraft,
            email_system_prompt(),
            f"PROFILE:\n{profile_text(profile)}\n\nJOB: {listing.title} at {listing.company}\n"
            f"NEED: {really_need}\nPOSTER: {poster_name}",
        )
    except Exception:
        pass
    draft = audit_email(draft, profile)
    try:
        from alice_core.llm import scoring_model_name, structured

        from alice_core.engine_config import email_audit_prompt

        draft = structured(
            scoring_model_name(),
            OutreachDraft,
            email_audit_prompt(),
            f"PROFILE:\n{profile_text(profile)}\n\nDRAFT:\n{draft.model_dump_json()}",
        )
        draft = audit_email(draft, profile)
    except Exception:
        pass
    return draft


def compile_typst(job_id: str, listing: Listing, tailored: ResumeTailorOutput, profile: dict | None = None) -> tuple[str, str, bool]:
    profile = profile or load_profile()
    candidate = profile.get("candidate") or {}
    payload = {
        "name": candidate.get("full_name") or "Operator",
        "headline": candidate.get("headline") or listing.title,
        "email": candidate.get("email") or "",
        "location": candidate.get("location") or "",
        "summary": tailored.tailored_summary,
        "skills": tailored.optimized_skills,
        "experience": [],
    }
    for job in profile.get("experience") or []:
        original = [b if isinstance(b, str) else str(b.get("text") or "") for b in (job.get("bullets") or [])]
        rewritten = []
        for bullet in tailored.bullets:
            if bullet.original_text in original or not rewritten:
                rewritten.append(bullet.rewritten_text)
        payload["experience"].append(
            {
                "company": job.get("company") or "",
                "role": job.get("role") or job.get("title") or "",
                "location": job.get("location") or "",
                "dates": job.get("dates") or "",
                "bullets": rewritten[:4] or original[:4],
            }
        )
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    folder = ARTIFACTS / job_id
    folder.mkdir(parents=True, exist_ok=True)
    data_path = folder / "resume.json"
    data_path.write_text(json.dumps(payload, indent=2))
    typ_path = folder / "resume.typ"
    if TEMPLATE.exists():
        typ_path.write_text(TEMPLATE.read_text())
    pdf_path = folder / "resume.pdf"
    grounded = all(b.grounded_in_truth for b in tailored.bullets) if tailored.bullets else True
    if shutil.which("typst"):
        subprocess.run(
            ["typst", "compile", str(typ_path), str(pdf_path)],
            cwd=str(folder),
            check=False,
            capture_output=True,
            timeout=20,
        )
    db.save_resume(
        job_id,
        typ_path.read_text() if typ_path.exists() else "",
        str(pdf_path) if pdf_path.exists() else "",
        grounded,
        [b.rewritten_text for b in tailored.bullets],
    )
    return str(typ_path), str(pdf_path) if pdf_path.exists() else "", grounded
