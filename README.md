# EAGV3_Capstone_AP_tax

Capstone project for **Team 03 (School of AI, EAG V4)**: the **Ledger — Payables &
Tax Agent** seat on the **AgentSwitch** platform.

## Mission

Build an autonomous agent that answers, live, against a real shared ledger:

> "What is our tax liability this period, what is unclaimed, and is any vendor
> being paid twice?"

The agent must run **dynamically across two jurisdictions** without branching in
source code — it inspects `GET /api/accounting/locale` at runtime and adapts:

| Business | Jurisdiction | Accounting basis |
|---|---|---|
| Suryodaya Precision Works | India | Ind AS / Schedule III, GST, TDS, MSME compliance |
| Keystone Precision Works LLC | United States | US GAAP, Sales & Use Tax |

**Shared environment**: Teams 01 (General Ledger), 02 (Accounts Receivable) and 03
(this team, AP & Tax) all read/write the *same* live database (415 records), not
copies. A write from any team is visible to the others immediately — always
re-read state before acting on it.

## Grading (why the repo is shaped this way)

```
Final Score = (10 × Hand-Written Tests) + (100 × Verified Platform Bugs)
```

- **Hand-written tests only.** Tests must be authored directly by team members —
  **LLM-generated tests score 0.** When Claude (or anyone) adds a test to
  `team03-agent/tests/`, a human must actually understand and own it; don't treat
  test-writing here as a routine codegen task.
