"""ToolGateway — the policy layer between the harness and MCP (harness_plan.md §4.3).

Patterns:
- **Proxy** — `ToolGateway` has the same `call_tool` / `rest_get` shape as a
  `Transport`, so playbooks and the fetcher cannot tell they are talking to a guard.
  Every MCP call from the deterministic runner (and later the LLM loop) goes through it.
- **Chain of Responsibility** — each `Policy` inspects a call and either decides
  (refuse / suppress) or passes it on. The first decision wins; if none decides, the
  call goes through. New rules are new `Policy` classes, inserted in the chain.
- Events go to an `EventBus` (**Observer**, see trace.py).

Refusals happen *before* the transport is touched, so a refused call shows zero MCP
traffic in the trace — which is what the boundary tests check.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum

from harness.trace import EventBus, ToolCallEvent, result_hash
from harness.transport import ToolResult, Transport


class Tier(IntEnum):
    READ = 0       # *.list, *.get, read endpoints
    ANNOTATE = 1   # escalations, todos, memory — deduped, suppressed in dry-run
    WORKFLOW = 2   # approval submits — off by default
    MUTATE = 3     # anything that changes a ledger document — never


ANNOTATE_TOOLS = {
    "AgentEscalation.create", "AgentEscalation.update", "AgentTodo.create",
    "Notification.create", "AgentMemory.create", "AgentMemory.update",
}
WORKFLOW_TOOLS = {"Bill.approval.submit", "Invoice.approval.submit"}
# endpoint.* tools that only read, whatever their _meta risk tag says (see N3).
READ_ENDPOINTS = {"endpoint.accounting.bill_match"}

PROHIBITED_ENTITIES = {"SalarySlip", "Contract", "EsignDocument"}
PROHIBITED_PREFIXES = ("Lead", "Opportunity", "Deal", "Campaign", "Crm")  # least privilege: no CRM

# Curated read allowlist (harness_plan.md §4.3 b). Playbook manifests add to it for
# the duration of their run (`ToolGateway.scoped`).
BASE_READ_ALLOWLIST = {
    "Bill.list", "Bill.get", "Invoice.list", "Invoice.get", "Party.list", "Party.get",
    "PaymentMade.list", "PaymentMade.get", "CreditNote.list", "CreditNote.get",
    "VendorCredit.list", "VendorCredit.get", "GSTReturn.list", "GSTReturn.get",
    "Item.list", "Item.get", "ApprovalRequest.list", "ApprovalRequest.get",
    "EWayBill.list", "EWayBill.get", "TaxNexus.list", "Company.list", "Company.get",
}


def classify(tool: str) -> Tier:
    if tool in ANNOTATE_TOOLS:
        return Tier.ANNOTATE
    if tool in WORKFLOW_TOOLS:
        return Tier.WORKFLOW
    if tool in READ_ENDPOINTS or tool.endswith((".list", ".get")):
        return Tier.READ
    return Tier.MUTATE


@dataclass(frozen=True)
class ToolCall:
    tool: str
    args: dict
    tier: Tier


@dataclass(frozen=True)
class Decision:
    outcome: str   # "refused" | "suppressed"
    reason: str


class Policy:
    """One link in the chain. Return a Decision to stop, or None to pass the call on."""

    def check(self, call: ToolCall) -> Decision | None:
        raise NotImplementedError


class ProhibitedEntityPolicy(Policy):
    def check(self, call):
        entity = call.tool.split(".")[0]
        if entity in PROHIBITED_ENTITIES or entity.startswith(PROHIBITED_PREFIXES):
            return Decision("refused", f"{entity} is outside Seat 03's remit; route to Admin/Human")
        return None


class WriteTierPolicy(Policy):
    def __init__(self, allow_workflow: bool = False):
        self.allow_workflow = allow_workflow

    def check(self, call):
        if call.tier is Tier.MUTATE:
            return Decision("refused", "T3 mutate: the harness never changes ledger documents")
        if call.tier is Tier.WORKFLOW and not self.allow_workflow:
            return Decision("refused", "T2 workflow is off; needs --allow-workflow")
        return None


class AllowlistPolicy(Policy):
    def __init__(self, allowed: set[str]):
        self.allowed = set(allowed)

    def check(self, call):
        if call.tier is Tier.READ and call.tool not in self.allowed:
            return Decision("refused", f"{call.tool} is not on the read allowlist")
        return None


class DryRunPolicy(Policy):
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run

    def check(self, call):
        if self.dry_run and call.tier in (Tier.ANNOTATE, Tier.WORKFLOW):
            return Decision("suppressed", "dry-run: write recorded, not sent")
        return None


class ToolGateway:
    def __init__(self, transport: Transport, bus: EventBus, run_id: str, *,
                 dry_run: bool = True, allow_workflow: bool = False,
                 allowlist: set[str] | None = None):
        self._transport = transport
        self._bus = bus
        self._run_id = run_id
        self._seq = 0
        self._allowlist = AllowlistPolicy(allowlist or BASE_READ_ALLOWLIST)
        # Order matters: identity/remit first, then write tier, then allowlist, then dry-run.
        self.policies: list[Policy] = [
            ProhibitedEntityPolicy(),
            WriteTierPolicy(allow_workflow),
            self._allowlist,
            DryRunPolicy(dry_run),
        ]

    @contextmanager
    def scoped(self, extra_tools):
        """Widen the read allowlist for one playbook, then restore it."""
        before = set(self._allowlist.allowed)
        self._allowlist.allowed |= set(extra_tools or ())
        try:
            yield self
        finally:
            self._allowlist.allowed = before

    def _publish(self, call: ToolCall, outcome: str, ok: bool, **extra) -> None:
        self._seq += 1
        self._bus.publish(ToolCallEvent(self._run_id, self._seq, call.tool, call.args,
                                        call.tier.name, outcome, ok, **extra))

    def call_tool(self, tool: str, args: dict) -> ToolResult:
        call = ToolCall(tool, dict(args), classify(tool))
        for policy in self.policies:
            decision = policy.check(call)
            if decision is None:
                continue
            self._publish(call, decision.outcome, decision.outcome == "suppressed",
                          reason=decision.reason)
            if decision.outcome == "suppressed":
                return ToolResult(True, data={"suppressed": True, "reason": decision.reason})
            return ToolResult(False, error=f"refused: {decision.reason}")

        started = time.monotonic()
        result = self._transport.call_tool(tool, args)
        rows = None
        if result.ok and isinstance(result.data, dict) and isinstance(result.data.get("data"), list):
            rows = len(result.data["data"])
        self._publish(call, "called", result.ok, ms=int((time.monotonic() - started) * 1000),
                      rows=rows, result_hash=result_hash(result.data) if result.ok else None,
                      reason=result.error)
        return result

    def rest_get(self, path: str, params: dict | None = None) -> dict:
        call = ToolCall(f"GET {path}", dict(params or {}), Tier.READ)
        started = time.monotonic()
        body = self._transport.rest_get(path, params)
        self._publish(call, "called", True, ms=int((time.monotonic() - started) * 1000))
        return body
