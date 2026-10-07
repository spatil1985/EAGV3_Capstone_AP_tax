# CURRENT_STATUS.md — read this first

**Team 03 · Seat 03 (Ledger — Payables & Tax) on AgentSwitch · status as of 2026-10-03**

This is the onboarding brief for a teammate, or a teammate's Claude, opening this repo
cold. It says what the project is, where everything lives, what is true on the live
platform today, and the rules we learned the hard way. Facts marked *(live)* were
re-checked against both tenants on 2026-10-03. Earlier verification logs
(20–22 Sep) are in git history: `git log -p -- team03-agent/CURRENT_STATUS.md`.

---

## 0. For Claude on a new machine — ground rules

1. **Read in this order:** this file → [`../README.md`](../README.md) (mission and
   grading) → [`docs/README.md`](docs/README.md) (doc map) →
   [`docs/planning/agent_design.md`](docs/planning/agent_design.md) (design of record, implemented in `aptax/`)
   → the use case you're working on in [`docs/usecases/`](docs/usecases/README.md).
2. **The ledger is live and shared** with Teams 01 and 02. Never write to it unless the
   user explicitly asks. The agent (`aptax`) defaults to **dry-run**, and T3 writes (ledger
   mutations) are refused in code.
3. **Never commit credentials.** They live in `.env` and
   `postman/*.postman_environment.json`, both gitignored. Never echo passwords.
4. **Graded tests must be hand-written by a human.** LLM-generated tests score 0. Do
   not add files under `tests/` on your own initiative; propose predicates instead.
5. **Bugs score, features don't** (100 points per verified bug; feature requests went
   into one unscheduled card). Before filing anything, check the **class bug board**
   (§4.3) as well as `bug-report/mine` — they disagree (see F18 in §4.3).
6. **Verify before claiming.** Several "bugs" we nearly filed turned out to be by design
   or seed data (§6). Re-check live data and the platform's own oracle first.

---

## 1. The project in one paragraph

Build an agent that answers, live and against a real shared ledger, *"What is our tax
liability this period, what is unclaimed, and is any vendor being paid twice?"* for
two companies in two jurisdictions, branching only on `GET /api/accounting/locale`,
never on company name. It uses a hand-rolled loop with no agent frameworks (capstone
rule). Score = 10 × hand-written tests + 100 × verified platform bugs.

## 2. Setup on a new machine

```
cd team03-agent
cp .env.example .env            # fill AGENTSWITCH_* (India) and US_AGENTSWITCH_* (US)
py -3 -m pip install -r requirements.txt     # requests, pytest, pyyaml
py -3 -m pytest -q                            # expect 10 passed, 5 skipped (live tests skip without creds)
py -3 -m aptax routes --tenant in             # reads AGENTSWITCH_* from the environment or .env
py -3 -m aptax run --tenant in --playbook uc-12          # dry-run; writes runs/<run_id>/
py -3 -m aptax --help                         # call, ask (needs APTAX_LLM), policy, journal, serve, kill
```

On this Windows machine Python is `py -3` (3.14); `python` is not on PATH. Postman
users: import `postman/AgentSwitch.postman_collection.json` plus a filled-in copy of
`AgentSwitch.postman_environment.example.json` (see `postman/README.md`).

## 3. Repo map