- **Goal Predicates, not prose.** Graded tests check actual database state after
  the agent runs against a live job (e.g. "is this invoice `status="under_review"`
  and `hold_payment=True`?"), not what the agent said in a chat reply. See
  `TestDuplicatePaymentGoal` in `team03-agent/tests/test_duplicate_pay.py`.
  Anything added under `team03-agent/tests/integration/` (see below) is a plain
  connectivity smoke test, *not* a Goal Predicate, and doesn't count toward this
  score the same way.
- **Bug bounty**: 100 pts per verified platform defect filed via
  `/api/bug-report`, with reproducible steps, expected vs. actual, job ID, and
  entity IDs.
- No third-party agent frameworks (LangChain, CrewAI, AutoGen, etc.) — the agent
  loop in `run_agent.py` is a hand-rolled Python loop over MCP.

## Platform access

Login is per-business (same email, different password per jurisdiction). See
`Comms from Rohan` / the instructor's message in project chat for the actual
credentials — **do not commit them anywhere in this repo.**

| What | URL |
|---|---|
| Suryodaya (India) | https://agentswitch.theschoolofai.in |
| Keystone (US) | https://class.agentswitch.theschoolofai.in |
| API docs (requires login) | `{base_url}/docs` |
| MCP endpoint | `POST {base_url}/api/mcp` |
| Brief (read first, esp. Section 8) | https://axiom.theschoolofai.in/courses/cmox5yhwl000107pgrjx41sqk/sessions/cms20eagv3asbrief00001/lesson |

Auth flow (confirmed working against the live Suryodaya instance):

```bash
export AS=https://agentswitch.theschoolofai.in        # or the Keystone URL for US
export TOKEN=$(curl -s -X POST "$AS/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"teamNN@theschoolofai.in","password":"YOUR_PASSWORD"}' \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["token"])')

curl -s "$AS/api/auth/me" -H "Authorization: Bearer $TOKEN"
```

MCP is JSON-RPC 2.0 over that same Bearer token: `initialize` →
`notifications/initialized` → `tools/list` → `tools/call`, protocol version
`2025-11-25`. There is no SSE stream (`GET /api/mcp` → 405) and no batching. See
`team03-agent/scripts/agentswitch_client.py` for the working client.

**Credentials never go in files in this repo.** Set them as environment variables
only (copy `team03-agent/.env.example` to a local, gitignored `.env`, or export
them in your shell):

```
AGENTSWITCH_BASE_URL=https://agentswitch.theschoolofai.in   # default: Suryodaya
AGENTSWITCH_EMAIL=teamNN@theschoolofai.in
AGENTSWITCH_PASSWORD=...
```

## Repo layout

```
team03-agent/
├── SKILL.md                        # Agent charter: mission, allowed/prohibited
│                                    # entities, hard safety rules (zero-trust on
│                                    # data, dynamic locale, no in-context math)
├── playbooks/
│   ├── duplicate_audit.md          # SOP: "is any vendor being paid twice?"
│   └── tax_audit.md                # SOP: tax liability & unclaimed ITC
├── scripts/
│   ├── tax_math.py                 # Deterministic GST/ITC reconciliation math
│   ├── invoice_matcher.py          # Exact + suspicious (±3 day) duplicate match
│   └── agentswitch_client.py       # Bearer-token auth + MCP JSON-RPC client,
│                                   # shared by run_agent.py and the integration tests
├── run_agent.py                    # Custom agent loop (no frameworks); LLM call
│                                   # is still a stub -- see Status below
├── tests/                          # GRADED hand-written unit tests (Goal Predicates)
│   ├── test_duplicate_pay.py
│   └── test_tax_audit.py
├── tests/integration/              # Live smoke tests, NOT part of the graded
│   │                                # score -- skipped unless credentials are set
│   ├── conftest.py
│   ├── test_api_connectivity.py    # login, /api/auth/me, /api/accounting/locale
│   └── test_mcp_connectivity.py    # MCP handshake, tools/list scope check
├── requirements.txt
├── .env.example                    # Template for local credentials (gitignored .env)
├── postman/                        # Postman collection covering every REST + MCP
│   │                                # call (see postman/README.md); real creds live
│   │                                # only in gitignored *.postman_environment.json
│   ├── AgentSwitch.postman_collection.json
│   ├── AgentSwitch.postman_environment.example.json
│   └── README.md
├── DESIGN.md                       # Loop architecture, shared-ledger state
│                                    # tolerance, refusal handling, known limitations
└── CURRENT_STATUS.md               # Ground truth from real API/MCP calls against
                                     # Suryodaya: real entity model, real tool list,
                                     # real data volumes, and where SKILL.md/
                                     # playbooks/postman need correcting as a result
```

## Postman

`team03-agent/postman/` has a full collection (login, whoami, locale, schemas,
bug-report template, and the complete MCP handshake with read/write tool-call
examples). The collection file itself has no secrets in it; real credentials live
in a Postman Environment file that's gitignored. See `team03-agent/postman/README.md`
for import/setup steps.

## Running tests

```bash
cd team03-agent
pip install -r requirements.txt

pytest tests/ -v                    # graded unit tests only (no network, no creds needed)
pytest tests/integration -v         # live connectivity checks; needs AGENTSWITCH_EMAIL/PASSWORD
```

## Status / what's done vs. outstanding

Done:
- `SKILL.md` charter, both playbooks, `tax_math.py`, `invoice_matcher.py` — **but
  see `CURRENT_STATUS.md`: these were written against the brief's illustrative
  example, and real API calls against Suryodaya show the actual entity model,
  permissions, and MCP tool names differ in several important ways (no `TaxLine`/
  `Vendor` entities, no `hold_payment` field, `AgentMessage.create` doesn't exist,
  etc.). Not yet corrected.**
- Graded hand-written unit tests for duplicate detection and GST/ITC math (9
  passing, no network needed).
- `agentswitch_client.py` + live integration tests for both the REST API and MCP
  handshake — verified passing against the real Suryodaya instance.
- Full read-only exploration of the real API/MCP surface against Suryodaya
  (`CURRENT_STATUS.md`): real entity model, full 436-tool MCP inventory, real
  `BugReport.create` schema, live record counts, and the platform's own documented
  list of known gaps (with ticket ids) for the gap report / bug-hunting strategy.
- **Week 1 gap report delivered** — `docs/gap_report.md` (all six competitors) plus
  `docs/razorpay_gap_report.md` (RazorpayX verified first-hand, screen by screen).
- **Platform bugs found, filed and two already fixed in production:**
  - `N126` — all 100 `TaxJurisdiction` rows on the India company were US sales-tax
    data → **fixed, live on server**; re-verified, those rows are now gone.
  - `N127` — tax records carrying tool names, and the Tax Summary report counting
    them as tax heads → **fixed, live on server**. The fix note records
    **8,535 tool-named values across 85 fields** corrected in both apps; our sample
    had covered ~3 fields, so the report triggered a far wider sweep.
  - `N128` — documents can store tax lines the platform's own calculator would never
    produce → **open**, filed with control tests.
  - `N173` — five feature requests, bundled → Low, "Carbon upgrade", not scheduled.
  - **`B6` (ready, not yet filed)** — re-verification found N127's fix is
    *incomplete*: parent `Tax` records are corrected but nested
    `group_taxes[].tax_type` still holds tool names (0 of 88 valid). See
    `CURRENT_STATUS.md` §9a.

Outstanding (see `DESIGN.md`, `CURRENT_STATUS.md` §7, and the Week-by-Week roadmap
in the brief):

> ⚠️ **Blocking the Week 1 review (instructor feedback, 2026-09-22):** *"Expected
> bug filing is too low, and we have not received any harness-related GitHub code
> yet."* Bug filing has since improved (five board items, two fixed in production).
> **The harness gap is still open** — the two items below are the priority.

- **`run_agent.py::call_llm` is still a stub** (`raise NotImplementedError`). The
  MCP half works and is tested; the LLM half is not wired, so there is no running
  agent. This is the "harness code" the review is asking for.
- **This repository is private.** `api.github.com/repos/spatil1985/EAGV3_Capstone_AP_tax`
  returns 404 unauthenticated, so the instructor may simply be unable to see the
  code. Make it public or add him as a collaborator.
- Apply the corrections in `CURRENT_STATUS.md` §7 to `SKILL.md`, both playbooks,
  `scripts/*.py`, and `postman/AgentSwitch.postman_collection.json`.
- Week 1 gap report (comparing AgentSwitch against a competitor like Rillet,
  Vic.ai, Mysa, CashFlo, etc. — draft companies already gathered, and
  `CURRENT_STATUS.md` §2 now has the platform's own documented gap list to build
  from; report not finalized as a deliverable).
- Keystone (US) side untested — everything so far has only been verified against
  Suryodaya (India); locale-driven branching (GST vs. Sales Tax) isn't
  implemented yet.
- Refusal/boundary tests (forbidden entities, prompt-injection resistance) not
  yet written.
- Open questions in `CURRENT_STATUS.md` §8 (Invoice-vs-Bill duplication, how our
  agent's runs tie to a gradable `job_id`, the `agent_authority_unresolved`
  scheduled-job failures) need answers before Week 2/3 work continues.
- No platform bug reports filed yet.
- CI/CD and AWS infra not yet set up.

## Team

- Sudip Patil ([spatil1985](https://github.com/spatil1985)) — sudip.patil20@gmail.com
- Geethapriya S ([geethapriya-s](https://github.com/geethapriya-s)) — geethapriyas2001@gmail.com
- Sandip Jadhav — sandip.jadhav99@gmail.com
