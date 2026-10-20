"""Setup page is the control plane. Hardcoded fallbacks live here as defaults only."""

from __future__ import annotations

import copy
import json
from typing import Any

from alice_core import db

CONFIG_KEY = "frontend_config"

SOURCE_CATALOG = (
    ("remoteok", "RemoteOK", "https://remoteok.com/api"),
    ("remotive", "Remotive", "https://remotive.com/api/remote-jobs"),
    ("arbeitnow", "Arbeitnow", "https://www.arbeitnow.com/api/job-board-api"),
    ("himalayas", "Himalayas", "https://himalayas.app/jobs/api/search"),
    ("wwr", "We Work Remotely", "https://weworkremotely.com/categories/remote-programming-jobs.rss"),
    ("hnhiring", "HN Who's Hiring", "https://hn.algolia.com/api/v1/search_by_date"),
    ("ats_boards", "Greenhouse / Lever / Ashby", "https://boards-api.greenhouse.io/v1/boards/stripe/jobs"),
    ("jobspy", "LinkedIn & Indeed (JobSpy)", None),
)

SOURCE_IDS = [row[0] for row in SOURCE_CATALOG]
SOURCE_LABEL = {row[0]: row[1] for row in SOURCE_CATALOG}

DEFAULTS: dict[str, Any] = {
    "identity": {
        "name": "Hadi Adnan",
        "email": "",
        "title": "Python & local inference engineer",
        "links": [],
    },
    "profile": {
        "resumeName": "master-profile.pdf",
        "profile": "",
        "skills": ["Python", "FastAPI", "SQLite"],
        "neverClaim": [],
    },
    "email": {
        "gmailAddress": "",
        "credsPath": "credentials.json",
        "signature": "",
        "draftOnly": True,
        "ccSelf": False,
    },
    "geography": {
        "basedIn": "",
        "allowed": ["Worldwide"],
        "blocked": ["US only", "Onsite"],
        "needsVisa": True,
        "tzOverlap": 4,
    },
    "role": {
        "titles": [],
        "payMin": 40,
        "payMax": 60,
        "currency": "USD / hour",
        "maxHeadcount": 20,
        "seniority": [],
        "excludeCompanies": ["Google", "Meta", "Amazon", "Apple", "Netflix", "Microsoft", "Nvidia"],
    },
    "scoring": {
        "weights": {
            "skills": 35,
            "experience": 25,
            "location": 15,
            "trajectory": 15,
            "culture": 10,
        },
        "threshold": 3.5,
        "dailyRelease": 15,
        "perCompany": 2,
    },
    "engine": {
        "ollamaHost": "http://127.0.0.1:11434",
        "scoreModel": "hermes3:8b",
        "writeModel": "gemma2:9b",
        "jobspyKey": "",
        "sources": list(SOURCE_IDS),
    },
    "cadence": {
        "jdCap": 80,
    },
    "prompts": {
        "cvSystem": "",
        "emailSystem": "",
    },
}


