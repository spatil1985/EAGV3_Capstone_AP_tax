"""Subscriptions: for matching envelopes, what to run, with what authority and budget
(agent_design.md §4.5). Human-owned config — authority never comes from the data.

Phase 1 ships the built-ins:
- `ask`     on_request through the agent loop. Side effects default to escalate and
            add_todo (no action capability is offered yet, so nothing can be written).
- `manual`  operator commands: deterministic playbook runs (`aptax run`), single
            capability calls (`aptax call`) and route listings. May escalate, which
            dry-run suppresses unless the operator passes --send.

Budgets follow the Q12 proposal ($0.05 per run, $1 per tenant per day) until decided.
YAML subscriptions in config/subscriptions/ (scheduled and on_event) arrive in Phase 3
with these same fields.
"""

import fnmatch
from dataclasses import dataclass, field

EFFECTS = frozenset({"escalate", "add_todo", "request_approval", "hold_for_review"})


@dataclass(frozen=True)
class Budget:
    per_run_usd: float | None = None
    daily_usd: float | None = None
    max_runs_per_day: int | None = None


@dataclass(frozen=True)
class Subscription:
    id: str
    mode: str                                   # agent | pipeline
    event_types: tuple = ("*",)                 # fnmatch globs
    sources: tuple = ("*",)
    enabled: bool = True
    ignore_actors: tuple = ()
    allowed_side_effects: frozenset = frozenset()
    budget: Budget = field(default_factory=Budget)
    escalate: str = "digest"

    def __post_init__(self):
        unknown = set(self.allowed_side_effects) - EFFECTS
        if unknown:
            raise ValueError(f"{self.id}: unknown side effect(s) {sorted(unknown)}")
        if self.mode not in ("agent", "pipeline"):
            raise ValueError(f"{self.id}: mode must be agent or pipeline")

    def matches(self, env) -> bool:
        return (self.enabled
                and any(fnmatch.fnmatchcase(env.type, p) for p in self.event_types)
                and any(fnmatch.fnmatchcase(env.source, p) for p in self.sources))

    def window(self, tenant: str) -> str:
        """Daily windows are per subscription and tenant."""
        return f"{self.id}@{tenant}"


ASK = Subscription(
    id="ask", mode="agent", event_types=("request.ask",), sources=("user.*",),
    allowed_side_effects=frozenset({"escalate", "add_todo"}),
    budget=Budget(per_run_usd=0.05, daily_usd=1.00, max_runs_per_day=200))

MANUAL = Subscription(
    id="manual", mode="pipeline", event_types=("request.run", "request.call", "request.routes"),
    sources=("user.*",), allowed_side_effects=frozenset({"escalate"}),
    budget=Budget(max_runs_per_day=500))
