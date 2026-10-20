#!/usr/bin/env python3
"""Local runtime smoke: Typst, Ollama models, tok/s, RAM. No cloud endpoints."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERMES = "hermes3:8b"
GEMMA = "gemma2:9b"
OLLAMA = "http://127.0.0.1:11434"
MIN_TPS = 35
MAX_BOTH_GB = 11.0
ESTIMATE_GB = {HERMES: 4.8, GEMMA: 5.6}


def fail(msg: str) -> None:
    print(f"FAIL {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"ok   {msg}")


def main() -> None:
    if not shutil.which("typst"):
        fail("typst not on PATH (brew install typst)")
    ver = subprocess.check_output(["typst", "--version"], text=True).strip()
    ok(ver)

    try:
        with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=2) as resp:
            listing = json.load(resp)
    except (urllib.error.URLError, TimeoutError) as exc:
        fail(f"ollama not reachable at {OLLAMA}: {exc}")

    names = {m.get("name") for m in listing.get("models") or []}
    for model in (HERMES, GEMMA):
        if not any(model in n for n in names):
            fail(f"ollama list missing {model}")
        ok(f"model present {model}")

    both = ESTIMATE_GB[HERMES] + ESTIMATE_GB[GEMMA]
    print(f"est  Hermes {ESTIMATE_GB[HERMES]}GB + Gemma {ESTIMATE_GB[GEMMA]}GB = {both}GB")
    if both > MAX_BOTH_GB:
        fail(f"both models together exceed {MAX_BOTH_GB}GB; swap one at a time")
    print("note load one model at a time on 16GB (swap < 1.2s)")

    for model in (HERMES, GEMMA):
        tps = generate_tps(model)
        print(f"perf {model} {tps:.1f} tok/s")
        if tps < MIN_TPS:
            fail(f"{model} {tps:.1f} tok/s < {MIN_TPS}")
        ok(f"{model} meets {MIN_TPS} tok/s")
    sys.exit(0)


def generate_tps(model: str) -> float:
    payload = json.dumps(
        {
            "model": model,
            "prompt": "Count from 1 to 8, then stop.",
            "stream": False,
            "options": {"num_predict": 64, "temperature": 0},
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.load(resp)
    elapsed = time.perf_counter() - t0
    eval_count = float(body.get("eval_count") or 64)
    eval_ns = body.get("eval_duration")
    if eval_ns:
        return eval_count / (eval_ns / 1e9)
    return eval_count / max(elapsed, 0.001)


if __name__ == "__main__":
    main()
