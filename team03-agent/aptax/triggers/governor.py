"""Governor — admits or refuses every envelope before any cost is incurred
(agent_design.md §4.4, S17 events/governor.py).

Checks, in order; the first that fails refuses, and the refusal is recorded with the
name of the control:

1. dedupe              (source, id) already seen
2. kill_switch         config/kill exists or APTAX_KILL=1
3. self_trigger        the actor is one of our own identities or the subscription's ignore_actors
4. source_rate_limit   more than 120 envelopes per minute from one source
5. max_runs_per_day    slot claimed atomically from a window persisted in SQLite, so
                       concurrent deciders can't overshoot and a restart doesn't reset the day
6. daily_budget        the subscription's LLM spend today has reached its daily limit

(plus subscription_match, when an envelope is offered to a subscription it doesn't match.)
Every decision — admit or refuse — is recorded, so a quiet night can be told apart from
a broken one. An admitted envelope gets its run budget: min(per-run, what is left today).
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from aptax.clock import tenant_today
from aptax.config import kill_switch_on, self_actors

SOURCE_RATE_PER_MINUTE = 120


@dataclass(frozen=True)
class Admission:
    admitted: bool
    control: str | None = None
    reason: str = ""
    run_budget_usd: float | None = None


class Governor:
    def __init__(self, store, *, rate_per_minute: int = SOURCE_RATE_PER_MINUTE,
                 kill=kill_switch_on, actors=self_actors, today=tenant_today):
        self.store = store
        self.rate_per_minute = rate_per_minute
        self._kill = kill
        self._actors = actors
        self._today = today

    def admit(self, env, sub) -> Admission:
        if not self.store.ingest_envelope(env):
            return self._refuse(env, sub, "dedupe", f"envelope {env.source}/{env.id} was already seen",
                                ingested=False)
        if not sub.matches(env):
            return self._refuse(env, sub, "subscription_match", f"{env.type} from {env.source} does not match {sub.id}")
        if self._kill():
            return self._refuse(env, sub, "kill_switch", "the kill switch is on")
        if env.actor and env.actor in (self._actors() | set(sub.ignore_actors)):
            return self._refuse(env, sub, "self_trigger", f"caused by our own identity {env.actor}")
        since = (datetime.now(UTC) - timedelta(minutes=1)).isoformat(timespec="seconds")
        recent = self.store.count_recent_envelopes(env.source, since)
        if recent > self.rate_per_minute:
            return self._refuse(env, sub, "source_rate_limit",
                                f"{recent} envelopes from {env.source} in the last minute (limit {self.rate_per_minute})")

        window, day = sub.window(env.tenant), self._today(env.tenant).isoformat()
        limit = sub.budget.max_runs_per_day
        ok, count = self.store.window_reserve(window, day, "runs", limit)
        if not ok:
            return self._refuse(env, sub, "max_runs_per_day", f"{count} runs already today (limit {limit})")
        spent = self.store.window_spend(window, day, "llm")
        daily = sub.budget.daily_usd
        if daily is not None and spent >= daily:
            return self._refuse(env, sub, "daily_budget", f"${spent:.4f} spent today (limit ${daily:.2f})")

        budgets = [b for b in (sub.budget.per_run_usd, None if daily is None else daily - spent) if b is not None]
        self.store.set_admitted(env.source, env.id, True)
        self.store.add_decision(env.source, env.id, sub.id, "admit",
                                f"run {count} today" + (f" of {limit}" if limit else ""))
        return Admission(True, run_budget_usd=min(budgets) if budgets else None)

    def record_spend(self, sub, tenant: str, usd: float) -> None:
        if usd:
            self.store.window_add_spend(sub.window(tenant), self._today(tenant).isoformat(), "llm", usd)

    def _refuse(self, env, sub, control: str, reason: str, *, ingested: bool = True) -> Admission:
        self.store.add_refusal(control, reason, source=env.source, envelope_id=env.id,
                               subscription_id=sub.id, detail={"type": env.type, "tenant": env.tenant})
        self.store.add_decision(env.source, env.id, sub.id, "refuse", f"{control}: {reason}")
        if ingested:
            self.store.set_admitted(env.source, env.id, False)
        return Admission(False, control, reason)
