"""Gateway — the policy layer every AgentSwitch call passes through (agent_design.md §4.10).

Pattern: **Proxy**. It has the transport's shape (`call_tool`, `rest`), so playbooks and
the fetcher cannot tell they are talking to a guard. For each call it:

1. classifies the tier from our own risk table (risk.py), never the server's tag;
2. asks the declarative policy (policy.py / config/policy.yaml) — refusals happen
   **before** the transport is touched, so a refused call costs zero MCP traffic;
3. suppresses allowed T1/T2 writes in dry-run, recording what would have been sent;
4. journals the call (append-only) with outcome, verdict, latency, rows and a result hash.

Writes carry an `effect` label (escalate, add_todo, request_approval, hold_for_review);
the policy condition `subscription_allows` is true only if the run's subscription lists
that effect. Authority comes from config, never from the data being processed.
"""

import hashlib
import json
import threading
import time
from collections import Counter
from contextlib import contextmanager

from aptax.agentswitch.policy import CallFacts, PolicyEngine
from aptax.agentswitch.risk import Tier, classify, classify_rest
from aptax.agentswitch.transport import ToolResult

# Read tools the agent may call (T0). Playbook manifests widen it per run (`scoped`).
BASE_READ_ALLOWLIST = frozenset({
    "Bill.list", "Bill.get", "Invoice.list", "Invoice.get", "Party.list", "Party.get",
    "PaymentMade.list", "PaymentMade.get", "PaymentReceived.list", "CreditNote.list", "CreditNote.get",
    "VendorCredit.list", "VendorCredit.get", "GSTReturn.list", "GSTReturn.get", "Item.list", "Item.get",
    "ApprovalRequest.list", "ApprovalRequest.get", "ApprovalLog.list", "EWayBill.list", "EWayBill.get",
    "DeliveryChallan.list", "PurchaseOrder.list", "PurchaseOrder.get", "RecurringBill.list",
    "RetainerInvoice.list", "Expense.list", "Expense.get", "BankTransaction.list", "BankAccount.list",
    "TaxNexus.list", "TaxJurisdiction.list", "ExemptionCertificate.list", "TaxExemption.list",
    "Company.list", "OrgProfile.list", "Location.list", "AccountingPeriod.list", "TransactionLock.list",
    "DirectTaxPreferences.list", "EInvoicingPreferences.list", "GeneralPreferences.list",
    "CustomerVendorPreferences.list", "MSMEPreferences.list", "PartyRelationship.list",
    "AgentEscalation.list", "AgentEscalation.get", "AgentTodo.list", "AgentSession.list",
    "endpoint.accounting.bill_match", "endpoint.approvals.check_sla",
})


class GatewayRefused(PermissionError):
    """A REST call the policy refused (MCP refusals come back as a failed ToolResult)."""


def result_hash(data) -> str:
    return hashlib.sha1(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:12]


class Gateway:
    def __init__(self, transport, store, policy: PolicyEngine, *, run_id: str, tenant: str,
                 dry_run: bool = True, allowed_effects=frozenset(), allowlist=None):
        self._transport = transport
        self._store = store
        self.policy = policy
        self.run_id = run_id
        self.tenant = tenant
        self.dry_run = dry_run
        self.allowed_effects = frozenset(allowed_effects)
        self._allowlist = frozenset(allowlist or BASE_READ_ALLOWLIST)
        self._scoped: Counter = Counter()      # tools widened by playbooks running right now
        self._lock = threading.Lock()
        self._seq = 0
        self.stats = {"called": 0, "refused": 0, "suppressed": 0, "failed": 0}
        self._available: set[str] | None = None

    # -- allowlist and tool availability -------------------------------------------

    @contextmanager
    def scoped(self, extra_tools):
        """Widen the read allowlist while one playbook runs.

        Reference-counted: the agent loop runs playbooks concurrently, and one playbook
        finishing must not narrow the allowlist under another that is still running.
        """
        tools = list(extra_tools or ())
        with self._lock:
            self._scoped.update(tools)
        try:
            yield self
        finally:
            with self._lock:
                self._scoped.subtract(tools)
                self._scoped += Counter()      # drop tools no running playbook needs

    def available_tools(self) -> set[str]:
        """Tool names the live tools/list exposes to our role (cached per run)."""
        if self._available is None:
            try:
                self._available = {t.get("name") for t in self._transport.tools_list() if t.get("name")}
            except Exception:  # noqa: BLE001 — unknown availability must not crash a run
                self._available = set()
        return self._available

    # -- calls -------------------------------------------------------------------------

    def _journal(self, tool, tier, args, outcome, ok, **extra) -> None:
        with self._lock:
            self._seq += 1
            seq = self._seq
            self.stats[outcome if outcome in self.stats else ("called" if ok else "failed")] += 1
            if outcome == "called" and not ok:
                self.stats["failed"] += 1
        self._store.journal(self.run_id, "tool_call", {
            "seq": seq, "tool": tool, "tier": tier.name, "args": args, "outcome": outcome, "ok": ok,
            **{k: v for k, v in extra.items() if v is not None}})

    def _facts(self, tool, tier, args, effect, approval_granted) -> CallFacts:
        with self._lock:
            allowlisted = tool in self._allowlist or self._scoped[tool] > 0
        return CallFacts(tool=tool, tier=tier, args=dict(args), allowlisted=allowlisted,
                         subscription_allows=bool(effect) and effect in self.allowed_effects,
                         approval_granted=approval_granted)

    def call_tool(self, tool: str, args: dict, *, effect: str | None = None,
                  approval_granted: bool = False) -> ToolResult:
        tier = classify(tool)
        verdict = self.policy.evaluate(self._facts(tool, tier, args, effect, approval_granted))
        if not verdict.allowed:
            self._journal(tool, tier, args, "refused", False, reason=verdict.reason, effect=effect)
            return ToolResult(False, error=f"refused: {verdict.reason}")
        if self.dry_run and tier in (Tier.ANNOTATE, Tier.WORKFLOW):
            self._journal(tool, tier, args, "suppressed", True, reason="dry-run", effect=effect)
            return ToolResult(True, data={"suppressed": True, "reason": "dry-run: write recorded, not sent"})

        started = time.monotonic()
        result = self._transport.call_tool(tool, args)
        rows = None
        if result.ok and isinstance(result.data, dict) and isinstance(result.data.get("data"), list):
            rows = len(result.data["data"])
        self._journal(tool, tier, args, "called", result.ok, ms=int((time.monotonic() - started) * 1000),
                      rows=rows, result_hash=result_hash(result.data) if result.ok else None,
                      error=result.error, effect=effect)
        return result

    def rest(self, method: str, path: str, params: dict | None = None, body: dict | None = None):
        name = f"{method} {path}"
        tier = classify_rest(method, path)
        args = {"params": params or {}, "body": body or {}}
        verdict = self.policy.evaluate(CallFacts(tool=name, tier=tier, args=args,
                                                 allowlisted=tier is Tier.READ))
        if not verdict.allowed:
            self._journal(name, tier, args, "refused", False, reason=verdict.reason)
            raise GatewayRefused(f"{name} refused: {verdict.reason}")
        started = time.monotonic()
        try:
            response = self._transport.rest(method, path, params, body)
        except Exception as exc:
            self._journal(name, tier, args, "called", False, error=f"{type(exc).__name__}: {exc}",
                          ms=int((time.monotonic() - started) * 1000))
            raise
        self._journal(name, tier, args, "called", True, ms=int((time.monotonic() - started) * 1000),
                      result_hash=result_hash(response))
        return response
