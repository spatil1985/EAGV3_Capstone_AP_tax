# AgentSwitch harness — design

**Date:** 2026-10-12 · **Status:** approved in chat, pending spec review · **Branch:** `feat/agentswitch-harness`

## 1. Goal

Run Team 03's agent (`aptax`) on the AgentSwitch server through **Our harness → Submit for a
run** (Release 8.1) and score as many **reliably passing, meaningful** tasks as possible.

Server contract (instructor, Release 8.1; example repo
`theschoolofai/agentswitch-harness-example`):

- `agentswitch-harness.toml` at the **git root** with `install`, `run`, `results`,
  `instances`, `timeout_minutes` (1–30).
- The run gets only these environment variables: `AGENTSWITCH_BASE_URL`, `AGENTSWITCH_TOKEN`,
  `AGENTSWITCH_INSTANCE` (`suryodaya` | `keystone`), `OPENAI_BASE_URL`, `OPENAI_API_KEY`,
  `OPENAI_MODEL`. No `.env`, no passwords, no keys of our own.
- No internet during `run` (install may use PyPI/GitHub).
- Each instance runs against a **fresh copy**; writes are thrown away.
- `results.json`: `{"tasks": [{"id", "title", "passed": bool, "score": 0–1 (optional), "evidence"}], "summary": str}`, 1–200 tasks.
- One run per team every 3 days.

## 2. Decisions

| Decision | Choice | Why |
|---|---|---|
| What to test | Deterministic playbooks (`aptax run`, dry-run), no LLM | Reliability; the platform model is unknown |
| Pass vs. score | **Hybrid**: `passed` = playbook ran cleanly; `score` = matched its verified worked example | The fresh copy may differ from the live data the goldens came from; drift must not turn tasks red |
| Golden matching | Substring of the playbook's own `summary` / `context` | No new structured field in 56 playbooks |
| Blocked / spec-only playbooks | Listed as `passed: false` with the router's reason | Shows the full scope honestly |
| Other-regime playbooks | Omitted (US playbooks on Suryodaya and vice versa) | They do not apply to that instance |
| Instances | `["suryodaya", "keystone"]` | The agent is built for both |
| Writes | Dry-run (aptax default) | Unchanged safety posture; escalations suppressed |

Out of scope: LLM-agent tasks, the `openai` dependency, CI, changes to playbook logic.

## 3. Layout

```
EAGV3_Capstone_AP_tax/                 git root
├── agentswitch-harness.toml           NEW
└── team03-agent/
    ├── scripts/agentswitch_client.py  CHANGED: AgentSwitchClient.from_token(base_url, token)
    ├── aptax/service.py               CHANGED: make_transport() prefers {prefix}_TOKEN
    ├── harness/                       NEW
    │   ├── __init__.py
    │   ├── __main__.py                entry point
    │   ├── tasks.py                   pure: runs/routes → task dicts
    │   ├── validate.py                results.json schema check (CLI + importable)
    │   └── goldens.yaml               playbook id → expected figure strings
    └── tests_generated/harness_tests/       NEW, ungraded (LLM-written tests never go in tests/)
```

`agentswitch-harness.toml`:

```toml
install = "pip install -r team03-agent/requirements.txt"
run     = "cd team03-agent && python -m harness"
results = "team03-agent/results.json"
instances = ["suryodaya", "keystone"]
timeout_minutes = 20
```

`results.json` is added to `.gitignore` (`team03-agent/results.json`).

## 4. Components

### 4.1 Token auth
- `AgentSwitchClient.from_token(base_url, token)` builds the client with the Bearer header
  and makes no login call.
- `service.make_transport(tenant)`: if `{prefix}_TOKEN` is set (prefix from `config.TENANTS`:
  `in` → `AGENTSWITCH`, `us` → `US_AGENTSWITCH`), use `from_token({prefix}_BASE_URL, token)`.
  Otherwise use the current email/password path unchanged. Local CLI use is unaffected.

### 4.2 `harness/__main__.py`
1. Read `AGENTSWITCH_BASE_URL`, `AGENTSWITCH_TOKEN`, `AGENTSWITCH_INSTANCE`. If any is
   missing, or the instance is not `suryodaya` / `keystone`, write one failed task naming
   the problem and exit 0.
2. Map the instance to a tenant (`suryodaya` → `in`, `keystone` → `us`). Copy the base URL
   and token into the tenant's prefix (`US_AGENTSWITCH_BASE_URL` / `US_AGENTSWITCH_TOKEN` for `us`).
3. **Platform tasks**:
   - `mcp_tools_list`: passes when tools/list returns more than 0 tools.
   - `locale_matches_instance`: passes when the regime is `gst` on `in` and `sales_use_tax` on `us`.
   - `whoami`: passes when `/api/auth/me` returns a user.

   If tools/list fails, also add one failed task `playbooks_skipped` and stop there (go to step 6).
