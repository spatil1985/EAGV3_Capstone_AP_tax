"""Built-in and playbook capabilities for one run (agent_design.md §4.6, §4.8).

Read capabilities:
    as_context        tenant, regime, period, vertical, documented platform gaps
    as_query          a guarded read of one allowlisted entity: count | list | get
    load_playbook     a playbook's SOP text (S17 load_skill idea: loaded on demand)
    explain_use_case  a spec's question, verdict and status — for spec/blocked use cases
    get_findings      page through a playbook run's rows (G9)
Playbook capabilities: one per live, routable playbook manifest — generated, so adding a
use case never edits this file.
Terminal: submit_answer — the only way the agent loop finishes.

Every worker returns plain data; the loop shapes it, wraps free text as untrusted and
gives it an evidence id the final answer must cite.
"""

import re

from aptax.capabilities.registry import Arg, Capability, CapabilityError, Registry
from aptax.config import ROOT
from aptax.playbooks.manifest import MAX_SOP_CHARS
from aptax.runtime.shaping import PRIVATE_PREFIXES, shape_outcome, shape_record

QUERYABLE = (
    "Bill", "Invoice", "Party", "PaymentMade", "PaymentReceived", "CreditNote", "VendorCredit",
    "GSTReturn", "Item", "ApprovalRequest", "EWayBill", "DeliveryChallan", "PurchaseOrder", "Expense",
    "BankTransaction", "TaxNexus", "TaxJurisdiction", "ExemptionCertificate", "AccountingPeriod",
    "TransactionLock", "Location", "RecurringBill",
)
USECASE_DIR = ROOT / "docs" / "usecases"
SUBMIT_ANSWER = "submit_answer"

# Records are wide (a Bill has ~60 fields) and results are clipped to 30 keys, so rows
# put identifying and money fields first, and leave empty and nested values out unless
# the model asks for them by name.
PRIORITY_FIELDS = (
    "id", "bill_number", "invoice_number", "number", "name", "display_name", "status", "docstatus",
    "direction", "date", "due_date", "_vendor_id_display", "_customer_id_display", "_party_id_display",
    "vendor_id", "customer_id", "party_id", "currency_code", "grand_total", "total", "sub_total",
    "total_tax", "balance_due", "amount_paid", "approval_status", "itc_eligibility", "gst_treatment",
)
FIELD_NAME = re.compile(r"_?[a-z][a-z0-9_]{0,63}")


def project(record: dict, fields=None) -> dict:
    if not isinstance(record, dict):
        return record
    if fields:
        return {f: record.get(f) for f in fields if f in record}
    flat = {k: v for k, v in record.items() if v not in (None, "") and not isinstance(v, (list, dict))}
    ordered = {k: flat[k] for k in PRIORITY_FIELDS if k in flat}
    ordered.update((k, v) for k, v in flat.items() if k not in ordered)
    return ordered


def nested_fields(rows) -> list[str]:
    return sorted({k for r in rows if isinstance(r, dict) for k, v in r.items()
                   if isinstance(v, (list, dict)) and v and not k.startswith(PRIVATE_PREFIXES)})

SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "description": "The sub-question this section answers."},
        "evidence_ids": {"type": "array", "items": {"type": "string"},
                         "description": "Evidence ids (E1, E2, …) or finding ids this section relies on."},
        "narrative": {"type": "string", "description": "The answer. Every number must appear in the cited evidence."},
    },
    "required": ["question", "evidence_ids", "narrative"],
}


def _scalar_filters(filters: dict) -> dict:
    clean = {}
    for key, value in (filters or {}).items():
        if not re.fullmatch(r"[a-z_][a-z0-9_]{0,63}", str(key)):
            raise CapabilityError(f"filter name {key!r} is not a field name")
        if isinstance(value, (list, dict)):
            raise CapabilityError(f"filter {key!r} must be a single value (filters are flat, one value each)")
        clean[key] = value
    return clean


def _spec_file(ident: str):
    ident = ident.strip().lower()
    for sub in ("IN", "US"):
        for path in sorted((USECASE_DIR / sub).glob(f"{ident}-*.md")):
            return path
    return None


def explain_spec(ident: str) -> dict:
    path = _spec_file(ident)
    if not path:
        raise CapabilityError(f"no use-case spec {ident!r} (try UC-01…UC-44 or US-01…US-22)")
    text = path.read_text(encoding="utf-8")
    title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("# ")), path.stem)
    verdict = next((l.strip("* ").strip() for l in text.splitlines()
                    if "Verdict" in l and l.startswith("**")), "")
    m = re.search(r"## 1\.[^\n]*\n+(.*?)(?=\n## |\n---)", text, re.S)
    question = " ".join(l.strip()[1:].strip(" *\"") for l in (m.group(1).splitlines() if m else [])
                        if l.strip().startswith(">"))
    return {"id": ident.upper(), "title": title, "verdict": verdict, "question": question,
            "spec": str(path.relative_to(ROOT)).replace("\\", "/")}


