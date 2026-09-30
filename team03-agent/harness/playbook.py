"""Playbook and Rule base classes — what every use case plugs into.

Patterns:
- **Template Method** — `Playbook.run()` is the fixed skeleton:
      fetch (I/O)  →  evaluate rules (pure)  →  sort  →  context + summary
  A use case overrides the hooks (`fetch`, `rules`, optionally `context`, `summary`,
  `sort_key`) and never the skeleton, so every playbook behaves the same way in the
  runner, the report and the escalation writer.
- **Strategy** — each check is a `Rule`. A playbook is a list of rules over one
  dataset; rules can be added, removed, reordered or reused across use cases without
  touching the playbook.
- `RecordRule` is a second, smaller Template Method for the common case "for each
  record in one dataset: does it apply? then build a finding".

Why the split between `fetch` and `evaluate`: `evaluate(dataset, ctx)` does no I/O.
Hand-written tests (harness_plan.md §8) build a `Dataset` from a few dicts and assert
on the findings, with no network, credentials or mocks.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from decimal import Decimal

from scripts.findings import Finding


class Dataset(dict):
    """Named record sets for one playbook run, e.g. {"ewb": [...], "invoices": [...]},
    plus lookup indexes rules share instead of rebuilding."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._indexes: dict[tuple, dict] = {}

    def index(self, source: str, key: str) -> dict:
        """{record[key]: record} over dataset[source], built once."""
        cache_key = (source, key)
        if cache_key not in self._indexes:
            self._indexes[cache_key] = {r.get(key): r for r in self.get(source, []) if r.get(key)}
        return self._indexes[cache_key]


class Rule(ABC):
    """Strategy: one independent check. `id` becomes Finding.rule."""

    id: str = ""
    severity: int = 50            # higher sorts first
    platform_contradiction = False  # True → findings also go to anomalies.jsonl

    @abstractmethod
    def evaluate(self, data: Dataset, ctx) -> Iterable[Finding]: ...


class RecordRule(Rule):
    """Template Method for per-record checks: subclasses fill `applies` and `finding`."""

    source: str = ""

    def evaluate(self, data: Dataset, ctx) -> Iterator[Finding]:
        for record in data.get(self.source, []):
            if self.applies(record, data, ctx):
                yield self.finding(record, data, ctx)

    @abstractmethod
    def applies(self, record: dict, data: Dataset, ctx) -> bool: ...

    @abstractmethod
    def finding(self, record: dict, data: Dataset, ctx) -> Finding: ...


@dataclass
class PlaybookOutcome:
    findings: list[Finding]
    context: dict = field(default_factory=dict)
    anomalies: list[dict] = field(default_factory=list)
    summary: str = ""


class Playbook(ABC):
    manifest = None   # set by the registry when it instantiates the class

    @property
    @abstractmethod
    def rules(self) -> list[Rule]: ...

    @abstractmethod
    def fetch(self, ctx, fetcher) -> Dataset:
        """All I/O for the run happens here, through the gateway-backed fetcher."""

    # -- the skeleton: do not override ------------------------------------------

    def run(self, ctx, fetcher) -> PlaybookOutcome:
        data = self.fetch(ctx, fetcher)
        findings = sorted(self.evaluate(data, ctx), key=self.sort_key)
        outcome = PlaybookOutcome(
            findings=findings,
            context=self.context(data, findings, ctx),
            anomalies=[self.anomaly(f, ctx) for f in findings if self._contradiction(f)],
        )
        outcome.summary = self.summary(outcome, ctx)
        return outcome

    def evaluate(self, data: Dataset, ctx) -> list[Finding]:
        """Pure: dataset in, findings out. The entry point for hand-written tests."""
        return [f for rule in self.rules for f in rule.evaluate(data, ctx)]

    # -- hooks with sensible defaults ---------------------------------------------

    @staticmethod
    def sort_key(f: Finding):
        return (-f.severity, -f.total_exposure)

    def context(self, data: Dataset, findings: list[Finding], ctx) -> dict:
        return {name: len(records) for name, records in data.items()}

    def summary(self, outcome: PlaybookOutcome, ctx) -> str:
        total = sum((f.total_exposure for f in outcome.findings), Decimal("0"))
        return f"{len(outcome.findings)} findings; total exposure {total}."

    def anomaly(self, f: Finding, ctx) -> dict:
        return {"run_id": ctx.run_id, "playbook": getattr(self.manifest, "id", None),
                "rule": f.rule, "entity_type": f.entity_type, "entity_id": f.entity_id,
                "entity_ref": f.entity_ref, "summary": f.summary, "details": f.details}

    def _contradiction(self, f: Finding) -> bool:
        return any(r.platform_contradiction and r.id == f.rule for r in self.rules)
