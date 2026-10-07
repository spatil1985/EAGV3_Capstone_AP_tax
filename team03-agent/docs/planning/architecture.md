# architecture.md — the harness as built

> **Historical (2026-10-07).** The `harness/` package described here has been retired and removed; its
> parts were ported into `aptax/` (mapping in [`agent_design.md`](agent_design.md) §2a). Kept as a record; links
> to `harness/` files point into git history.

**Team 03 · Seat 03 (Payables & Tax) · as of 2026-10-03**

[`agent_design.md`](agent_design.md) is the design of record (its §2a maps this code
onto it); [`harness_plan.md`](harness_plan.md) is the earlier, superseded design. This
document describes **what exists in the code today**: every module, what it is for, who calls it, and when you
would change it. For the hands-on guide (commands, adding a playbook, test ideas) see
[`../../harness/README.md`](../../harness/README.md).

**Status:** the deterministic path is built and verified live: registry, policy
gateway, runner, state and reports, with **one live playbook, UC-12** (e-way bill
audit, India). The LLM loop, event polling and the `AgentMemory` store are not built
yet (see [What is not built](#what-is-not-built)).

---

## 1. Layout

```
team03-agent/
├── harness/                      reusable machinery — no use-case logic
│   ├── __main__.py               CLI + composition root  (py -3 -m harness …)
│   ├── core/                     what a run IS
│   │   ├── context.py            RunContext: tenant, locale, dates, constants (immutable)
│   │   ├── playbook.py           Playbook / Rule / RecordRule / Dataset base classes
│   │   ├── registry.py           Manifest loader + router (run | skip | spec | blocked)
│   │   └── runner.py             Runner: executes routed playbooks end to end
│   ├── access/                   how we REACH AgentSwitch
│   │   ├── transport.py          Live / Recording / Replay transports, ToolResult
│   │   └── gateway.py            ToolGateway: policy chain, write tiers, allowlist, dry-run
│   ├── tracking/                 what a run REMEMBERS and LOGS
│   │   ├── state.py              finding fingerprints, dedup stores
│   │   └── trace.py              EventBus, trace writer, call counter, anomaly log
│   └── output/                   what a run PRODUCES
│       └── report.py             Markdown / JSON renderers, escalation writer
├── scripts/                      deterministic helpers and use-case logic
│   ├── agentswitch_client.py     HTTP + JSON-RPC client (login, REST, MCP)
│   ├── fetch.py                  Fetcher: paged reads + field quarantine
│   ├── findings.py               Finding row — the shared output contract
│   ├── money.py                  Decimal money + ₹/$ formatting
│   ├── uc/uc12_eway_bill.py      UC-12 playbook (rules + fetch)
│   ├── invoice_matcher.py        legacy UC-05 matcher (used by existing tests)
│   └── tax_math.py               legacy tax reconciliation (used by existing tests)
├── playbooks/
│   ├── uc-12-eway-bill.md        manifest (YAML front matter) + SOP
│   ├── constants.yaml            statutory constants with their sources
│   └── duplicate_audit.md, tax_audit.md   legacy SOPs, no manifest (ignored by the registry)
└── runs/                         gitignored: per-run reports, traces, recordings, state
```

**Dependency direction:** `__main__` → `core` → `access` / `tracking` / `output`, and
`scripts/uc/*` → `harness.core.playbook`. Nothing in `harness/` imports a use case;
playbooks are found through their manifests.

---

## 2. One run, step by step

```
py -3 -m harness run --tenant in --playbook uc-12
│
├─ __main__.build_transport()        LiveTransport(AgentSwitchClient.from_env("AGENTSWITCH"))
│                                    [+ RecordingTransport if --record | ReplayTransport if --replay]
├─ RunContext.build(transport)       GET /api/auth/me + GET /api/accounting/locale
│                                    → tax_regime, currency, features, as_of, constants, run_id
├─ EventBus ← JsonlTraceWriter, CallCounter
├─ ToolGateway(transport, bus, dry_run=True)
├─ Runner.run(ctx, trigger)
│   ├─ Registry.route(ctx)           per manifest: status × regime × vertical × features × trigger
│   └─ for each "run" route:
│       ├─ Registry.instantiate()    import "scripts.uc.uc12_eway_bill:EWayBillAudit"
│       ├─ gateway.scoped(manifest.tools)        widen the read allowlist for this playbook
│       ├─ Playbook.run(ctx, Fetcher(gateway))
│       │    fetch()  → Fetcher.list("EWayBill") → gateway.call_tool → transport → MCP
│       │    evaluate() → Rule.evaluate() × 5     (pure, no I/O)
│       │    sort → context() → summary()
│       ├─ fingerprint(f) → FindingStore.is_new()  new vs already reported
│       ├─ AnomalyLog.record()       findings from platform-contradiction rules
│       └─ EscalationWriter.write()  → gateway → AgentEscalation.create (suppressed in dry-run)
└─ MarkdownReport / JsonReport       runs/<run_id>/report.md, report.json
```

---

## 3. Module reference

### `harness/__main__.py` — CLI and composition root
- **Does:** parses `run` / `routes`, and is the **only** place concrete classes are
  chosen and wired together (transport, gateway, store, renderers). Forces UTF-8 output
  so ₹ prints on Windows consoles.
- **Use:** `py -3 -m harness routes --tenant in` · `py -3 -m harness run --tenant in --playbook uc-12 [--commit] [--record DIR | --replay DIR] [--as-of YYYY-MM-DD]`
- **Touch it when:** adding a CLI flag, or swapping an implementation (e.g. an
  `AgentMemory` store).

### `harness/core/context.py` — `RunContext`
- **Does:** an immutable snapshot of the facts a run is about: tenant, `company_id`,
  roles, `tax_regime`, currency, locale `features`, `as_of`, `period`, `run_id`,
  `dry_run`, vertical, and the constants from `playbooks/constants.yaml`. Built only
  through `RunContext.build()` (Factory Method). Raises `ContextError` if the locale is
  unavailable: there is no fallback jurisdiction.
- **Use in a playbook:** `ctx.as_of`, `ctx.currency`, `ctx.tax_regime`,
  `ctx.constant("eway_bill_threshold_inr")`.
- **Also defines:** `ROOT` (the `team03-agent/` path) and `CONSTANTS_FILE`.

### `harness/core/playbook.py` — the base classes every use case extends
- **`Playbook`** (Template Method): `run()` is fixed (fetch → evaluate → sort →
  context → summary). Subclasses implement `fetch()` and `rules`, and may override
  `context()`, `summary()` and `sort_key()`. **Never override `run()`.**
- **`Rule`** (Strategy): one check, `evaluate(dataset, ctx) → Finding*`. Set
  `platform_contradiction = True` to send its findings to `anomalies.jsonl`.
- **`RecordRule`**: per-record Template Method; implement `applies()` and `finding()`.
- **`Dataset`**: named record sets plus cached indexes (`data.index("invoices", "id")`).
- **`PlaybookOutcome`**: findings, context dict, anomalies, summary.

### `harness/core/registry.py` — manifests and routing
- **Does:** loads every `playbooks/*.md` with YAML front matter into a `Manifest`.
  `route()` returns a `Route(action, reason)` per manifest: `run`, `skip` (wrong regime,
  vertical, missing locale feature, no matching trigger), `spec` or `blocked`.
  `instantiate()` builds the class named in `compute: module:Class` (Factory).
- **Touch it when:** adding a routing dimension (e.g. a new manifest field).

### `harness/core/runner.py` — `Runner` (Facade)
- **Does:** for each routed playbook: instantiate → scope the allowlist → run →
  fingerprint and dedupe → record anomalies → escalate → render reports. One
  playbook's exception is isolated in its `PlaybookRun.error`; the rest continue.
- **Returns:** `RunResult` (with `headline()`, which counts each document's exposure
  once) and the report paths.

### `harness/access/transport.py` — reaching AgentSwitch
- **`Transport`** protocol: `call_tool(name, args) → ToolResult` and `rest_get(path)`.
- **`LiveTransport`** (Adapter) over `AgentSwitchClient`; does the MCP handshake once
  and normalises the three MCP result shapes into `ToolResult(ok, data, error)`.
- **`RecordingTransport`** (Decorator): saves every response to a directory.
  **`ReplayTransport`** serves them back, so recorded runs replay offline and
  deterministically. Recordings contain live business data: keep them under `runs/`.

### `harness/access/gateway.py` — `ToolGateway` (Proxy + Chain of Responsibility)
- **Does:** every MCP call goes through it. It classifies the tool into a write tier
  (T0 read · T1 annotate · T2 workflow · T3 mutate), then runs the policy chain
  **before** touching the transport:
  `ProhibitedEntityPolicy` (SalarySlip, Contract, EsignDocument, CRM) →
  `WriteTierPolicy` (T3 always refused, T2 needs `--allow-workflow`) →
  `AllowlistPolicy` (curated reads plus the manifest's `tools`) →
  `DryRunPolicy` (T1/T2 suppressed unless `--commit`).
  Every call, refused or not, is published to the `EventBus`.
- **Use:** `gateway.call_tool("EWayBill.list", {...})`; `with gateway.scoped([...]):`.
- **Touch it when:** adding a policy (a new `Policy` subclass inserted in `policies`)
  or a tool to `BASE_READ_ALLOWLIST`.

### `harness/tracking/state.py` — "have we already reported this?"
- **Does:** `fingerprint(finding, period)` = hash of rule, entity, period and exposure
  bucket. A finding is *new* if unseen, or if its exposure moved bucket.
  `FindingStore` protocol with `LocalJsonStore` (`runs/state.json`, and
  `runs/state.dry-run.json` for dry runs so rehearsals never swallow real
  escalations) and `MemoryStore` (replays, tests).
- **Touch it when:** implementing the planned `AgentMemory`-backed store.

### `harness/tracking/trace.py` — observability (Observer)
- **`EventBus`** with subscribers: **`JsonlTraceWriter`** (`runs/<run_id>/trace.jsonl`:
  tool, args, tier, outcome, ms, rows, result hash; never credentials) and
  **`CallCounter`** (totals for the CLI summary).
- **`AnomalyLog`** (`runs/<run_id>/anomalies.jsonl`): platform values that contradict
  our recomputation. This is the bug-bounty feed; a human reviews entries before
  anything is filed.

### `harness/output/report.py` — what a run produces
- **`ReportRenderer`** (Strategy): `MarkdownReport` and `JsonReport` write
  `runs/<run_id>/report.md|json`. The first line is the one-sentence headline; the
  Markdown groups findings by rule.
- **`EscalationWriter`**: one `AgentEscalation.create` per playbook per run, built only
  from **new** findings, sent through the gateway (so dry-run suppresses it).

### `scripts/fetch.py` — `Fetcher` (Repository)
- **Does:** `list(entity, **filters)` pages `Entity.list` (limit 1000, offset) until
  done; `get(entity, id)`. Applies **field quarantine** at fetch time:
  `CreditNote.taxes` and `Tax.group_taxes` are stripped; `Bill.tds_amount` and
  `ApprovalRequest.is_overdue` are renamed `_suspect_*`; `Bill.match_status/detail`
  are stripped.
- **Rule:** filters are flat and single-valued (`{"itc_eligibility": "input"}`,
  booleans as `true`). There are no range filters, so ranges are client-side.

### `scripts/findings.py` — the shared output contract
- `Finding` (frozen dataclass) with the UC-01 §7 fields (`finding_type, rule,
  entity_type, entity_id, entity_ref, total_exposure, …, summary`) plus `severity` and
  free-form `details`. The runner stamps `run_id` and `fingerprint`; playbooks never
  do. `to_dict()` keeps amounts as exact decimal strings.

### `scripts/money.py`
- `money(x)` → `Decimal` at 2 dp, ROUND_HALF_UP. `fmt(amount, currency)` → `₹1,24,267.28`
  (lakh grouping) or `$124,267.28`. **No floats in amounts.**

### `scripts/agentswitch_client.py`
- Login (`login`, `from_env(prefix)`), `whoami`, `get_locale`, `rest_get`,
  `mcp_rpc`, `mcp_tools_call`. Shared with `tests/integration/`.

### `scripts/uc/uc12_eway_bill.py` — the first playbook
- `EWayBillAudit(Playbook)` with 5 rules: `EwbMissing`, `EwbNotReal`,
  `EwbExpiredInTransit`, `EwbPartBMissing`, `EwbValidityWrong`. `fetch()` reads
  EWayBill, receivable Invoice and DeliveryChallan. Spec:
  [`../usecases/IN/uc-12-eway-bill-coverage.md`](../usecases/IN/uc-12-eway-bill-coverage.md).

### Configuration files
| File | Purpose |
|---|---|
| `playbooks/<id>.md` | Manifest front matter: `id, title, status, tax_regimes, verticals, requires_features, triggers, compute, tools, escalate, spec`. Body: the SOP |
| `playbooks/constants.yaml` | `{name: {value, unit, source, verified}}`. Read via `ctx.constant()` |
| `.env` (from `.env.example`) | `AGENTSWITCH_*` (India, `--tenant in`) and `US_AGENTSWITCH_*` (Keystone, `--tenant us`) |

---

## 4. Outputs

| Path (all gitignored) | Written by | Contents |
|---|---|---|
| `runs/<run_id>/report.md` · `report.json` | `output/report.py` | Headline, per-playbook summary, context, findings |
| `runs/<run_id>/trace.jsonl` | `tracking/trace.py` | Every gateway call, including refused and suppressed ones |
| `runs/<run_id>/anomalies.jsonl` | `tracking/trace.py` | Platform-contradiction findings for bug review |
| `runs/state.json` · `state.dry-run.json` | `tracking/state.py` | Fingerprints of findings already reported |
| `runs/<dir>` from `--record` | `access/transport.py` | Raw responses for offline replay |

---

## 5. Extending

| To add… | Do this | Harness change? |
|---|---|---|
| a use case | manifest in `playbooks/`, constants in `constants.yaml`, `scripts/uc/<id>.py` with a `Playbook` subclass | **none** |
| a check to an existing use case | a new `Rule` / `RecordRule` in its `rules` list | none |
| a safety rule | a `Policy` subclass, inserted in `ToolGateway.policies` | `access/gateway.py` |
| an output format | a `ReportRenderer` subclass, added in `__main__` | `output/report.py` + one line |
| persistent dedupe | an `AgentMemory`-backed `FindingStore` | `tracking/state.py` + one line in `__main__` |
| the LLM loop | `harness/llm.py` (Protocol) + `harness/loop.py`, calling the same gateway, with each playbook exposed as a tool via `Runner` | new modules only |

## 6. Testing

Graded tests must be hand-written (harness_plan.md §8), so the code is shaped for
them: `Playbook.evaluate()` and every `Rule` are pure (build a `Dataset` from dicts),
`ToolGateway` is testable with a spy transport (assert it was never called for a
refused tool), and whole runs replay offline with `--record` / `--replay`. Verified on
2026-10-03 after the regrouping: the replay reproduces 367 findings exactly, refusals
make zero transport calls, and the existing suite passes (10 passed, 5 skipped).

## What is not built

From harness_plan.md: the LLM loop and `LLMGateway` (§4.1, §4.4) · untrusted-data
wrapping of model-facing results · event triggers with `updated_at` watermarks (no
`updated_since` filter exists, requested in
[`../submissions/requested_tools.md`](../submissions/requested_tools.md) T3.1; sorting by
`updated_at` descending works instead) · the
`AgentMemory` store · `scripts/vertical.py` (the vertical defaults to manufacturing) ·
re-read-before-write · the GitHub Actions cron · playbooks beyond UC-12.
