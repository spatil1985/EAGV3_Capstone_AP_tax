"""Heartbeats for background loops (agent_design.md §4.14, S17 events/report.py).

A loop calls `beat(name)` every cycle. `/v1/liveness` answers 503 once any registered
loop has been silent for more than 900 s, so "alive but quiet" can be told apart from
"dead". Phase 1 has no background loops; the scheduler and watcher register here.
"""

import threading
import time

STALE_AFTER_SECONDS = 900

_lock = threading.Lock()
_beats: dict[str, float] = {}


def beat(name: str) -> None:
    with _lock:
        _beats[name] = time.time()


def status(now: float | None = None) -> tuple[bool, dict]:
    now = now or time.time()
    with _lock:
        ages = {name: round(now - ts) for name, ts in _beats.items()}
    return all(age <= STALE_AFTER_SECONDS for age in ages.values()), ages
