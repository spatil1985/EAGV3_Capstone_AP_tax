"""Deterministic playbook runner — no LLM (harness_plan.md §1 principle 2).

Pattern: **Facade**. `Runner.run()` hides the registry, gateway scoping, fingerprint
store, anomaly log, escalations and renderers behind one call, so the CLI, a cron job
and (later) the LLM loop's `run_playbook_ucNN` tool all run a playbook the same way.

One failing playbook never aborts the run; its error is reported and the rest continue.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from harness.core.playbook import PlaybookOutcome
from harness.core.registry import Registry, Route
from harness.tracking.state import fingerprint
from scripts.money import fmt


@dataclass
class PlaybookRun:
    route: Route
    outcome: PlaybookOutcome | None = None
    error: str | None = None
    new_fingerprints: set = field(default_factory=set)
    escalation: dict | None = None

    @property
    def new_count(self) -> int:
        return len(self.new_fingerprints)

    @property
    def repeat_count(self) -> int:
        return len(self.outcome.findings) - self.new_count if self.outcome else 0


@dataclass
class RunResult:
    ctx: object
    runs: list[PlaybookRun]

    def headline(self) -> str:
        ran = [r for r in self.runs if r.outcome]
        findings = [f for r in ran for f in r.outcome.findings]
        # One document can trip several rules; count its exposure once.
        per_entity = {(f.entity_type, f.entity_id): f.total_exposure for f in findings}
        exposure = sum(per_entity.values(), Decimal("0"))
        new = sum(r.new_count for r in ran)
        errors = sum(1 for r in self.runs if r.error)
        return (f"{len(ran)} playbook(s) ran: {len(findings)} findings ({new} new), "
                f"{fmt(exposure, self.ctx.currency)} affected"
                + (f"; {errors} failed" if errors else "") + ".")


class Runner:
    def __init__(self, *, registry: Registry, gateway, fetcher, store, anomaly_log,
                 renderers, escalations=None):
        self.registry = registry
        self.gateway = gateway
        self.fetcher = fetcher
        self.store = store
        self.anomaly_log = anomaly_log
        self.renderers = renderers
        self.escalations = escalations

    def run(self, ctx, *, trigger: str, cadence: str | None = None,
            ids: list[str] | None = None) -> tuple[RunResult, list[str]]:
        runs = []
        for route in self.registry.route(ctx, trigger=trigger, cadence=cadence, ids=ids):
            run = PlaybookRun(route)
            runs.append(run)
            if route.action == "run":
                self._execute(ctx, run)
        self.store.flush()
        result = RunResult(ctx, runs)
        return result, [r.write(result) for r in self.renderers]

    def _execute(self, ctx, run: PlaybookRun) -> None:
        manifest = run.route.manifest
        try:
            playbook = self.registry.instantiate(manifest)
            with self.gateway.scoped(manifest.tools):
                outcome = playbook.run(ctx, self.fetcher)
        except Exception as exc:  # noqa: BLE001 — isolate one playbook's failure
            run.error = f"{type(exc).__name__}: {exc}"
            return

        stamped = []
        for f in outcome.findings:
            fp = fingerprint(f, ctx.period)
            if self.store.is_new(ctx.tenant, fp):
                run.new_fingerprints.add(fp)
            self.store.remember(ctx.tenant, fp, f)
            stamped.append(f.stamped(ctx.run_id, fp))
        outcome.findings = stamped
        run.outcome = outcome

        for anomaly in outcome.anomalies:
            self.anomaly_log.record(anomaly)
        if self.escalations:
            run.escalation = self.escalations.write(ctx, run)