def _merge(base: dict, overlay: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (overlay or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _normalize_sources(raw: Any) -> list[str]:
    aliases = {
        "remoteok": "remoteok",
        "remotive": "remotive",
        "arbeitnow": "arbeitnow",
        "himalayas": "himalayas",
        "wwr": "wwr",
        "we work remotely": "wwr",
        "hn who's hiring": "hnhiring",
        "hnhiring": "hnhiring",
        "greenhouse / lever / ashby": "ats_boards",
        "ats_boards": "ats_boards",
        "linkedin & indeed (jobspy)": "jobspy",
        "jobspy": "jobspy",
        "linkedin": "jobspy",
        "indeed": "jobspy",
    }
    if not raw:
        return list(SOURCE_IDS)
    out: list[str] = []
    for item in raw:
        key = aliases.get(str(item).strip().lower(), str(item).strip().lower().replace(" ", "_"))
        if key in SOURCE_IDS and key not in out:
            out.append(key)
    return out or list(SOURCE_IDS)


def load() -> dict[str, Any]:
    db.init_db()
    raw = db.get_setting(CONFIG_KEY, "")
    overlay: dict[str, Any] = {}
    if raw:
        try:
            overlay = json.loads(raw) or {}
        except json.JSONDecodeError:
            overlay = {}
    merged = _merge(DEFAULTS, overlay)
    merged["engine"]["sources"] = _normalize_sources(merged.get("engine", {}).get("sources"))
    weights = merged["scoring"]["weights"]
    total = sum(float(weights.get(k, 0)) for k in ("skills", "experience", "location", "trajectory", "culture")) or 1.0
    merged["scoring"]["weightFractions"] = {
        k: float(weights.get(k, 0)) / total for k in ("skills", "experience", "location", "trajectory", "culture")
    }
    return merged


def save(payload: dict[str, Any]) -> dict[str, Any]:
    merged = _merge(DEFAULTS, payload or {})
    merged["engine"]["sources"] = _normalize_sources(merged.get("engine", {}).get("sources"))
    store = copy.deepcopy(merged)
    store.get("scoring", {}).pop("weightFractions", None)
    db.set_setting(CONFIG_KEY, json.dumps(store))
    return load()


def pay_band() -> tuple[float, float]:
    role = load()["role"]
    lo = float(role.get("payMin") or 40)
    hi = float(role.get("payMax") or 60)
    if hi <= lo:
        hi = lo + 1
    return lo, hi


def max_headcount() -> int:
    return int(load()["role"].get("maxHeadcount") or 20)


def threshold() -> float:
    return float(load()["scoring"].get("threshold") or 3.5)


def daily_release() -> int:
    return max(1, int(load()["scoring"].get("dailyRelease") or 15))


def per_company() -> int:
    return max(1, int(load()["scoring"].get("perCompany") or 2))


def jd_cap() -> int:
    return max(1, int(load()["cadence"].get("jdCap") or 80))


def blocked_phrases() -> list[str]:
    return [p for p in (load()["geography"].get("blocked") or []) if str(p).strip()]


def exclude_companies() -> list[str]:
    return [c.lower() for c in (load()["role"].get("excludeCompanies") or []) if str(c).strip()]


def enabled_source_ids() -> list[str]:
    import os

    raw = os.environ.get("ALICE_SOURCES", "")
    if raw.strip():
        return [s.strip() for s in raw.split(",") if s.strip() and s.strip() in SOURCE_IDS]
    return list(load()["engine"]["sources"])


def scoring_model() -> str:
    import os

    return os.environ.get("ALICE_HERMES_MODEL") or load()["engine"].get("scoreModel") or "hermes3:8b"


def writing_model() -> str:
    import os

    return os.environ.get("ALICE_GEMMA_MODEL") or load()["engine"].get("writeModel") or "gemma2:9b"


def ollama_host() -> str:
    import os

    return os.environ.get("OLLAMA_HOST") or load()["engine"].get("ollamaHost") or "http://127.0.0.1:11434"


CV_SYSTEM_BASE = (
    "Rewrite resume bullets toward this job. Use only facts from the profile. "
    "Never add tools, employers, or metrics that are not in the profile."
)
CV_AUDIT_BASE = (
    "Audit every noun, number, and tool against the master profile. "
    "If a bullet is ungrounded, set rewritten_text to original_text and grounded_in_truth false."
)
EMAIL_SYSTEM_BASE = (
    "Write a 5-8 sentence email. Subject at most 8 words. No 'I hope this email finds you well', "
    "no 'I came across your posting'. One line on their problem, two grounded facts, one ask."
)
EMAIL_AUDIT_BASE = "Strip ungrounded claims and slop. Keep 5-8 sentences. Subject <= 8 words."


def _extra_prompt(key: str) -> str:
    raw = (load().get("prompts") or {}).get(key) or ""
    return str(raw).strip()


def _join_system(base: str, extra: str) -> str:
    if not extra:
        return base
    return f"{base}\n\nOperator instructions:\n{extra}"


def cv_system_prompt() -> str:
    return _join_system(CV_SYSTEM_BASE, _extra_prompt("cvSystem"))


def cv_audit_prompt() -> str:
    return _join_system(CV_AUDIT_BASE, _extra_prompt("cvSystem"))


def email_system_prompt() -> str:
    return _join_system(EMAIL_SYSTEM_BASE, _extra_prompt("emailSystem"))


def email_audit_prompt() -> str:
    return _join_system(EMAIL_AUDIT_BASE, _extra_prompt("emailSystem"))
