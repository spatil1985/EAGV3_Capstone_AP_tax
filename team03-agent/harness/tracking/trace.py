"""Run tracing and anomaly capture.

Pattern: **Observer**. `ToolGateway` publishes a `ToolCallEvent` for every call
(allowed, refused or suppressed) to an `EventBus`; subscribers decide what to do
with it. Adding a new sink (metrics, cost report) means subscribing, not editing the
gateway.

Credentials never reach this module: events carry tool names and arguments only.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


@dataclass
class ToolCallEvent:
    run_id: str
    seq: int
    tool: str
    args: dict
    tier: str
    outcome: str          # called | refused | suppressed
    ok: bool
    ms: int = 0
    rows: int | None = None
    result_hash: str | None = None
    reason: str | None = None


Subscriber = Callable[[ToolCallEvent], None]


class EventBus:
    def __init__(self):
        self._subscribers: list[Subscriber] = []

    def subscribe(self, subscriber: Subscriber) -> None:
        self._subscribers.append(subscriber)

    def publish(self, event: ToolCallEvent) -> None:
        for subscriber in self._subscribers:
            subscriber(event)


def result_hash(data) -> str:
    return hashlib.sha1(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]


class JsonlTraceWriter:
    """Subscriber: appends every event to runs/<run_id>/trace.jsonl."""

    def __init__(self, run_dir: Path):
        run_dir.mkdir(parents=True, exist_ok=True)
        self.path = run_dir / "trace.jsonl"

    def __call__(self, event: ToolCallEvent) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), default=str) + "\n")


class CallCounter:
    """Subscriber: in-memory tallies for the run summary and for tests."""

    def __init__(self):
        self.called = 0
        self.refused: list[ToolCallEvent] = []
        self.suppressed: list[ToolCallEvent] = []

    def __call__(self, event: ToolCallEvent) -> None:
        if event.outcome == "called":
            self.called += 1
        elif event.outcome == "refused":
            self.refused.append(event)
        else:
            self.suppressed.append(event)


class AnomalyLog:
    """runs/<run_id>/anomalies.jsonl — platform values that contradict our recomputation.

    Feeds the bug bounty (harness_plan.md §4.9). A human reviews every entry before
    anything is filed; the harness never auto-files.
    """

    def __init__(self, run_dir: Path):
        run_dir.mkdir(parents=True, exist_ok=True)
        self.path = run_dir / "anomalies.jsonl"
        self.count = 0

    def record(self, anomaly: dict) -> None:
        self.count += 1
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(anomaly, default=str) + "\n")
