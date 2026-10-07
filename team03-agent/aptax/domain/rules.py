"""Rulebook — statutory numbers as effective-dated data (agent_design.md §4.12, G6).

Two entry formats are accepted, so today's playbooks/constants.yaml keeps working:

    # legacy (one value)
    eway_bill_threshold_inr: {value: 50000, unit: ..., source: ..., verified: null}

    # effective-dated (a list, oldest first)
    rbi_bank_rate_pct:
      - {value: 6.50, effective_from: 2023-02-08, effective_to: 2025-02-06, source: ...}
      - {value: 6.25, effective_from: 2025-02-07, source: ..., review_by: 2026-12-31}

`rule(name, on=date)` returns the value in force on that date, so an FY 2025-26 document
is judged by FY 2025-26 law. Every lookup is remembered as `name → "value @effective_from"`
so a finding can say which rule version produced it (`rules_used`). Entries past their
`review_by` date are reported as stale instead of silently trusted.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml


class RuleMissing(KeyError):
    pass


def _as_date(value) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


@dataclass(frozen=True)
class RuleVersion:
    value: object
    effective_from: date | None
    effective_to: date | None
    source: str
    review_by: date | None

    def in_force(self, on: date) -> bool:
        return ((self.effective_from is None or self.effective_from <= on)
                and (self.effective_to is None or on <= self.effective_to))


@dataclass
class Rulebook:
    entries: dict[str, list[RuleVersion]] = field(default_factory=dict)
    used: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, *paths: Path) -> "Rulebook":
        book = cls()
        for path in paths:
            path = Path(path)
            files = sorted(path.rglob("*.yaml")) if path.is_dir() else [path]
            for f in files:
                if not f.exists():
                    continue
                raw = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                for name, entry in raw.items():
                    versions = entry if isinstance(entry, list) else [entry]
                    book.entries[name] = [
                        RuleVersion(value=v.get("value"),
                                    effective_from=_as_date(v.get("effective_from")),
                                    effective_to=_as_date(v.get("effective_to")),
                                    source=str(v.get("source") or ""),
                                    review_by=_as_date(v.get("review_by")))
                        for v in versions if isinstance(v, dict)]
        return book

    def rule(self, name: str, on: date | None = None):
        on = on or date.today()
        versions = self.entries.get(name)
        if not versions:
            raise RuleMissing(f"rule {name!r} missing from the rulebook")
        for v in reversed(versions):
            if v.in_force(on):
                self.used[name] = f"{v.value} @{v.effective_from or 'always'}"
                return v.value
        raise RuleMissing(f"rule {name!r} has no version in force on {on}")

    def stale(self, on: date | None = None) -> list[str]:
        on = on or date.today()
        return sorted(name for name, versions in self.entries.items()
                      for v in versions if v.review_by and v.review_by < on and v.in_force(on))

    def flat(self, on: date | None = None) -> dict:
        """{name: value in force} — for code that still reads ctx.constants."""
        out = {}
        for name in self.entries:
            try:
                out[name] = self.rule(name, on)
            except RuleMissing:
                continue
        self.used.clear()
        return out