| Path | What |
|---|---|
| `aptax/` | The agent (agent_design.md §7): `agentswitch/` (transport, policy gateway, risk tiers, fetch + quarantine), `capabilities/` (registry, built-ins), `runtime/` (agent loop, evidence check, runner, outbox, render), `triggers/` (envelope, subscriptions, governor), `playbooks/` (manifests, base classes), `store/` (SQLite), `llm/` (contract; the gateway plugs in via `APTAX_LLM`), `api.py`, `cli.py`. The earlier `harness/` was retired on 2026-10-07 (git history keeps it) |
| `config/` | `policy.yaml` (tool policy, default deny), `charter.md` (the agent's corrected charter) |
| `scripts/` | Client, `findings.py` (output contract), `money.py`, `uc/` (one module per use case; UC-12 so far). `invoice_matcher.py` and `tax_math.py` are legacy, used by existing tests |
| `playbooks/` | Use-case manifests (`uc-12-eway-bill.md`) and `constants.yaml`. `duplicate_audit.md` / `tax_audit.md` are legacy SOPs (no manifest), to be replaced by UC-05 and period-liability playbooks |
| `docs/planning/` | `spec.md` (22 use cases), `assignment.md` (workstreams), `agent_design.md` (design of record), `harness_plan.md` (superseded), `architecture.md` (the retired harness, historical) |
| `docs/usecases/` | `IN/` UC-01…22 and `US/` US-01…10, each with live evidence |
| `docs/submissions/` | Bugs and feature requests: `agentswitch_submissions.md` (master, tallied with the board), `submission_tracker.md`, `requested_tools.md`, `bugs_to_file_2026-09-30.md` |
| `docs/gapreports/` | Competitor analyses (RazorpayX, Clear, Mysa, overall) |
| `docs/platform/` | MCP tool inventories (IN/US), UI screen inventory, screen-to-API mapping |
| `SKILL.md`, `DESIGN.md` | Agent charter (loaded by `run_agent.py`); design notes. `SKILL.md` still needs the corrections in §8 |
| `runs/` | Gitignored run output: reports, traces, anomalies, recordings, dedup state |

## 4. Where things stand (2026-10-03)

### 4.1 Use cases
- **India:** 22 specs (UC-01…22), grouped into workstreams A/B/C per
  `assignment.md`, each with a §11 of live evidence.
- **US:** 10 specs (US-01…10), with a full IN→US mapping in
  [`docs/usecases/US/README.md`](docs/usecases/US/README.md). Highlights: our liability
  recompute matches the platform report to the cent ($226,488.27 YTD); no use tax is
  accrued on any purchase; 36 Ohio invoices charge Stark County tax to customers
  outside the county (seed data).

### 4.2 Harness
- **Built and verified live:** the deterministic path (registry → gateway → runner →
  state → reports) and **one live playbook, UC-12** (e-way bill audit). On India
  (2026-09-30): 367 findings from 3 MCP calls; a second run reports 0 new; replay is
  identical; on US it is skipped by locale with 0 MCP calls.
- **Not built:** the LLM loop (LLM gateway), event polling, the `AgentMemory`
  store, vertical detection, cron, and every playbook except UC-12. Next playbooks
  per the plan: UC-05 (duplicates), UC-01 (Rule 37), period liability IN + US.

### 4.3 Bug bounty — tallied with the class bug board
The board is a Claude artifact (`claude.ai/artifact/6LvLawFFUXGoRHUQKbPg9h`). Its rows
are embedded in the page HTML, so it can be parsed. **Team 3 has 21 board rows:**
8 Live on server · 5 Fixed (ships in next release) · 5 In review · 3 To do. The full
mapping, with our ids and board ids, is in
[`docs/submissions/agentswitch_submissions.md` §A](docs/submissions/agentswitch_submissions.md#a--filed--tallied-with-the-class-bug-board-2026-10-03).

**Do next:**
1. **File N14–N16** (texts in §C.1 of that file): the US
   `indirect-tax/determinations` endpoint returns HTTP 500 for every document; exempt
   rows labelled "state" on a county jurisdiction; the liability report drops
   `liability_account_id`.
2. **Answer the open questions on N414–N418** (§A.1). Triage asks us for
   "authoritative records and finance approval" to correct historical documents. Honest
   answer: it's seed data and we have none; suggest voiding the documents instead.
3. **B5** (journal voucher renders ₹0.00) still needs reproduction before filing.

**Lesson:** F18 (Rule 42/43 apportionment) is missing from `bug-report/mine` and its
id returns 404, **but it is on the board as N273**. We nearly re-filed a duplicate.
Always check the board.

## 5. Platform facts *(live, 2026-10-03)*

| | India | US |
|---|---|---|
| Company | Suryodaya Precision Works Pvt. Ltd. `5cbe5a55-af74-4363-a436-f5350593114c` | Keystone Precision Works LLC `c1e47d8d-b849-4187-9a32-4103d3dece4a` |
| Base URL | `https://agentswitch.theschoolofai.in` | `https://class.agentswitch.theschoolofai.in` |
| Locale | `gst`, Ind AS, INR, FY Apr–Mar (FY 2026-27) | `sales_use_tax`, US GAAP, USD, FY = calendar 2026 |
| Features on | gst_returns, gst_ims, eway_bill, msme_45_day, tds_tcs | sales_tax_jurisdictions, sales_tax_nexus, exemption_certificates, form_1099, lifo_permitted |
| MCP tools | 508 | 500 |
| Records | 281 Bill · 487 Invoice · 230 Party · 176 ApprovalRequest · 100 EWayBill · 25 CreditNote · 1,142 JournalEntry · 12,026 GL entries | 101 Bill · 158 Invoice · 120 Party · 123 ApprovalRequest · 0 CreditNote · 296 JournalEntry · 2,775 GL entries |

- **Identity (both):** `team03@theschoolofai.in`, role `finance_user`, roles
  `finance_user, user, agent_user, sales_viewer`, apps
  `accounting, agent, crm, approvals` (F6 granted).
- **Read-only for us:** `JournalEntry`, `GLEntry`, `Payment`. Nothing can be *posted*.
- **Entity model:** AP is both `Bill` and `Invoice(direction=payable)` (why both exist
  is open). Vendors and customers are `Party` (no `Vendor` entity). There is no
  `TaxLine` entity. Document `status` is a flow state, and there is no `hold_payment`
  field. MSME fields live on `Party`. US 1099 fields (`tin`, `w9_on_file`,
  `form_1099_box`, `backup_withholding`) are also on `Party`.
- **Prohibited (absent from `tools/list`):** SalarySlip, Contract, EsignDocument. CRM is
  readable through `sales_viewer`, but the agent's policy denies it.

## 6. Data-trust rules — what we learned

| Rule | Why |
|---|---|
| **Tax source is per document.** On Bill/Invoice use document-level `taxes[]` where it reconciles to `total_tax`; else item-level lines that pass validity; else emit `data_quality` | `taxes[]` reconciles on 401/401 manual invoices and 63/64 bills, where lines carry no tax. Recurring-generated invoices are the reverse (N10/N415). The old rule "item-level only" read real GST as ₹0 |
| **`CreditNote.taxes[]` — never** | N128 (fixed going forward; historical rows remain) |
| **Recompute, don't trust:** `Bill.tds_amount`, `ApprovalRequest.is_overdue`, `Bill.match_status` | N7, N1/N8 (now fixed in R7), N2 (fixed, next release). `scripts/fetch.py` quarantines these at fetch time |
| **Expect seed data** | Clusters like 213 bills dated 2026-09, dozens created within seconds on 2026-09-12 17:19, one seeding user (`e30b0c70…`) creating US invoices. Before calling anything a platform bug, check whether the platform's own engine produces it (`POST /api/accounting/tax/compute`) |
| **Use the platform's oracles** | `tax/compute` (arithmetic), `endpoint.approvals.check_sla {"dry_run":true}`, `endpoint.accounting.bill_match`, US `GET /api/accounting/reports/sales-tax-liability`, US `GET /api/cpa/reports/1099-summary` |

## 7. Working with the API — conventions and gotchas

- **MCP:** `POST /api/mcp`, JSON-RPC 2.0. Do the handshake once (`initialize` →
  `notifications/initialized`). The `tools/call` result is in
  `result.content[0].text` (a JSON string); errors arrive as a JSON-RPC `error`
  (`-32602` for bad arguments) or as `result.isError`.
- **List filters are flat, single-valued and strictly typed:**
  `{"itc_eligibility":"input"}` works, an array does not; booleans must be `true`, not
  `1`. `limit` max 1000. There are **no range or `updated_since` filters**, so do
  ranges client-side (requested as T3.1).
- **REST-only capabilities** (not MCP tools yet): tax compute, AP/AR ageing, GSTR-2B
  reconcile, indirect-tax ledger and reconcile, US liability and 1099 reports. Full
  list: [`docs/submissions/requested_tools.md`](docs/submissions/requested_tools.md).
- **`BugReport.create`:** only `description` is required (plus optional `page`,
  `agent_seat`, `job_id`). Put steps, expected vs actual and entity ids in the
  description text. Our reports go in via the India account.
- **Platform-documented gaps are not bugs.** The locale's `not_yet_supported` lists
  them. India: e-invoicing (GST-28), e-way generation (GST-29), amendments (GST-32),
  GSTR-9 501 (GST-39), TDS returns (GST-18), depreciation posting, inventory costing,
  consolidation. US: ASC 606/842/830, US payroll filings, tax rate service (rates are
  manual), 1099 e-filing, cash basis.
- **Windows tooling:** print with UTF-8 (₹ breaks cp1252); Git Bash heredocs strip
  regex backslashes, so write scripts to files; `rm -rf "$VAR"/*` is blocked by a
  safety check, so use literal paths.

## 8. Open questions and known follow-ups

- **India now has 100 `TaxNexus` rows** although its locale says `sales_tax_nexus=false`.
  This is the same shape as B1/N126 (US data on the India company). Verify the content
  before filing.
- **India Bill count is still rising:** 254 (30 Sep) → 281 (3 Oct). Check whether the
  recurring catch-up (N220, "live in R7") is still generating.
- **AgentJob:** all 1,000 sampled jobs on India have failed: 773 with
  `agent_authority_unresolved`, 171 with "Gemini rejected the request (HTTP 400)".
  Possibly a bug, possibly expected for jobs not addressed to our seat. Unfiled.
- Why do both `Bill` and `Invoice(direction=payable)` exist? Which is the AP source of
  truth?
- How does a run get a gradable `job_id` (create an `AgentSession`, or does the grader
  supply one)?
- **`SKILL.md` and the legacy playbooks are still on the brief's illustrative model.**
  They name `TaxLine`, `Vendor`, `Invoice.update(hold_payment)` and
  `AgentMessage.create`, none of which exist; Journal/Payment should be read-only.
  Fix with the UC-05 and period-liability playbooks (harness_plan.md §9).
- `postman/` bug-report template body does not match the real `BugReport.create`
  schema (§7).
