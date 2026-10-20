from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from alice_core.db import ROOT

PROFILE_PATH = ROOT / "config" / "master_profile.yaml"
EXAMPLE_PATH = ROOT / "config" / "master_profile.example.yaml"


def load_profile() -> dict[str, Any]:
    path = PROFILE_PATH if PROFILE_PATH.exists() else EXAMPLE_PATH
    if not path.exists():
        return {
            "candidate": {"full_name": "Operator", "email": "", "headline": "Software engineer"},
            "summary_foundation": {"years_of_experience": 4, "summary": "Ships production software."},
            "skills": {"languages": ["Python"], "frameworks": ["FastAPI"], "infrastructure": []},
            "experience": [],
        }
    return yaml.safe_load(path.read_text()) or {}


def profile_text(profile: dict[str, Any] | None = None) -> str:
    data = profile or load_profile()
    return yaml.safe_dump(data, sort_keys=False)


def candidate_name(profile: dict[str, Any] | None = None) -> str:
    data = profile or load_profile()
    return ((data.get("candidate") or {}).get("full_name")) or "Operator"
