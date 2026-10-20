from __future__ import annotations

from typing import Callable

from alice_core.schemas import Listing


def _safe(name: str, fn: Callable[[], list[Listing]]) -> Callable[[], list[Listing]]:
    def wrapped() -> list[Listing]:
        try:
            return fn()
        except Exception:
            return []

    wrapped.__name__ = name
    return wrapped


def _load() -> dict[str, Callable[[], list[Listing]]]:
    from alice_core.sources import (
        arbeitnow,
        ats_boards,
        himalayas,
        hnhiring,
        jobspy,
        remoteok,
        remotive,
        wwr,
    )

    return {
        "remoteok": _safe("remoteok", remoteok.pull),
        "remotive": _safe("remotive", remotive.pull),
        "arbeitnow": _safe("arbeitnow", arbeitnow.pull),
        "himalayas": _safe("himalayas", himalayas.pull),
        "wwr": _safe("wwr", wwr.pull),
        "hnhiring": _safe("hnhiring", hnhiring.pull),
        "ats_boards": _safe("ats_boards", ats_boards.pull),
        "jobspy": _safe("jobspy", jobspy.pull),
    }


class _Pullers:
    def get(self, name: str):
        return _load().get(name)


pullers = _Pullers()
