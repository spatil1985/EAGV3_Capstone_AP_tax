"""TriggerEnvelope — one shape for every way work starts (agent_design.md §4.1).

S17's EventEnvelope plus tenant and trust:

| Trigger    | Producer                 | trust     | type                              | id                                   |
|------------|--------------------------|-----------|-----------------------------------|--------------------------------------|
| on_request | CLI, POST /v1/ask        | owner     | request.ask (request.run/.call)   | uuid                                 |
| scheduled  | scheduler loop           | system    | schedule.tick                     | {schedule_id}:{tick_iso}             |
| on_event   | watcher loop             | untrusted | agentswitch.{entity}.{kind}       | {tenant}:{entity}:{id}:{updated_at}:{kind} |

The event id carries the kind because one update can produce several transitions
(approval_status_changed and status_changed at the same updated_at), and each needs
its own dedupe key.

Trust marks the *data*, never authority: authority comes from the subscription. Only an
owner envelope may carry free text (the operator's own question); system and untrusted
envelopes may hold ids, enums and {field, from, to} transitions only, so a vendor's
notes can never influence routing.
"""

import re
import uuid
from dataclasses import dataclass, field

from aptax.config import TENANTS
from aptax.store.db import now_iso

TRUST = ("owner", "system", "untrusted")
MAX_CLEAN_TEXT = 128


def _check_clean(value, depth: int = 0) -> None:
    if depth > 3:
        raise ValueError("envelope data is nested too deeply")
    if isinstance(value, dict):
        for k, v in value.items():
            _check_clean(str(k), depth + 1)
            _check_clean(v, depth + 1)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _check_clean(v, depth + 1)
    elif isinstance(value, str):
        if len(value) > MAX_CLEAN_TEXT or "\n" in value:
            raise ValueError("free text is not allowed in system or untrusted envelope data")
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise ValueError(f"unsupported envelope value type {type(value).__name__}")


@dataclass(frozen=True)
class TriggerEnvelope:
    id: str
    source: str
    type: str
    tenant: str
    trust: str
    occurred_at: str
    observed_at: str
    subject: str | None = None
    actor: str | None = None
    traceparent: str | None = None
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        if not (self.id and self.source and self.type):
            raise ValueError("an envelope needs id, source and type")
        if self.tenant not in TENANTS:
            raise ValueError(f"unknown tenant {self.tenant!r}")
        if self.trust not in TRUST:
            raise ValueError(f"trust must be one of {TRUST}")
        if not isinstance(self.data, dict):
            raise ValueError("envelope data must be an object")
        if self.trust != "owner":
            _check_clean(self.data)


def snake(entity: str) -> str:
    """PaymentMade → payment_made, AgentEscalation → agent_escalation."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", entity).lower()


def request_envelope(tenant: str, kind: str, data: dict, *, source: str = "user.cli",
                     actor: str = "operator") -> TriggerEnvelope:
    """An owner request: kind is ask, run, call or routes."""
    now = now_iso()
    return TriggerEnvelope(id=uuid.uuid4().hex, source=source, type=f"request.{kind}", tenant=tenant,
                           trust="owner", occurred_at=now, observed_at=now, actor=actor, data=dict(data))


def ask_envelope(tenant: str, question: str, *, source: str = "user.cli") -> TriggerEnvelope:
    return request_envelope(tenant, "ask", {"question": question}, source=source)


def tick_envelope(schedule_id: str, tenant: str, tick_iso: str, *, catch_up: bool = False) -> TriggerEnvelope:
    return TriggerEnvelope(id=f"{schedule_id}:{tick_iso}", source=f"cron.{schedule_id}", type="schedule.tick",
                           tenant=tenant, trust="system", occurred_at=tick_iso, observed_at=now_iso(),
                           actor="scheduler", data={"schedule_id": schedule_id, "catch_up": catch_up})


def event_envelope(tenant: str, entity: str, record_id: str, updated_at: str, kind: str, *,
                   actor: str | None, transition: dict | None = None) -> TriggerEnvelope:
    data = {"entity": entity, "id": record_id}
    if transition:
        data["transition"] = transition
    return TriggerEnvelope(id=f"{tenant}:{entity}:{record_id}:{updated_at}:{kind}", source=f"agentswitch.{tenant}",
                           type=f"agentswitch.{snake(entity)}.{kind}", tenant=tenant, trust="untrusted",
                           occurred_at=updated_at, observed_at=now_iso(), subject=f"{entity}/{record_id}",
                           actor=actor, data=data)