def build_registry(*, ctx, gateway, fetcher, store, runner) -> Registry:
    manifests = runner.manifests
    routes = {r.manifest.id: r for r in runner.routes()}
    ids = tuple(sorted({m.id for m in manifests} | {m.capability for m in manifests}))

    def as_context(_args):
        # Rule values in force are included so a statutory number the answer quotes
        # (a threshold, a day count) is citable evidence.
        return {**ctx.summary(), "rules_in_force": ctx.constants}

    def as_query(args):
        entity, op, fields = args["entity"], args.get("op", "list"), args.get("fields")
        bad = [f for f in fields or () if not isinstance(f, str) or not FIELD_NAME.fullmatch(f)]
        if bad:
            raise CapabilityError(f"fields must be field names, got {bad}")
        if op == "get":
            if not args.get("id"):
                raise CapabilityError("as_query op=get needs an id")
            record = fetcher.get(entity, args["id"])
            out = {"entity": entity, "op": op, "record": shape_record(project(record, fields))}
            if not fields:
                out["nested_fields_omitted"] = nested_fields([record])
            return out
        filters = _scalar_filters(args.get("filters") or {})
        limit = 1 if op == "count" else args.get("limit", 20)
        rows, total = fetcher.page(entity, limit=limit, **filters)
        out = {"entity": entity, "op": op, "filters": filters, "total": total}
        if op == "list":
            out.update(returned=len(rows), truncated=(total or 0) > len(rows),
                       rows=[shape_record(project(r, fields)) for r in rows])
            if not fields:
                out["nested_fields_omitted"] = nested_fields(rows)
        return out

    def load_playbook(args):
        m = runner.get(args["id"])
        r = routes.get(m.id)
        return {"id": m.id, "title": m.title, "status": m.status, "route": r.action if r else None,
                "route_reason": r.reason if r else None, "questions": list(m.questions), "sop": m.sop()}

    def explain_use_case(args):
        return explain_spec(args["id"])

    def get_findings(args):
        total, rows = store.page_run_findings(args["run_ref"], playbook=args.get("playbook"),
                                              rule=args.get("rule"), offset=args.get("offset", 0),
                                              limit=args.get("limit", 20))
        return {"run_ref": args["run_ref"], "total": total, "offset": args.get("offset", 0),
                "rows": [shape_record({k: r.get(k) for k in ("fingerprint", "rule", "entity_type", "entity_ref",
                                                             "counterparty_name", "total_exposure", "currency",
                                                             "summary")}) for r in rows]}

    caps = [
        Capability("as_context", "The tenant, tax regime (gst or sales_use_tax), currency, period, "
                   "vertical and the platform's own documented gaps. Call this first.", "read", as_context),
        Capability("as_query", "Read-only query of ONE allowlisted AgentSwitch entity. op=count returns the "
                   "server total for flat filters (e.g. {\"status\": \"open\"}); op=list returns up to 50 "
                   "rows; op=get returns one record by id. Rows show non-empty scalar fields, key fields "
                   "first; name fields to see others, including nested ones such as items or taxes. "
                   "Prohibited entities cannot be queried.",
                   "read", as_query, args={
                       "entity": Arg("string", "Entity name.", choices=QUERYABLE),
                       "op": Arg("string", "count | list | get", required=False, choices=("count", "list", "get")),
                       "filters": Arg("object", "Flat field=value filters, one value each.", required=False),
                       "id": Arg("string", "Record id for op=get.", required=False, maximum=64),
                       "limit": Arg("integer", "Rows for op=list (1-50).", required=False, minimum=1, maximum=50),
                       "fields": Arg("array", "Only these fields (max 20).", required=False,
                                     items={"type": "string"}, maximum=20)}),
        Capability("load_playbook", "Load the full procedure (SOP) of one playbook before relying on it.",
                   "read", load_playbook, args={"id": Arg("string", "Playbook id or capability name.", choices=ids)},
                   result_chars=MAX_SOP_CHARS),
        Capability("explain_use_case", "Explain a use case by id (UC-01…UC-44, US-01…US-22): its question, "
                   "verdict and status. Use for use cases that are spec-only or blocked.", "read",
                   explain_use_case, args={"id": Arg("string", "Use-case id, e.g. UC-36.", maximum=8)}),
        Capability("get_findings", "Page through the rows of an earlier playbook result in this run.",
                   "read", get_findings, args={
                       "run_ref": Arg("string", "run_ref from a playbook result.", maximum=80),
                       "playbook": Arg("string", "Playbook id filter.", required=False, maximum=16),
                       "rule": Arg("string", "Rule filter.", required=False, maximum=64),
                       "offset": Arg("integer", "Offset.", required=False, minimum=0, maximum=100000),
                       "limit": Arg("integer", "Rows (1-20).", required=False, minimum=1, maximum=20)}),
    ]

    for m in manifests:
        r = routes.get(m.id)
        if not r or r.action != "run" or not m.compute:
            continue

        def run_playbook(_args, manifest=m):
            run = runner.run_one(manifest, escalate=False)
            if run.error:
                raise RuntimeError(run.error)
            if run.route.action != "run":
                return {"playbook": manifest.id, "status": run.route.action, "reason": run.route.reason}
            return shape_outcome(manifest, run.outcome, run_ref=ctx.run_id)

        caps.append(Capability(m.capability, m.description, "playbook", run_playbook,
                               tax_regimes=m.tax_regimes, verticals=m.requires.verticals,
                               requires_tools=m.requires.tools))

    caps.append(Capability(
        SUBMIT_ANSWER, "Finish with the final answer. Each section answers one sub-question and cites the "
        "evidence ids its numbers come from. This is the only way to finish.", "terminal", None,
        args={"sections": Arg("array", "One section per sub-question.", items=SECTION_SCHEMA, maximum=8),
              "caveats": Arg("array", "Limits the reader must know.", required=False,
                             items={"type": "string"}, maximum=8)}))
    return Registry(caps)


def playbook_index(runner) -> str:
    """One line per playbook for the system prompt; full SOPs load on demand."""
    lines = []
    for r in runner.routes():
        m = r.manifest
        status = "available" if r.action == "run" else f"{r.action}: {r.reason}"
        q = m.questions[0] if m.questions else m.title
        lines.append(f"- {m.capability} ({m.id}) — {q} [{status}]")
    return "\n".join(lines) or "- (no playbooks)"
