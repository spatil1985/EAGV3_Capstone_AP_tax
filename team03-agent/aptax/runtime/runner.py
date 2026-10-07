"""Deterministic playbook runner — no LLM (agent_design.md §4.7, principle 2).

Pattern: **Facade**, ported from harness/core/runner.py. The CLI, scheduled pipelines and
the agent loop's playbook capabilities all run a playbook through `run_one`, so it
behaves the same way in every mode:

    route → instantiate → fetch + evaluate (scoped allowlist) → fingerprint against
    memory → keep rows for paging → anomalies → digest escalation (if allowed)

One failing playbook never aborts the others; its error is reported.
"""

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal

from aptax.playbooks.manifest import Manifest, Route, instantiate, route
from aptax.runtime.actions import Actions

BUCKETS = [Decimal(x) for x in ("0", "50000", "100000", "500000", "1000000", "5000000", "10000000")]


def exposure_bucket(amount: Decimal) -> int:
    return sum(1 for edge in BUCKETS if amount >= edge)


def fingerprint(f, period: str) -> str:
    """rule | entity | period | exposure bucket — the formula the retired harness used, so memories stay comparable."""
    raw = f"{f.rule}|{f.entity_id}|{period}|{exposure_bucket(f.total_exposure)}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


@dataclass
class PlaybookRun:
    route: Route
    outcome: object | None = None
    error: str | None = None
    new_fingerprints: set = field(default_factory=set)
    escalation: dict | None = None

    @property
    def manifest(self) -> Manifest:
        return self.route.manifest

    @property
    def new_count(self) -> int:
        return len(self.new_fingerprints)


class PlaybookRunner:
    def __init__(self, ctx, gateway, fetcher, store, manifests: list[Manifest]):
        self.ctx = ctx
        self.gw = gateway
        self.fetcher = fetcher
        self.store = store
        self.manifests = manifests
        self.actions = Actions(ctx, gateway, store)

    def get(self, ident: str) -> Manifest:
        for m in self.manifests:
            if ident in (m.id, m.capability):
                return m
        raise KeyError(f"no playbook {ident!r}")

    def routes(self, *, trigger: str | None = None, cadence: str | None = None) -> list[Route]:
        tools = self.gw.available_tools()
        return [route(m, self.ctx, available_tools=tools, trigger=trigger, cadence=cadence)
                for m in self.manifests]

    def run_one(self, manifest: Manifest, *, escalate: bool = False) -> PlaybookRun:
        run = PlaybookRun(route(manifest, self.ctx, available_tools=self.gw.available_tools()))
        if run.route.action != "run":
            return run
        try:
            playbook = instantiate(manifest)
            with self.gw.scoped(manifest.tools):
                outcome = playbook.run(self.ctx, self.fetcher)
        except Exception as exc:  # noqa: BLE001 — isolate one playbook's failure
            run.error = f"{type(exc).__name__}: {exc}"
            self.store.journal(self.ctx.run_id, "note", {"playbook": manifest.id, "error": run.error})
            return run

        stamped, rows = [], []
        for f in outcome.findings:
            fp = fingerprint(f, self.ctx.period)
            if self.store.finding_is_new(self.ctx.tenant, fp, self.ctx.dry_run):
                run.new_fingerprints.add(fp)
            self.store.remember_finding(self.ctx.tenant, fp, self.ctx.dry_run, playbook=manifest.id,
                                        finding=f, run_id=self.ctx.run_id)
            sf = f.stamped(self.ctx.run_id, fp)
            stamped.append(sf)
            rows.append(sf.to_dict())
        outcome.findings = stamped
        run.outcome = outcome
        self.store.add_run_findings(self.ctx.run_id, manifest.id, rows)
        for anomaly in outcome.anomalies:
            self.store.record_anomaly(self.ctx.run_id, manifest.id, anomaly)
        self.store.journal(self.ctx.run_id, "capability", {
            "playbook": manifest.id, "findings": len(stamped), "new": run.new_count,
            "anomalies": len(outcome.anomalies), "summary": outcome.summary})

        if escalate and manifest.escalate == "digest":
            new = [f for f in stamped if f.fingerprint in run.new_fingerprints]
            run.escalation = self.actions.escalate_digest(manifest, outcome.summary, new)
        return run
