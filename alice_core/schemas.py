from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Listing(BaseModel):
    source: str
    title: str
    company: str
    location: str = ""
    apply_url: str = ""
    source_url: str
    snippet: str = ""
    description: str = ""
    pay_text: str = ""
    is_remote: bool = True
    extra: dict = Field(default_factory=dict)


class HardFilterExtract(BaseModel):
    size_headcount: Optional[int] = None
    size_bucket: Literal["lt_20", "ge_20", "unknown"]
    international_hire: Literal["yes", "no", "unknown"]
    pay_hourly_usd: Optional[float] = None
    pay_band: Literal["in_band", "out_of_band", "unknown"]
    evidence: list[str] = Field(default_factory=list)


class JobEvaluation(BaseModel):
    score_skills: float = Field(ge=1.0, le=5.0)
    score_experience: float = Field(ge=1.0, le=5.0)
    score_location: float = Field(ge=1.0, le=5.0)
    score_trajectory: float = Field(ge=1.0, le=5.0)
    score_culture: float = Field(ge=1.0, le=5.0)
    key_strengths: list[str] = Field(default_factory=list)
    critical_gaps: list[str] = Field(default_factory=list)
    really_need: list[str] = Field(default_factory=list)


class PosterExtract(BaseModel):
    poster_name: Optional[str] = None
    poster_title: Optional[str] = None
    poster_email: Optional[str] = None
    evidence: str = ""


class TailoredBullet(BaseModel):
    original_text: str
    rewritten_text: str
    grounded_in_truth: bool = True
    injected_keywords: list[str] = Field(default_factory=list)


class ResumeTailorOutput(BaseModel):
    tailored_summary: str
    optimized_skills: list[str]
    bullets: list[TailoredBullet]


class OutreachDraft(BaseModel):
    subject: str
    body_text: str


class JobCard(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str] = None
    source: str
    apply_url: Optional[str] = None
    status: str
    shown_on: Optional[date] = None
    size_bucket: Optional[str] = None
    international_hire: Optional[str] = None
    pay_hourly_usd: Optional[float] = None
    pay_band: Optional[str] = None
    score_skills: Optional[float] = None
    score_experience: Optional[float] = None
    score_location: Optional[float] = None
    score_trajectory: Optional[float] = None
    score_culture: Optional[float] = None
    composite_score: Optional[float] = None
    really_need: list[str] = Field(default_factory=list)
    poster_name: Optional[str] = None
    poster_title: Optional[str] = None
    poster_email: Optional[str] = None
    email_found: bool = False
    subject: Optional[str] = None
    body_text: Optional[str] = None
    pdf_path: Optional[str] = None
    gmail_ready: bool = False
    updated_at: Optional[datetime] = None


STATUSES = (
    "DISCOVERED",
    "SNIPPET_FILTERED",
    "JD_FETCHED",
    "ARCHIVED",
    "NEEDS_REVIEW",
    "BACKLOG",
    "READY",
    "APPLIED",
    "SENT",
    "BOTH",
    "SKIPPED",
)

LEGAL_TRANSITIONS = {
    "DISCOVERED": {"SNIPPET_FILTERED", "ARCHIVED", "JD_FETCHED"},
    "SNIPPET_FILTERED": {"JD_FETCHED", "ARCHIVED"},
    "JD_FETCHED": {"ARCHIVED", "NEEDS_REVIEW", "BACKLOG"},
    "NEEDS_REVIEW": {"BACKLOG", "ARCHIVED", "SKIPPED"},
    "BACKLOG": {"READY", "ARCHIVED"},
    "READY": {"APPLIED", "SENT", "BOTH", "SKIPPED"},
    "APPLIED": {"BOTH", "SKIPPED"},
    "SENT": {"BOTH"},
    "BOTH": set(),
    "ARCHIVED": set(),
    "SKIPPED": set(),
}
