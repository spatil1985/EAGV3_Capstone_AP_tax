# Harness — how it fits together, and how to add a playbook

Deterministic path of [`docs/harness_plan.md`](../docs/harness_plan.md): registry,
policy gateway, runner, state and reports, with **UC-12 (e-way bill audit)** as the
first live playbook. The LLM loop (plan §4.4) plugs in on top of the same gateway and
runner later; nothing here changes when it does.

```
py -3 -m harness routes --tenant in                     # what would run, and why not
py -3 -m harness run --tenant in --playbook uc-12       # dry-run: no writes sent
py -3 -m harness run --tenant in --trigger scheduled --cadence daily
py -3 -m harness run --tenant in --playbook uc-12 --record runs/rec-uc12
py -3 -m harness run --tenant in --playbook uc-12 --replay runs/rec-uc12 --as-of 2026-09-30
```

Credentials come from the environment: `AGENTSWITCH_*` for `--tenant in`,
`US_AGENTSWITCH_*` for `--tenant us`. Output goes to `runs/<run_id>/`, which is
gitignored: `report.md`, `report.json`, `trace.jsonl`, `anomalies.jsonl`.

---

## Flow

```
CLI (__main__.py: composition root)
  │ builds
  ▼
RunContext.build()  ── whoami + locale ──▶  regime, currency, features, as_of, constants
  │
Runner.run()  (Facade)
  ├─ Registry.route()   status × regime × vertical × features × trigger → run | skip | spec | blocked
  ├─ Registry.instantiate()  manifest "compute: module:Class" → Playbook      (Factory)
  ├─ gateway.scoped(manifest.tools)
  │     Playbook.run()   fetch → evaluate(rules) → sort → context → summary    (Template Method)
  │        ├─ fetch:     Fetcher.list()  paging + quarantine                     (Repository)
  │        │               └─ ToolGateway.call_tool()  policy chain              (Proxy + Chain of Responsibility)
  │        │                     └─ Transport  Live | Recording | Replay         (Adapter + Decorator)
  │        └─ evaluate:  Rule.evaluate() × N  — pure, no I/O                     (Strategy)
  ├─ fingerprint → FindingStore.is_new()  (dedupe across runs)
  ├─ AnomalyLog.record()  for platform-contradiction rules
  ├─ EscalationWriter  → gateway (T1; suppressed in dry-run)
  └─ ReportRenderer × N  Markdown | JSON                                         (Strategy)
Every gateway call → EventBus → JsonlTraceWriter, CallCounter                    (Observer)
```

## Pattern map

| Pattern | Where | What it buys |
|---|---|---|
| **Template Method** | `Playbook.run()`, `RecordRule.evaluate()` | Every use case runs the same skeleton; authors fill hooks only |
| **Strategy** | `Rule` subclasses; `ReportRenderer` subclasses | Checks and output formats are independent, reorderable, reusable |
| **Registry + Factory** | `registry.py`: YAML manifests, `instantiate()` | New use case = new files; the runner never imports use-case code |
| **Proxy** | `ToolGateway` | Same interface as a transport, but every call is policed and traced |
| **Chain of Responsibility** | `gateway.Policy` chain | Refusal / write-tier / allowlist / dry-run rules added one class at a time |
| **Repository** | `scripts/fetch.py` `Fetcher` | Paging and field quarantine in one place; no playbook sees raw MCP |
| **Adapter** | `LiveTransport` | Existing `AgentSwitchClient` behind a two-method interface |
| **Decorator** | `RecordingTransport` | Record any live run; `ReplayTransport` serves it offline |
| **Observer** | `EventBus` → trace writer, counter | New sinks (cost, metrics) without touching the gateway |
| **Factory Method** | `RunContext.build()` | A context is complete and immutable, or the run doesn't start |
| **Facade** | `Runner` | CLI, cron and (later) the LLM loop all run playbooks the same way |

---

## Adding a playbook (the whole job for UC-01, UC-05, UC-13, …)

**1. Manifest** — `playbooks/uc-NN-<name>.md`, front matter plus SOP text:

```yaml
---
id: uc-04
title: MSME 45-day exposure
questions: ["Which small suppliers are we about to pay late?"]
owner: sudip
status: live                 # live | spec | blocked
blocked_by: null             # e.g. F18
tax_regimes: [gst]           # or [all]
verticals: [all]
requires_features: [msme_45_day]   # locale.features flags that must be true
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.uc04_msme:MsmeExposure
tools: [Party.list, Bill.list]       # added to the read allowlist for this run only
escalate: new_findings               # or never
spec: docs/usecases/uc-04-msme-45-day-exposure.md
---
```

**2. Constants** — add any statutory number to `playbooks/constants.yaml` with its
source. Read it with `ctx.constant("msme_payment_days")`, and never hardcode it.

**3. Code** — `scripts/uc/uc04_msme.py`:

