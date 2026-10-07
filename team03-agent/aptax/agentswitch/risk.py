"""Our own risk table (agent_design.md §4.10, G3).

The tier of a call comes from this table, never from the server's `risk` tag:
`endpoint.accounting.bill_match` is tagged WRITE but only reads (our filed N3), and
`VendorCredit.apply_to_bill` / `PaymentMade.create` exist and must never be called.

    T0 READ      *.list, *.get, read endpoints, allowlisted REST reads
    T1 ANNOTATE  AgentSession / AgentEscalation / AgentTodo writes
    T2 WORKFLOW  Bill.approval.submit (only after a human approval)
    T3 MUTATE    anything else — never sent
"""

from enum import IntEnum


class Tier(IntEnum):
    READ = 0
    ANNOTATE = 1
    WORKFLOW = 2
    MUTATE = 3


ANNOTATE_TOOLS = {
    "AgentSession.create", "AgentEscalation.create", "AgentEscalation.update",
    "AgentTodo.create", "AgentTodo.update",
    # Notification.create is not exposed on either tenant (2026-10-03); not listed.
}
WORKFLOW_TOOLS = {"Bill.approval.submit"}

# endpoint.* tools that only read, whatever their risk tag says. check_sla is read-only
# only with dry_run: true — policy.yaml enforces that argument.
READ_ENDPOINTS = {"endpoint.accounting.bill_match", "endpoint.approvals.check_sla"}

# REST allowlist (G2): (method, path) → purpose. POSTs here were verified not to persist.
REST_READS = {
    ("GET", "/api/auth/me"): "session identity",
    ("GET", "/api/accounting/locale"): "regime, features, not_yet_supported",
    ("POST", "/api/accounting/tax/compute"): "tax oracle (pure computation, verified)",
    ("GET", "/api/accounting/reports/sales-tax-liability"): "US-01 oracle",
    ("GET", "/api/cpa/reports/1099-summary"): "US-06 oracle",
    ("GET", "/api/accounting/indirect-tax/ledger-balance"): "UC-23 oracle",
    ("GET", "/api/accounting/indirect-tax/reconcile"): "UC-23 oracle",
    ("GET", "/api/accounting/reports/ap-aging"): "UC-42 / UC-04 cross-check",
    # POST /api/accounting/gst/reconcile-2b is deliberately absent until Q13 confirms
    # it does not persist.
}


def classify(tool: str) -> Tier:
    if tool in ANNOTATE_TOOLS:
        return Tier.ANNOTATE
    if tool in WORKFLOW_TOOLS:
        return Tier.WORKFLOW
    if tool in READ_ENDPOINTS or tool.endswith((".list", ".get")):
        return Tier.READ
    return Tier.MUTATE


def classify_rest(method: str, path: str) -> Tier:
    return Tier.READ if (method, path) in REST_READS else Tier.MUTATE