4. **Playbooks**: open a dry-run session and get the routes. For each route with
   action `run`, in order:
   - If the global deadline (17 min from start) has passed, emit `passed: false`,
     evidence `"not run: harness time budget exhausted"`.
   - Otherwise snapshot `gateway.stats["failed"]`, call `runner.run_one(manifest)` inside
     try/except, and take the snapshot again. Record the error (or the exception's repr),
     the failed-call delta and the elapsed time.
5. **Routing tasks** (a route is "other-regime" when `ctx.tax_regime` is not in `manifest.tax_regimes`; those are omitted):
   - Each route for the instance's own regime that does not run (blocked, spec-only,
     missing tools, vertical mismatch) becomes `passed: false`, with the router's reason as evidence.
   - `routing_floor`: passes when the number of `run` routes is at least the floor
     (`in`: 36, `us`: 18).
6. Write `results.json` in a `finally` block. If anything above raised an exception, the
   file holds whatever tasks were collected plus `harness_crashed` (traceback trimmed).
   Exit 0 whenever the file was written.

Each instance runs as its own server process, so a run never shares state with the other instance.
The runner's SQLite store is the existing default under `runs/`.

### 4.3 `harness/tasks.py` (pure, no I/O)
- Task id: `{instance}:{playbook id}` (e.g. `suryodaya:uc-23`) or `{instance}:{check}`.
  The title is the manifest title.
- **Playbook task**:
  - `passed = error is None and failed_delta == 0`.
  - `score`:
    - 0.0 if not passed.
    - Otherwise 1.0 if the playbook has no goldens or every golden string occurs in
      `outcome.summary` or `json.dumps(outcome.context, default=str)`.
    - Otherwise 0.5.
  - `evidence`: summary, finding count, and golden result
    (e.g. `golden 5,72,073.68: found`).
- **Route task** (did not run): `passed: false, score: 0.0`, evidence is the route reason.
- **Normalisation**:
  - Evidence is trimmed to 500 characters.
  - Duplicate ids get a `#2` suffix.
  - Above 200 tasks, the list is truncated and the summary says so.
- **Summary**: `"{instance}: {passed}/{total} passed · goldens {exact}/{with_goldens} exact"`.

### 4.4 `harness/goldens.yaml`
- Maps a playbook id to a list of exact figure strings, formatted the way the playbook prints them.
- Seeded from the figures already verified in `CURRENT_STATUS.md` §4.2:
  - UC-23 `5,72,073.68`
  - UC-26 `45,152.62`
  - UC-41 `4,91,099.27`
  - UC-43 `56,20,600`
  - US-01 `226,488.27`
  - US-05 `7,919.93`
- Further figures come from the specs' worked examples, confirmed by a local run.
- Only figures that a local dry-run reproduces go into this file.

### 4.5 `harness/validate.py`
- `validate(doc) -> list[str]` returns the problems it finds, and an empty list means OK.
  It checks:
  - `tasks` is a list of 1–200 items.
  - Each task has a non-empty `id`, a `title`, a bool `passed`, an optional `score` that is
    a number in [0, 1], and string `evidence`.
  - Ids are unique.
  - `summary` is a string.
- CLI: `python -m harness.validate results.json` exits 1 and prints the problems.

## 5. Error handling and time budget

- Every HTTP call keeps the transport's existing 30-second timeout and retry-with-backoff.
- There is no per-playbook timeout: Python cannot kill a hung thread. The HTTP timeouts
  plus the 17-minute global deadline (below the 20-minute server limit) keep the run bounded.
- `results.json` is always written. Pass/fail is in the file, never in the exit code.

## 6. Testing

Offline unit tests in `tests_generated/harness_tests/`, using fake runs, routes and transport.
None of them use the network.

**Task mapping**
- Clean run, golden found → 1.0.
- Clean run, golden missing → 0.5.
- Run with an error → 0.
- Failed-call delta greater than 0 → failed.
- Blocked route → failed, with the reason as evidence.
- Route for the other regime → omitted.

**Goldens**
- Indian and US number formats match as substrings of the summary or the context JSON.

**Results format**
- `validate` accepts good docs and rejects each kind of bad doc.
- Normalisation: evidence trimming, duplicate ids, the 200-task cap.

**`__main__` failure paths**
- Missing env vars → one failed task.
- Unknown instance → one failed task.
- An exception partway through → `harness_crashed`, and the file is still written.
- Deadline passed → the remaining playbooks are reported "not run".

**Token auth**
- `from_token` sends the Bearer header and makes no login request.
- `make_transport` prefers the token and falls back to email/password.

**Live check before submitting**
1. Run `python -m harness` with a seat token against both tenants (dry-run).
2. Time each run; it must finish well under 17 minutes.
3. Run `validate` on both outputs.
4. Look at every 0.5 score and resolve it (fix the golden figure, or find the drift).
5. Make a clean venv, run the toml's `install`, then run its `run` from the git root.