```python
from harness.playbook import Dataset, Playbook, RecordRule
from scripts.findings import Finding
from scripts.money import money

class MsmePastDue(RecordRule):          # Strategy + per-record Template Method
    id, severity, source = "msme_past_45", 80, "bills"

    def applies(self, bill, data, ctx):
        vendor = data.index("parties", "id").get(bill["vendor_id"], {})
        return vendor.get("is_msme") and money(bill["balance_due"]) > 0 and ...

    def finding(self, bill, data, ctx):
        return Finding(finding_type="msme_45_day_exposure", rule=self.id, ...)

class MsmeExposure(Playbook):
    rules = property(lambda self: [MsmePastDue()])

    def fetch(self, ctx, fetcher):            # the only I/O
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party", is_msme=True))
```

Override `context()` and `summary()` for a better report, and `sort_key()` if the
spec orders findings differently. **Never override `run()`.** Set
`platform_contradiction = True` on a rule when its findings mean the platform's own
data disagrees with itself; those findings also go to `anomalies.jsonl` for bug review.

**4. Check it:** `py -3 -m harness routes --tenant in`, then
`py -3 -m harness run --tenant in --playbook uc-04`.

No harness file changes. If a playbook needs one, raise it with the team: it means the
harness is missing a hook.

---

## Testing — hand-written only

Graded tests must be written by the team (harness_plan.md §8), so **none are included
here**. The structure is built to make them short:

- **Rules are pure.** Build `Dataset(ewb=[{...}, {...}])` from a few dicts and a
  context, call `EWayBillAudit().evaluate(data, ctx)`, and assert on `f.rule` and
  `f.entity_ref`. No network, no mocks. A context for tests can be built directly:
  `RunContext(run_id="t", tenant="in", as_of=date(2026, 9, 30), constants={...}, ...)`.
- **Policies are pure.** Construct `ToolGateway(spy_transport, EventBus(), "t")`, call
  a prohibited or T3 tool, and assert that the spy transport was never called.
- **Whole runs replay offline:** `--record` once, then `--replay` with a fixed
  `--as-of`, and the output is identical.

Predicates worth writing for UC-12, from its spec §9:

- a `draft` invoice above the threshold is *not* `ewb_missing`;
- 217.81 km gives 2 days of validity, so no `ewb_validity_wrong`;
- an `active` EWB with no number yields `ewb_not_real`;
- `EWayBill.list` still being allowed after `gateway.scoped()` exits;
- the second run reporting 0 new.

---

## Verified on 2026-09-30

| Check | Result |
|---|---|
| Live run, India, dry-run | 367 findings over 3 MCP calls: 167 `ewb_missing`, 80 `ewb_not_real`, 68 `ewb_expired_in_transit`, 52 `ewb_part_b_missing`, 0 `ewb_validity_wrong`; ₹14.18 Cr of consignments (each document counted once). The EWB counts match the independent 30 Sep verification ([`../docs/bugs_to_file_2026-09-30.md`](../docs/bugs_to_file_2026-09-30.md) N13) |
| Second run | 0 new; no escalation attempted |
| Replay, offline | Identical result |
| Keystone (US) | Skipped: `tax_regime sales_use_tax not in ['gst']`, 0 MCP calls |
| Policy chain | SalarySlip, `Bill.update`, `Bill.approval.submit` and non-allowlisted tools refused before the transport; escalation suppressed in dry-run |

## Differences from harness_plan.md (deliberate)

- **Bill/Invoice `taxes[]` is not quarantined.** It is the reliable tax source there
  (docs/usecases/README.md, "Correction 2026-09-30"). Only `CreditNote.taxes[]` is
  stripped.
- **The CLI is `python -m harness`, and `run_agent.py` is untouched.** Plan §9 moves
  the LLM loop out of `run_agent.py` in Phase 1, which is Geetha's gateway work.
  Wiring `run_agent.py` to this CLI is a one-line change once that lands.
- **`constants.yaml` holds UC-12's constants only.** The owner (Sudip) adds the rest.

## Not built yet (plan phases 0–3)

The LLM loop and `LLMGateway` (§4.1, §4.4) · untrusted-data wrapping for model-facing
results (§4.3) · event-trigger polling with watermarks (§4.7; needs the
`updated_since` filter requested in `docs/requested_tools.md` T3.1) · an
`AgentMemory`-backed `FindingStore` (open question Q6) · `scripts/vertical.py`
(the vertical defaults to manufacturing and the report says so) · re-read-before-write
for T1/T2 · the GitHub Actions cron.

## Open question for UC-12's owner

`ewb_missing` flags every non-draft outward document ever raised, including paid
invoices from 2025. The spec's question is "moving *right now*". Should Part B only
look back N days (a new constant), with older gaps reported as a historical
compliance count? Each finding carries `details.days_since_document`, so either
choice is a small change.
