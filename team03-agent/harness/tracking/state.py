"""Finding fingerprints — so a daily run doesn't re-escalate the same thing 30 times.

A finding is *new* if its fingerprint has not been seen for this tenant, or if its
exposure moved into a different bucket (harness_plan.md §4.8).

`FindingStore` is the seam: `LocalJsonStore` today, an `AgentMemory`-backed store once
its schema is confirmed (open question Q6). The runner only depends on the protocol.
"""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from scripts.findings import Finding

BUCKETS = [Decimal(x) for x in ("0", "50000", "100000", "500000", "1000000", "5000000", "10000000")]


def exposure_bucket(amount: Decimal) -> int:
    return sum(1 for edge in BUCKETS if amount >= edge)


def fingerprint(f: Finding, period: str) -> str:
    raw = f"{f.rule}|{f.entity_id}|{period}|{exposure_bucket(f.total_exposure)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


class FindingStore(Protocol):
    def is_new(self, tenant: str, fp: str) -> bool: ...
    def remember(self, tenant: str, fp: str, f: Finding) -> None: ...
    def flush(self) -> None: ...


class LocalJsonStore:
    def __init__(self, path: Path):
        self.path = path
        self._data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def is_new(self, tenant, fp):
        return fp not in self._data.get(tenant, {})

    def remember(self, tenant, fp, f):
        now = datetime.now().isoformat(timespec="seconds")
        entry = self._data.setdefault(tenant, {}).setdefault(
            fp, {"first_seen": now, "rule": f.rule, "entity_ref": f.entity_ref})
        entry["last_seen"] = now

    def flush(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=1), encoding="utf-8")


class MemoryStore:
    """No persistence — for replays and hand-written tests."""

    def __init__(self):
        self._seen: set[tuple[str, str]] = set()

    def is_new(self, tenant, fp):
        return (tenant, fp) not in self._seen

    def remember(self, tenant, fp, f):
        self._seen.add((tenant, fp))

    def flush(self):
        pass
