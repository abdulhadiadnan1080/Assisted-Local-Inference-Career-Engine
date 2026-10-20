"""Local Ollama + Instructor. Hosted LLM endpoints are forbidden."""

from __future__ import annotations

import os
from typing import TypeVar
from urllib.parse import urlparse

from pydantic import BaseModel

HERMES = os.environ.get("ALICE_HERMES_MODEL", "hermes3:8b")
GEMMA = os.environ.get("ALICE_GEMMA_MODEL", "gemma2:9b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", f"{OLLAMA_HOST.rstrip('/')}/v1")


def scoring_model_name() -> str:
    from alice_core.engine_config import scoring_model

    return scoring_model()


def writing_model_name() -> str:
    from alice_core.engine_config import writing_model

    return writing_model()

_ollama_ok: bool | None = None
_loaded: str | None = None

T = TypeVar("T", bound=BaseModel)


class CloudLLMForbidden(RuntimeError):
    pass


def _assert_local(url: str) -> None:
    lowered = url.lower()
    for banned in ("openai.com", "anthropic.com", "amazonaws.com", "googleapis.com/v1beta"):
        if banned in lowered:
            raise CloudLLMForbidden(f"cloud LLM host forbidden: {url}")
    host = urlparse(url).hostname or ""
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise CloudLLMForbidden(f"LLM host must be local Ollama, got {host}")


def ollama_reachable() -> bool:
    global _ollama_ok
    if _ollama_ok is not None:
        return _ollama_ok
    try:
        import httpx

        r = httpx.get(f"{OLLAMA_HOST.rstrip('/')}/api/tags", timeout=0.4)
        _ollama_ok = r.status_code == 200
    except Exception:
        _ollama_ok = False
    return _ollama_ok


def unload_and_load(model: str) -> None:
    """Keep one model hot on 16GB. Unload the other via keep_alive=0."""
    global _loaded
    _assert_local(OLLAMA_BASE)
    if _loaded == model:
        return
    try:
        import httpx

        base = OLLAMA_HOST.rstrip("/")
        if _loaded:
            httpx.post(
                f"{base}/api/generate",
                json={"model": _loaded, "keep_alive": 0, "prompt": ""},
                timeout=30,
            )
        httpx.post(
            f"{base}/api/generate",
            json={"model": model, "keep_alive": "10m", "prompt": "ok", "options": {"num_predict": 1}},
            timeout=60,
        )
        _loaded = model
    except Exception:
        _loaded = model


def _client():
    _assert_local(OLLAMA_BASE)
    from openai import OpenAI

    return OpenAI(base_url=OLLAMA_BASE, api_key=os.environ.get("OPENAI_API_KEY", "ollama"))


def structured(model: str, schema: type[T], system: str, user: str) -> T:
    if not ollama_reachable():
        raise RuntimeError("ollama not reachable")
    unload_and_load(model)
    import instructor

    patched = instructor.from_openai(_client(), mode=instructor.Mode.JSON)
    return patched.chat.completions.create(
        model=model,
        response_model=schema,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_retries=1,
        temperature=0.1,
    )


def complete(model: str, system: str, user: str) -> str:
    if not ollama_reachable():
        raise RuntimeError("ollama not reachable")
    unload_and_load(model)
    resp = _client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return (resp.choices[0].message.content or "").strip()
