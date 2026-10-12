# AgentSwitch Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run every live aptax playbook on the AgentSwitch server (Release 8.1 "Our harness") and report one pass/fail task per playbook in `results.json`. A task scores 1.0 when its verified worked-example figure is reproduced, and 0.5 when the playbook ran cleanly but the figure didn't match.

**Architecture:**
- A new `team03-agent/harness/` package does the run:
  - `__main__.py` reads the server's env vars, opens a dry-run aptax session, and runs each routed playbook through the existing `PlaybookRunner`.
  - `tasks.py` is pure code that turns each run or route into a task dict.
  - `validate.py` checks the instructor's `results.json` schema.
- aptax gets one new path: `make_transport()` uses a seat token (`{prefix}_TOKEN`) when one is set.
- `scripts/harness_env.sh` recreates the server's env vars locally by logging in with curl.

**Tech Stack:** Python 3.10+ (local venv 3.14), `requests`, `pyyaml` (both already in `requirements.txt`), pytest, bash/zsh plus curl for the helper script.

**Spec:** `team03-agent/docs/superpowers/specs/2026-10-12-agentswitch-harness-design.md`

## Global Constraints

- `agentswitch-harness.toml` sits at the **git root** (`EAGV3_Capstone_AP_tax/`) and contains exactly:
  - `install = "pip install -r team03-agent/requirements.txt"`
  - `run = "cd team03-agent && python -m harness"`
  - `results = "team03-agent/results.json"`
  - `instances = ["suryodaya", "keystone"]`
  - `timeout_minutes = 20`
- Instance → tenant → regime: `suryodaya` → `in` → `gst`; `keystone` → `us` → `sales_use_tax`. Env prefix by tenant comes from `aptax.config.TENANTS`: `in` → `AGENTSWITCH`, `us` → `US_AGENTSWITCH`.
- The routing floor is at least 36 `run` routes on `in` and at least 18 on `us`. The global deadline is 17 minutes (`17 * 60` s).
- `results.json` holds 1–200 tasks. Each task has a non-empty unique `id`, a str `title`, a bool `passed`, a `score` in [0, 1] and a str `evidence` of at most 500 chars. There is also a str `summary`.
- `results.json` is always written. `python -m harness` exits 0 whenever it was written.
- Runs are dry-run only (`dry_run=True`, `escalate=False`). No ledger writes.
- No new runtime dependencies. No LLM, no `openai`.
- Credentials never go in files. Never print a password or a full token.
- **Tests written by an LLM go only in `team03-agent/tests_generated/harness_tests/`, never in `team03-agent/tests/`** (the capstone grades only hand-written tests). Every such file starts with a docstring beginning `LLM-generated, not graded.`
- Run all commands from `team03-agent/` with the repo venv: `../.venv/bin/python -m pytest …`.
- Commit only the paths each task lists (the working tree has unrelated user edits: `.env.example`, `CURRENT_STATUS.md`, `aptax/llm/glc.py`). Commits are SSH-signed, so `git commit` must run outside the Claude Code sandbox. End every commit message with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A password or email containing `"`, `$` or spaces in `harness_env.sh`:** the JSON body must still be valid, nothing may be shell-expanded, and the password must never appear in curl's argv. This is pinned in Task 6 (`test_success_keystone_exports_and_hides_secrets`).
2. **Sourcing `harness_env.sh keystone` and then running the normal `aptax --tenant in` CLI in the same shell:** `AGENTSWITCH_TOKEN` now targets Keystone. The script must warn about this on stderr. Pinned in Task 6 (`test_warns_that_the_shell_now_targets_the_instance`).
3. **Whitespace or a trailing slash in the server's `AGENTSWITCH_BASE_URL` / `AGENTSWITCH_TOKEN`:** these must be stripped before use. Pinned in Task 1 (`test_from_token_sets_bearer_without_login`) and Task 4 (`test_env_values_are_stripped_and_mapped_to_the_tenant_prefix`).
4. **An exception that escapes `runner.run_one` (for example from the store) for one playbook:** that playbook fails and the rest still run. Pinned in Task 4 (`test_exception_from_run_one_fails_only_that_playbook`).
5. **Running `python -m harness` from a directory other than `team03-agent/`:** results must still land at the path the toml names. Pinned in Task 5 (`test_results_path_matches_toml`).

---

## File Structure

| Path (git root = `EAGV3_Capstone_AP_tax/`) | Responsibility |
|---|---|
| `agentswitch-harness.toml` (create) | Server contract |
| `.gitignore` (modify) | Ignore `team03-agent/results.json` and `*.json.tmp` |
| `team03-agent/scripts/agentswitch_client.py` (modify) | `AgentSwitchClient.from_token` |
| `team03-agent/aptax/service.py:65-79` (modify) | `make_transport` token path |
| `team03-agent/harness/__init__.py` (create) | Package docstring |
| `team03-agent/harness/validate.py` (create) | `validate(doc)`, CLI |
| `team03-agent/harness/tasks.py` (create) | Pure task mapping, goldens loader, finalize |
| `team03-agent/harness/goldens.yaml` (create) | Expected figures per playbook |
| `team03-agent/harness/__main__.py` (create) | Orchestration, results writing |
| `team03-agent/harness/README.md` (create) | How to run locally / what the server does |
| `team03-agent/scripts/harness_env.sh` (create) | Local login helper |
| `team03-agent/tests_generated/harness_tests/__init__.py` (create) | Test package |
| `team03-agent/tests_generated/harness_tests/fakes.py` (create) | Stand-ins for aptax objects |
| `team03-agent/tests_generated/harness_tests/test_token_auth.py` | Task 1 |
| `team03-agent/tests_generated/harness_tests/test_validate.py` | Task 2 |
| `team03-agent/tests_generated/harness_tests/test_tasks.py` | Task 3 |
| `team03-agent/tests_generated/harness_tests/test_main.py` | Task 4 |
| `team03-agent/tests_generated/harness_tests/test_toml.py` | Task 5 |
| `team03-agent/tests_generated/harness_tests/test_harness_env.py` | Task 6 |

---

### Task 1: Seat-token auth

**Files:**
- Modify: `team03-agent/scripts/agentswitch_client.py` (add a classmethod after `login`)
- Modify: `team03-agent/aptax/service.py:65-79` (`make_transport`)
- Create: `team03-agent/tests_generated/harness_tests/__init__.py`
- Test: `team03-agent/tests_generated/harness_tests/test_token_auth.py`

**Interfaces:**
- Produces:
  - `AgentSwitchClient.from_token(base_url: str, token: str) -> AgentSwitchClient`. It strips both arguments and raises `AgentSwitchAuthError` if either is empty.
  - `aptax.service.make_transport(tenant)`: when `os.environ[f"{prefix}_TOKEN"]` is non-empty, it returns `LiveTransport(AgentSwitchClient.from_token(base_url, token))`, and raises `ServiceError` if `{prefix}_BASE_URL` is empty. Otherwise it behaves as before.

- [ ] **Step 1: Write the failing tests**

`team03-agent/tests_generated/harness_tests/__init__.py`:

```python
"""LLM-generated, not graded. Offline checks for the AgentSwitch server harness."""
```

`team03-agent/tests_generated/harness_tests/test_token_auth.py`:

```python
"""LLM-generated, not graded. Seat-token auth: from_token and make_transport's token path."""

import pytest
import requests

from aptax import service
from aptax.agentswitch.transport import LiveTransport
from scripts.agentswitch_client import AgentSwitchAuthError, AgentSwitchClient


@pytest.fixture
def no_network(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("network call attempted")
    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setattr(requests, "get", boom)


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.setattr(service, "load_dotenv", lambda: 0)   # never read the developer's .env
    for prefix in ("AGENTSWITCH", "US_AGENTSWITCH"):
        for key in ("BASE_URL", "TOKEN", "EMAIL", "PASSWORD"):
            monkeypatch.delenv(f"{prefix}_{key}", raising=False)


def test_from_token_sets_bearer_without_login(no_network):
    client = AgentSwitchClient.from_token(" https://class.example/ ", " tok123\n")
    assert client.base_url == "https://class.example"
    assert client.token == "tok123"
    assert client._session.headers["Authorization"] == "Bearer tok123"


@pytest.mark.parametrize("base_url, token", [("", "tok"), ("https://x", "  ")])
def test_from_token_rejects_empty_values(base_url, token):
    with pytest.raises(AgentSwitchAuthError):
        AgentSwitchClient.from_token(base_url, token)


def test_make_transport_prefers_token(clean_env, no_network, monkeypatch):
    monkeypatch.setenv("US_AGENTSWITCH_BASE_URL", "https://class.example/")
    monkeypatch.setenv("US_AGENTSWITCH_TOKEN", "tok-us")
    monkeypatch.setenv("US_AGENTSWITCH_EMAIL", "x@y")
    monkeypatch.setenv("US_AGENTSWITCH_PASSWORD", "pw")
    transport = service.make_transport("us")
    assert isinstance(transport, LiveTransport)
    assert transport._client.token == "tok-us"
    assert transport._client.base_url == "https://class.example"


def test_token_without_base_url_is_an_error(clean_env, monkeypatch):
    monkeypatch.setenv("AGENTSWITCH_TOKEN", "tok")
    with pytest.raises(service.ServiceError, match="AGENTSWITCH_BASE_URL"):
        service.make_transport("in")


def test_falls_back_to_login_without_token(clean_env, monkeypatch):
    monkeypatch.setenv("AGENTSWITCH_EMAIL", "a@b")
    monkeypatch.setenv("AGENTSWITCH_PASSWORD", "pw")
    calls = []

    def fake_login(cls, base_url, email, password):
        calls.append((base_url, email, password))
        return AgentSwitchClient(base_url, "tok-login")

    monkeypatch.setattr(AgentSwitchClient, "login", classmethod(fake_login))
    transport = service.make_transport("in")
    assert calls == [("https://agentswitch.theschoolofai.in", "a@b", "pw")]
    assert transport._client.token == "tok-login"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_token_auth.py -q`
Expected: FAIL. The `from_token` tests fail with `AttributeError: type object 'AgentSwitchClient' has no attribute 'from_token'`. `test_make_transport_prefers_token` fails because it calls the patched `requests.post` ("network call attempted"). `test_token_without_base_url_is_an_error` fails because it raises "credentials missing" instead of the expected message.

- [ ] **Step 3: Implement**

In `team03-agent/scripts/agentswitch_client.py`, add this directly after the `login` classmethod:

```python
    @classmethod
    def from_token(cls, base_url: str, token: str) -> "AgentSwitchClient":
        """Use a token the caller already holds (the AgentSwitch harness runner gives one) -- no login."""
        base_url, token = (base_url or "").strip(), (token or "").strip()
        if not base_url or not token:
            raise AgentSwitchAuthError("from_token needs a base URL and a token")
        return cls(base_url, token)
```

In `team03-agent/aptax/service.py`, replace the whole `make_transport` function (lines 65–79) with:

```python
def make_transport(tenant: str, *, record: str | None = None, replay: str | None = None):
    """Live by default; --replay serves a recording offline; --record saves one.

    A seat token (`{prefix}_TOKEN`, what the AgentSwitch harness runner provides) wins over
    email/password login.
    """
    if replay:
        return ReplayTransport(Path(replay))
    load_dotenv()
    prefix = TENANTS[tenant]
    from scripts.agentswitch_client import AgentSwitchClient
    token = os.environ.get(f"{prefix}_TOKEN", "").strip()
    if token:
        base_url = os.environ.get(f"{prefix}_BASE_URL", "").strip()
        if not base_url:
            raise ServiceError(f"{prefix}_TOKEN is set but {prefix}_BASE_URL is not")
        live = LiveTransport(AgentSwitchClient.from_token(base_url, token))
        return RecordingTransport(live, Path(record)) if record else live
    missing = [f"{prefix}_{k}" for k in ("EMAIL", "PASSWORD") if not os.environ.get(f"{prefix}_{k}")]
    if missing:
        raise ServiceError(f"credentials missing: set {', '.join(missing)} (see .env.example)")
    try:
        live = LiveTransport(AgentSwitchClient.from_env(prefix))
    except Exception as exc:  # noqa: BLE001 — login failures are reported, never retried blindly
        raise ServiceError(f"could not log in to AgentSwitch ({tenant}): {type(exc).__name__}: {exc}") from exc
    return RecordingTransport(live, Path(record)) if record else live
```

- [ ] **Step 4: Run the tests to verify they pass, and that nothing else broke**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_token_auth.py -q && ../.venv/bin/python -m pytest -q`
Expected: `6 passed` for the new file. The full suite passes as before; live tests skip without credentials.

- [ ] **Step 5: Commit** (outside the sandbox; SSH signing)

```bash
git add team03-agent/scripts/agentswitch_client.py team03-agent/aptax/service.py \
        team03-agent/tests_generated/harness_tests/__init__.py \
        team03-agent/tests_generated/harness_tests/test_token_auth.py
git commit -m "Accept a seat token in make_transport (AgentSwitch harness runner)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: results.json validator

**Files:**
- Create: `team03-agent/harness/__init__.py`
- Create: `team03-agent/harness/validate.py`
- Test: `team03-agent/tests_generated/harness_tests/test_validate.py`

**Interfaces:**
- Produces:
  - `harness.validate.validate(doc) -> list[str]`: the list of problems, empty when the doc is valid.
  - `harness.validate.main(argv: list[str] | None = None) -> int`: returns 0 when valid, 1 otherwise.
  - `harness.validate.MAX_TASKS = 200` and `harness.validate.EVIDENCE_MAX = 500`.

- [ ] **Step 1: Write the failing tests**

`team03-agent/tests_generated/harness_tests/test_validate.py`:

```python
"""LLM-generated, not graded. harness.validate against the Release 8.1 results.json contract."""

import json

import pytest

from harness.validate import main, validate


def task(**over):
    t = {"id": "suryodaya:uc-05", "title": "Duplicate vendor payment", "passed": True,
         "score": 1.0, "evidence": "11 candidates"}
    t.update(over)
    return t


def doc(*tasks, summary="suryodaya: 1/1 passed"):
    return {"tasks": list(tasks), "summary": summary}


def test_good_doc_has_no_problems():
    assert validate(doc(task())) == []


def test_score_is_optional():
    t = task()
    del t["score"]
    assert validate(doc(t)) == []


@pytest.mark.parametrize("bad, fragment", [
    ([], "top level"),
    ({"summary": "x"}, "tasks must be a list"),
    (doc(), "1-200"),
    (doc(*[task(id=f"t{i}") for i in range(201)]), "1-200"),
    (doc(task(id="")), "id"),
    (doc(task(), task()), "duplicate"),
    (doc(task(title=None)), "title"),
    (doc(task(passed="true")), "passed"),
    (doc(task(passed=1)), "passed"),
    (doc(task(score=1.5)), "score"),
    (doc(task(score=True)), "score"),
    (doc(task(score=float("nan"))), "score"),
    (doc(task(evidence=None)), "evidence"),
    (doc(task(evidence="x" * 501)), "evidence"),
    (doc(task(), summary=None), "summary"),
])
def test_each_violation_is_reported(bad, fragment):
    problems = validate(bad)
    assert problems and any(fragment in p for p in problems), problems


def test_cli_ok_and_failure(tmp_path, capsys):
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps(doc(task())))
    bad.write_text(json.dumps(doc(task(passed="yes"))))
    assert main([str(good)]) == 0
    assert "OK (1 tasks)" in capsys.readouterr().out
    assert main([str(bad)]) == 1
    assert main([str(tmp_path / "missing.json")]) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_validate.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness'`.

- [ ] **Step 3: Implement**

`team03-agent/harness/__init__.py`:

```python
"""AgentSwitch server harness (Release 8.1): `python -m harness` runs aptax's live playbooks
in dry-run and writes results.json. Design:
docs/superpowers/specs/2026-10-12-agentswitch-harness-design.md
"""
```

`team03-agent/harness/validate.py`:

```python
"""Check a results.json against the AgentSwitch harness contract (Release 8.1).

    python -m harness.validate results.json      # exit 0 = OK, 1 = problems printed

{"tasks": [{"id", "title", "passed": bool, "score": 0-1 (optional), "evidence"}], "summary": str},
1-200 tasks. We also hold ourselves to unique ids and evidence of at most 500 characters.
"""

import json
import sys
from pathlib import Path

MAX_TASKS = 200
EVIDENCE_MAX = 500


def _task_problems(where: str, t, ids: set) -> list[str]:
    if not isinstance(t, dict):
        return [f"{where} must be an object"]
    problems = []
    tid = t.get("id")
    if not isinstance(tid, str) or not tid:
        problems.append(f"{where}.id must be a non-empty string")
    elif tid in ids:
        problems.append(f"{where}.id {tid!r} is a duplicate")
    else:
        ids.add(tid)
    if not isinstance(t.get("title"), str):
        problems.append(f"{where}.title must be a string")
    if not isinstance(t.get("passed"), bool):
        problems.append(f"{where}.passed must be true or false")
    if "score" in t:
        s = t["score"]
        if isinstance(s, bool) or not isinstance(s, (int, float)) or not 0 <= s <= 1:
            problems.append(f"{where}.score must be a number from 0 to 1")
    ev = t.get("evidence")
    if not isinstance(ev, str):
        problems.append(f"{where}.evidence must be a string")
    elif len(ev) > EVIDENCE_MAX:
        problems.append(f"{where}.evidence is longer than {EVIDENCE_MAX} characters")
    return problems


def validate(doc) -> list[str]:
    if not isinstance(doc, dict):
        return ["top level must be an object"]
    problems = []
    tasks = doc.get("tasks")
    if not isinstance(tasks, list):
        problems.append("tasks must be a list")
    else:
        if not 1 <= len(tasks) <= MAX_TASKS:
            problems.append(f"tasks must have 1-{MAX_TASKS} items, got {len(tasks)}")
        ids: set = set()
        for i, t in enumerate(tasks):
            problems += _task_problems(f"tasks[{i}]", t, ids)
    if not isinstance(doc.get("summary"), str):
        problems.append("summary must be a string")
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0] if argv else "results.json")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{path}: {exc}")
        return 1
    problems = validate(doc)
    for p in problems:
        print(f"{path}: {p}")
    if not problems:
        print(f"{path}: OK ({len(doc['tasks'])} tasks)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_validate.py -q`
Expected: `18 passed`.

- [ ] **Step 5: Commit** (outside the sandbox)

```bash
git add team03-agent/harness/__init__.py team03-agent/harness/validate.py \
        team03-agent/tests_generated/harness_tests/test_validate.py
git commit -m "Add results.json validator for the AgentSwitch harness

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Task mapping and goldens

**Files:**
- Create: `team03-agent/harness/tasks.py`
- Create: `team03-agent/harness/goldens.yaml`
- Create: `team03-agent/tests_generated/harness_tests/fakes.py`
- Test: `team03-agent/tests_generated/harness_tests/test_tasks.py`

**Interfaces:**
- Consumes: `harness.validate.MAX_TASKS`, `harness.validate.EVIDENCE_MAX` (Task 2).
- Reads these duck-typed objects:
  - a manifest, using `.id`, `.title` and `.tax_regimes`;
  - a route, using `.manifest`, `.action` (`run|skip|spec|blocked`) and `.reason`;
  - an outcome, using `.summary`, `.context` and `.findings`.
- Produces (`harness.tasks`):
  - Constants: `GOLDENS_PATH: Path`, `INSTANCES = {"suryodaya": ("in", "gst"), "keystone": ("us", "sales_use_tax")}`, `ROUTING_FLOOR = {"in": 36, "us": 18}`, `PARTIAL_SCORE = 0.5`, and the re-exported `EVIDENCE_MAX` and `MAX_TASKS`.
  - `make_task(instance, key, title, passed, score, evidence) -> dict`, which gives the id `f"{instance}:{key}"`.
  - `is_other_regime(manifest, tax_regime) -> bool`
  - `route_task(instance, route, tax_regime) -> dict | None`
  - `golden_check(figures: list[str], outcome) -> list[tuple[str, bool]]`
  - `playbook_task(instance, manifest, outcome, error: str | None, failed_delta: int, figures: list[str]) -> dict`
  - `not_run_task(instance, manifest, reason: str, has_golden: bool = False) -> dict`
  - `routing_floor_task(instance, tenant, runnable: int) -> dict`
  - `load_goldens(path: Path = GOLDENS_PATH) -> dict[str, list[str]]`
  - `finalize(instance, tasks: list[dict]) -> dict` returns `{"tasks": [...], "summary": str}`. It strips the private `_golden` key, makes ids unique (`#2`, …), trims evidence to 500 chars ending in `…`, caps at 200 tasks, and never returns an empty list.
  - Playbook, route and not-run tasks carry a private key `_golden: (exact: bool, has_golden: bool)`, which only `finalize` reads.

- [ ] **Step 1: Write the fakes and the failing tests**

`team03-agent/tests_generated/harness_tests/fakes.py`:

```python
"""LLM-generated, not graded. Stand-ins for the aptax objects the harness reads."""

from dataclasses import dataclass, field


@dataclass
class FakeManifest:
    id: str
    title: str = "A playbook"
    tax_regimes: tuple = ("gst",)


@dataclass
class FakeRoute:
    manifest: FakeManifest
    action: str = "run"
    reason: str = ""


@dataclass
class FakeOutcome:
    summary: str = ""
    context: dict = field(default_factory=dict)
    findings: list = field(default_factory=list)


@dataclass
class FakeRun:
    route: FakeRoute
    outcome: FakeOutcome | None = None
    error: str | None = None


@dataclass
class FakeCtx:
    tax_regime: str


class FakeGateway:
    def __init__(self):
        self.stats = {"called": 0, "refused": 0, "suppressed": 0, "failed": 0}


class FakeRunner:
    """routes: list[FakeRoute]; behaviours: playbook id -> fn(gateway, manifest) -> FakeRun."""

    def __init__(self, gateway, routes, behaviours):
        self.gateway = gateway
        self._routes = routes
        self._behaviours = behaviours
        self.ran = []

    def routes(self, *, trigger=None, cadence=None):
        return list(self._routes)

    def run_one(self, manifest, *, escalate=False):
        assert escalate is False
        self.ran.append(manifest.id)
        return self._behaviours[manifest.id](self.gateway, manifest)


class FakeSession:
    def __init__(self, tax_regime, routes, behaviours):
        self.ctx = FakeCtx(tax_regime)
        self.gateway = FakeGateway()
        self.runner = FakeRunner(self.gateway, routes, behaviours)
        self.run_id = "run-1"


class FakeTransport:
    def __init__(self, tools=("Bill.list",), me=None, tools_error=None):
        self.tools = tools
        self.me = {"email": "team03@theschoolofai.in"} if me is None else me
        self.tools_error = tools_error

    def tools_list(self):
        if self.tools_error:
            raise self.tools_error
        return list(self.tools)

    def rest(self, method, path, params=None, body=None):
        assert (method, path) == ("GET", "/api/auth/me")
        return self.me


class FakeStore:
    def __init__(self):
        self.finished = []
        self.closed = False

    def finish_run(self, run_id, status):
        self.finished.append((run_id, status))

    def close(self):
        self.closed = True
```

`team03-agent/tests_generated/harness_tests/test_tasks.py`:

```python
"""LLM-generated, not graded. harness.tasks: runs and routes -> results.json tasks."""

from decimal import Decimal

import pytest

from harness import tasks as T
from harness.validate import validate
from harness_tests.fakes import FakeManifest, FakeOutcome, FakeRoute

UC23 = FakeManifest("uc-23", "Cash-basis tax", ("gst",))
US01 = FakeManifest("us-01", "Period sales tax", ("sales_use_tax",))


def test_make_task_shape():
    t = T.make_task("suryodaya", "uc-23", "Cash-basis tax", 1, 1, 42)
    assert t == {"id": "suryodaya:uc-23", "title": "Cash-basis tax", "passed": True,
                 "score": 1.0, "evidence": "42"}


def test_route_task_omits_runnable_and_other_regime():
    assert T.route_task("suryodaya", FakeRoute(UC23, "run"), "gst") is None
    assert T.route_task("suryodaya", FakeRoute(US01, "skip", "tax_regime gst not in"), "gst") is None


@pytest.mark.parametrize("action, reason", [
    ("blocked", "blocked by N14"),
    ("spec", "spec only — no school tenant or data yet"),
    ("skip", "vertical manufacturing not in ['school']"),
    ("skip", "locale feature(s) off: gst_ims"),
])
def test_own_regime_route_that_does_not_run_fails(action, reason):
    t = T.route_task("suryodaya", FakeRoute(UC23, action, reason), "gst")
    assert t["passed"] is False and t["score"] == 0.0
    assert t["evidence"] == f"{action}: {reason}"
    assert t["id"] == "suryodaya:uc-23"


def test_all_regime_manifest_is_ours():
    m = FakeManifest("uc-99", tax_regimes=("all",))
    assert T.route_task("keystone", FakeRoute(m, "blocked", "x"), "sales_use_tax")["passed"] is False


def test_golden_found_in_summary_scores_one():
    out = FakeOutcome("₹5,72,073.68 cash-basis tax for August", findings=[1, 2])
    t = T.playbook_task("suryodaya", UC23, out, None, 0, ["5,72,073.68"])
    assert t["passed"] is True and t["score"] == 1.0
    assert t["evidence"].startswith("golden 5,72,073.68: found")
    assert "findings=2" in t["evidence"]
    assert t["_golden"] == (True, True)


def test_golden_found_as_raw_context_value():
    out = FakeOutcome("done", context={"total": Decimal("226488.27")})
    t = T.playbook_task("keystone", US01, out, None, 0, ["226488.27"])
    assert t["score"] == 1.0


def test_golden_missing_still_passes_at_half_score():
    out = FakeOutcome("₹5,70,000.00 cash-basis tax")
    t = T.playbook_task("suryodaya", UC23, out, None, 0, ["5,72,073.68"])
    assert t["passed"] is True and t["score"] == T.PARTIAL_SCORE
    assert t["evidence"].startswith("golden 5,72,073.68: NOT found")
    assert t["_golden"] == (False, True)


def test_no_goldens_scores_one():
    t = T.playbook_task("suryodaya", UC23, FakeOutcome("ok"), None, 0, [])
    assert t["score"] == 1.0 and t["_golden"] == (False, False)


def test_error_fails():
    t = T.playbook_task("suryodaya", UC23, None, "KeyError: 'taxes'", 0, ["5,72,073.68"])
    assert t["passed"] is False and t["score"] == 0.0
    assert t["evidence"] == "error: KeyError: 'taxes'"
    assert t["_golden"] == (False, True)


def test_failed_mcp_calls_fail_the_playbook():
    t = T.playbook_task("suryodaya", UC23, FakeOutcome("ok"), None, 2, [])
    assert t["passed"] is False and t["score"] == 0.0
    assert t["evidence"].startswith("2 MCP call(s) failed")


def test_no_outcome_and_no_error_fails():
    t = T.playbook_task("suryodaya", UC23, None, None, 0, [])
    assert t["passed"] is False and "no outcome" in t["evidence"]


def test_not_run_task():
    t = T.not_run_task("suryodaya", UC23, "not run: harness time budget exhausted", True)
    assert t["passed"] is False and t["evidence"] == "not run: harness time budget exhausted"
    assert t["_golden"] == (False, True)


@pytest.mark.parametrize("tenant, count, passed", [("in", 36, True), ("in", 35, False), ("us", 18, True)])
def test_routing_floor(tenant, count, passed):
    t = T.routing_floor_task("x", tenant, count)
    assert t["passed"] is passed
    assert t["evidence"] == f"{count} playbooks routed to run (floor {T.ROUTING_FLOOR[tenant]})"


def test_golden_evidence_survives_trimming():
    out = FakeOutcome("x" * 2000)
    doc = T.finalize("suryodaya", [T.playbook_task("suryodaya", UC23, out, None, 0, ["5,72,073.68"])])
    ev = doc["tasks"][0]["evidence"]
    assert len(ev) == T.EVIDENCE_MAX and ev.endswith("…") and ev.startswith("golden 5,72,073.68")


def test_finalize_dedupes_strips_private_keys_and_summarises():
    a = T.playbook_task("suryodaya", UC23, FakeOutcome("₹5,72,073.68"), None, 0, ["5,72,073.68"])
    b = T.playbook_task("suryodaya", UC23, FakeOutcome("ok"), None, 0, ["9,99,999.99"])
    c = T.make_task("suryodaya", "whoami", "whoami", False, 0.0, "boom")
    doc = T.finalize("suryodaya", [a, b, c])
    assert [t["id"] for t in doc["tasks"]] == ["suryodaya:uc-23", "suryodaya:uc-23#2", "suryodaya:whoami"]
    assert all("_golden" not in t for t in doc["tasks"])
    assert doc["summary"] == "suryodaya: 2/3 passed · goldens 1/2 exact"
    assert validate(doc) == []


def test_finalize_caps_at_max_tasks():
    many = [T.make_task("k", f"t{i}", "t", True, 1.0, "") for i in range(205)]
    doc = T.finalize("k", many)
    assert len(doc["tasks"]) == T.MAX_TASKS
    assert doc["summary"].endswith("· 5 task(s) dropped (limit 200)")
    assert validate(doc) == []


def test_finalize_never_returns_an_empty_list():
    doc = T.finalize("harness", [])
    assert [t["id"] for t in doc["tasks"]] == ["harness:no_tasks"]
    assert validate(doc) == []


def test_load_goldens(tmp_path):
    assert T.load_goldens(tmp_path / "missing.yaml") == {}
    p = tmp_path / "g.yaml"
    p.write_text('uc-23: ["5,72,073.68"]\nus-01: [226488.27]\n', encoding="utf-8")
    assert T.load_goldens(p) == {"uc-23": ["5,72,073.68"], "us-01": ["226488.27"]}
    p.write_text("uc-23: 5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="uc-23"):
        T.load_goldens(p)


def test_shipped_goldens_load():
    goldens = T.load_goldens()
    assert goldens and all(figs and all(isinstance(f, str) and f for f in figs) for figs in goldens.values())
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_tasks.py -q`
Expected: FAIL with `ImportError: cannot import name 'tasks' from 'harness'`.

- [ ] **Step 3: Implement**

`team03-agent/harness/goldens.yaml`:

```yaml
# Playbook id -> figures its dry-run output must contain for score 1.0 (harness/tasks.py).
# Matched as plain substrings of the playbook's summary or of its context dumped as JSON,
# so write each figure the way it appears there: "5,72,073.68" as printed in a summary, or
# "572073.68" as a raw context value. Always quote figures.
# Only figures a local dry-run has reproduced belong here (spec §4.4; plan Task 7 prunes).
uc-23: ["5,72,073.68"]
uc-26: ["45,152.62"]
uc-41: ["4,91,099.27"]
uc-43: ["56,20,600"]
us-01: ["226,488.27"]
us-05: ["7,919.93"]
```

`team03-agent/harness/tasks.py`:

```python
"""Pure mapping from aptax routes and playbook runs to results.json tasks.

`passed` says the playbook ran cleanly; `score` says whether it reproduced its verified
worked example (goldens.yaml). Data drift on the server's fresh instance copy can lower a
score but never turns a task red. The only I/O here is `load_goldens`.
"""

import json
from pathlib import Path

import yaml

from harness.validate import EVIDENCE_MAX, MAX_TASKS

GOLDENS_PATH = Path(__file__).with_name("goldens.yaml")
INSTANCES = {"suryodaya": ("in", "gst"), "keystone": ("us", "sales_use_tax")}   # instance -> (tenant, regime)
ROUTING_FLOOR = {"in": 36, "us": 18}       # live playbooks routed on 2026-10-08
PARTIAL_SCORE = 0.5


def make_task(instance, key, title, passed, score, evidence) -> dict:
    return {"id": f"{instance}:{key}", "title": str(title), "passed": bool(passed),
            "score": float(score), "evidence": str(evidence)}


def is_other_regime(manifest, tax_regime) -> bool:
    regimes = tuple(manifest.tax_regimes)
    return "all" not in regimes and tax_regime not in regimes


def route_task(instance, route, tax_regime) -> dict | None:
    """A failed task for our own playbooks that cannot run; None for runnable or other-regime ones."""
    if route.action == "run" or is_other_regime(route.manifest, tax_regime):
        return None
    m = route.manifest
    task = make_task(instance, m.id, m.title, False, 0.0, f"{route.action}: {route.reason}")
    task["_golden"] = (False, False)
    return task


def golden_check(figures, outcome) -> list[tuple[str, bool]]:
    haystack = (outcome.summary or "") + "\n" + json.dumps(outcome.context or {}, default=str,
                                                           ensure_ascii=False)
    return [(f, f in haystack) for f in figures]


def playbook_task(instance, manifest, outcome, error, failed_delta, figures) -> dict:
    has_golden = bool(figures)
    if error or outcome is None:
        task = make_task(instance, manifest.id, manifest.title, False, 0.0, f"error: {error or 'no outcome'}")
    elif failed_delta:
        task = make_task(instance, manifest.id, manifest.title, False, 0.0,
                         f"{failed_delta} MCP call(s) failed during the run; {outcome.summary}")
    else:
        checks = golden_check(figures, outcome)
        exact = all(found for _, found in checks)
        # Goldens first: evidence is trimmed to 500 characters and they are what a reader checks.
        parts = [f"golden {f}: {'found' if found else 'NOT found'}" for f, found in checks]
        parts += [f"findings={len(outcome.findings)}", outcome.summary or "(no summary)"]
        task = make_task(instance, manifest.id, manifest.title, True, 1.0 if exact else PARTIAL_SCORE,
                         " · ".join(parts))
        task["_golden"] = (exact and has_golden, has_golden)
        return task
    task["_golden"] = (False, has_golden)
    return task


def not_run_task(instance, manifest, reason, has_golden=False) -> dict:
    task = make_task(instance, manifest.id, manifest.title, False, 0.0, reason)
    task["_golden"] = (False, has_golden)
    return task


def routing_floor_task(instance, tenant, runnable) -> dict:
    floor = ROUTING_FLOOR[tenant]
    return make_task(instance, "routing_floor", "At least the expected number of playbooks route to run",
                     runnable >= floor, 1.0 if runnable >= floor else 0.0,
                     f"{runnable} playbooks routed to run (floor {floor})")


def load_goldens(path: Path = GOLDENS_PATH) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: expected a mapping of playbook id to figures")
    goldens = {}
    for pid, figures in raw.items():
        if not isinstance(figures, list):
            raise ValueError(f"{path}: {pid} must map to a list of figures")
        goldens[str(pid)] = [str(f) for f in figures]
    return goldens


def finalize(instance, tasks) -> dict:
    out, seen = [], {}
    exact = with_golden = 0
    for raw in tasks:
        task = dict(raw)
        golden = task.pop("_golden", None)
        if golden:
            exact += golden[0]
            with_golden += golden[1]
        base = task["id"]
        seen[base] = seen.get(base, 0) + 1
        if seen[base] > 1:
            task["id"] = f"{base}#{seen[base]}"
        if len(task["evidence"]) > EVIDENCE_MAX:
            task["evidence"] = task["evidence"][:EVIDENCE_MAX - 1] + "…"
        out.append(task)
    if not out:
        out = [make_task(instance, "no_tasks", "The harness produced at least one task", False, 0.0,
                         "no tasks were collected")]
    dropped = max(0, len(out) - MAX_TASKS)
    out = out[:MAX_TASKS]
    passed = sum(t["passed"] for t in out)
    summary = f"{instance}: {passed}/{len(out)} passed · goldens {exact}/{with_golden} exact"
    if dropped:
        summary += f" · {dropped} task(s) dropped (limit {MAX_TASKS})"
    return {"tasks": out, "summary": summary}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_tasks.py -q`
Expected: `24 passed`.

- [ ] **Step 5: Commit** (outside the sandbox)

```bash
git add team03-agent/harness/tasks.py team03-agent/harness/goldens.yaml \
        team03-agent/tests_generated/harness_tests/fakes.py \
        team03-agent/tests_generated/harness_tests/test_tasks.py
git commit -m "Map playbook runs to harness tasks; seed goldens

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Harness entry point

**Files:**
- Create: `team03-agent/harness/__main__.py`
- Test: `team03-agent/tests_generated/harness_tests/test_main.py`

**Interfaces:**
- Consumes:
  - Everything in `harness.tasks` (Task 3).
  - `aptax.service.make_transport(tenant)` (Task 1).
  - `aptax.service.open_session(store, transport, *, tenant, trigger, mode, dry_run)` returns a session with `.ctx.tax_regime`, `.gateway.stats["failed"]`, `.runner.routes()`, `.runner.run_one(manifest)` and `.run_id`.
  - `aptax.store.Store(path)`, which has `.finish_run(run_id, status)` and `.close()`.
  - `aptax.config.TENANTS` and `aptax.config.DB_PATH`.
  - `run_one` returns a `PlaybookRun` with `.route`, `.outcome` and `.error`.
- Produces (`harness.__main__`):
  - `RESULTS_PATH: Path` (= `team03-agent/results.json`), `DEADLINE_SECONDS = 1020` and `REQUIRED_ENV`.
  - `Deps(make_transport, open_session, make_store, goldens={}, clock=time.monotonic, deadline_s=DEADLINE_SECONDS)` and `default_deps() -> Deps`.
  - `collect(env: MutableMapping, deps: Deps, out: list) -> str` returns the instance label. It also writes `{prefix}_BASE_URL` and `{prefix}_TOKEN` into `env`.
  - `write_results(doc, path)`
  - `main(env=None, deps=None, out_path=RESULTS_PATH) -> int`, which always returns 0.

- [ ] **Step 1: Write the failing tests**

`team03-agent/tests_generated/harness_tests/test_main.py`:

```python
"""LLM-generated, not graded. harness.__main__: orchestration, failure paths, results file."""

import itertools
import json

import pytest

from harness.__main__ import Deps, main
from harness.validate import validate
from harness_tests.fakes import (FakeManifest, FakeOutcome, FakeRoute, FakeRun, FakeSession,
                                 FakeStore, FakeTransport)

US01 = FakeManifest("us-01", "Period sales tax", ("sales_use_tax",))
US02 = FakeManifest("us-02", "Consumer use tax", ("sales_use_tax",))
US09 = FakeManifest("us-09", "Blocked one", ("sales_use_tax",))
UC05 = FakeManifest("uc-05", "Duplicate vendor payment", ("gst",))
ENV = {"AGENTSWITCH_BASE_URL": "https://class.example", "AGENTSWITCH_TOKEN": "tok",
       "AGENTSWITCH_INSTANCE": "keystone"}


def ok(summary):
    return lambda gw, m: FakeRun(FakeRoute(m), FakeOutcome(summary, findings=[1]))


def errors(message):
    return lambda gw, m: FakeRun(FakeRoute(m), None, message)


def fails_a_call(gw, m):
    gw.stats["failed"] += 1
    return FakeRun(FakeRoute(m), FakeOutcome("partial"))


def raises(gw, m):
    raise RuntimeError("store is locked")


def harness(tmp_path, routes, behaviours, *, env=None, transport=None, regime="sales_use_tax",
            goldens=None, clock=None, open_session=None, make_store=None):
    session = FakeSession(regime, routes, behaviours)
    store = FakeStore()
    calls = {}

    def fake_open_session(st, tr, **kwargs):
        calls.update(kwargs)
        return session

    deps = Deps(make_transport=lambda tenant: calls.setdefault("tenant", tenant) and (transport or FakeTransport()),
                open_session=open_session or fake_open_session,
                make_store=make_store or (lambda: store),
                goldens=goldens or {}, clock=clock or (lambda: 0.0), deadline_s=100.0)
    env = dict(ENV if env is None else env)
    out = tmp_path / "results.json"
    assert main(env, deps, out) == 0
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert validate(doc) == []
    return doc, {t["id"]: t for t in doc["tasks"]}, session, store, calls, env


def test_keystone_run(tmp_path):
    routes = [FakeRoute(US01), FakeRoute(US02), FakeRoute(US09, "blocked", "blocked by N14"),
              FakeRoute(UC05, "skip", "tax_regime sales_use_tax not in ['gst']")]
    behaviours = {"us-01": ok("$226,488.27 YTD"), "us-02": errors("KeyError: 'taxes'")}
    doc, by_id, session, store, calls, env = harness(tmp_path, routes, behaviours,
                                                     goldens={"us-01": ["226,488.27"]})
    assert calls["tenant"] == "us" and calls["dry_run"] is True and calls["mode"] == "pipeline"
    assert env["US_AGENTSWITCH_BASE_URL"] == "https://class.example" and env["US_AGENTSWITCH_TOKEN"] == "tok"
    assert by_id["keystone:mcp_tools_list"]["passed"] is True
    assert by_id["keystone:whoami"]["evidence"] == "user=team03@theschoolofai.in"
    assert by_id["keystone:locale_matches_instance"]["passed"] is True
    assert by_id["keystone:us-01"]["score"] == 1.0
    assert by_id["keystone:us-02"]["passed"] is False
    assert by_id["keystone:us-09"]["evidence"] == "blocked: blocked by N14"
    assert "keystone:uc-05" not in by_id
    assert by_id["keystone:routing_floor"]["passed"] is False      # 2 < 18
    assert doc["summary"] == "keystone: 4/7 passed · goldens 1/1 exact"
    assert store.finished == [("run-1", "failed")] and store.closed


def test_locale_mismatch_fails(tmp_path):
    _, by_id, *_ = harness(tmp_path, [], {}, regime="gst")
    assert by_id["keystone:locale_matches_instance"]["passed"] is False
    assert by_id["keystone:locale_matches_instance"]["evidence"] == "tax_regime=gst (expected sales_use_tax)"


def test_failed_mcp_call_fails_the_playbook(tmp_path):
    _, by_id, *_ = harness(tmp_path, [FakeRoute(US01)], {"us-01": fails_a_call})
    assert by_id["keystone:us-01"]["passed"] is False
    assert by_id["keystone:us-01"]["evidence"].startswith("1 MCP call(s) failed")


def test_exception_from_run_one_fails_only_that_playbook(tmp_path):
    _, by_id, session, *_ = harness(tmp_path, [FakeRoute(US01), FakeRoute(US02)],
                                    {"us-01": raises, "us-02": ok("fine")})
    assert by_id["keystone:us-01"]["evidence"] == "error: RuntimeError: store is locked"
    assert by_id["keystone:us-02"]["passed"] is True
    assert session.runner.ran == ["us-01", "us-02"]


def test_deadline_marks_remaining_playbooks_not_run(tmp_path):
    clock = itertools.chain([0.0, 0.0], itertools.repeat(10_000.0)).__next__
    _, by_id, session, *_ = harness(tmp_path, [FakeRoute(US01), FakeRoute(US02)],
                                    {"us-01": ok("a"), "us-02": ok("b")}, clock=clock)
    assert by_id["keystone:us-01"]["passed"] is True
    assert by_id["keystone:us-02"]["evidence"] == "not run: harness time budget exhausted"
    assert session.runner.ran == ["us-01"]


def test_missing_env_gives_one_failed_task(tmp_path):
    doc, by_id, *_ = harness(tmp_path, [], {}, env={"AGENTSWITCH_INSTANCE": "keystone"})
    assert list(by_id) == ["keystone:environment"]
    assert by_id["keystone:environment"]["evidence"] == "missing: AGENTSWITCH_BASE_URL, AGENTSWITCH_TOKEN"


def test_unknown_instance_gives_one_failed_task(tmp_path):
    _, by_id, *_ = harness(tmp_path, [], {}, env={**ENV, "AGENTSWITCH_INSTANCE": "atlantis"})
    assert list(by_id) == ["atlantis:environment"]
    assert "unknown AGENTSWITCH_INSTANCE 'atlantis'" in by_id["atlantis:environment"]["evidence"]


def test_tools_list_failure_skips_playbooks(tmp_path):
    def never(*a, **k):
        raise AssertionError("open_session must not be called")
    _, by_id, *_ = harness(tmp_path, [], {}, transport=FakeTransport(tools_error=ConnectionError("down")),
                           open_session=never)
    assert by_id["keystone:mcp_tools_list"]["passed"] is False
    assert by_id["keystone:playbooks_skipped"]["evidence"] == "not run: MCP tools/list failed"


def test_open_session_failure_skips_playbooks(tmp_path):
    def broken(*a, **k):
        raise RuntimeError("locale 500")
    _, by_id, *_ = harness(tmp_path, [], {}, open_session=broken)
    assert by_id["keystone:locale_matches_instance"]["passed"] is False
    assert "locale 500" in by_id["keystone:playbooks_skipped"]["evidence"]


def test_crash_keeps_collected_tasks_and_writes_file(tmp_path):
    def no_store():
        raise OSError("disk full")
    doc, by_id, *_ = harness(tmp_path, [], {}, make_store=no_store)
    assert by_id["keystone:mcp_tools_list"]["passed"] is True
    assert by_id["keystone:harness_crashed"]["passed"] is False
    assert "disk full" in by_id["keystone:harness_crashed"]["evidence"]


def test_env_values_are_stripped_and_mapped_to_the_tenant_prefix(tmp_path):
    env = {"AGENTSWITCH_BASE_URL": " https://agentswitch.example/ \n", "AGENTSWITCH_TOKEN": " tok\n",
           "AGENTSWITCH_INSTANCE": " suryodaya "}
    _, by_id, _, _, calls, env_after = harness(tmp_path, [], {}, env=env, regime="gst")
    assert calls["tenant"] == "in"
    assert env_after["AGENTSWITCH_BASE_URL"] == "https://agentswitch.example/"
    assert env_after["AGENTSWITCH_TOKEN"] == "tok"
    assert "suryodaya:locale_matches_instance" in by_id
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_main.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.__main__'`.

- [ ] **Step 3: Implement**

`team03-agent/harness/__main__.py`:

```python
"""AgentSwitch server harness: `python -m harness` (Release 8.1 "Our harness").

The server sets AGENTSWITCH_BASE_URL, AGENTSWITCH_TOKEN and AGENTSWITCH_INSTANCE, runs this
once per instance against a fresh copy of it, and reads results.json. We run every live
aptax playbook in dry-run and report one task per playbook (harness/tasks.py).

results.json is always written, and the exit code is 0 whenever it was: pass/fail lives
in the file. Design: docs/superpowers/specs/2026-10-12-agentswitch-harness-design.md
"""

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from aptax.config import TENANTS
from harness import tasks as T

RESULTS_PATH = Path(__file__).resolve().parents[1] / "results.json"   # team03-agent/results.json
DEADLINE_SECONDS = 17 * 60          # the server stops the run at timeout_minutes = 20
REQUIRED_ENV = ("AGENTSWITCH_BASE_URL", "AGENTSWITCH_TOKEN", "AGENTSWITCH_INSTANCE")
ENV_TITLE = "The server's environment variables are set"
TOOLS_TITLE = "MCP tools/list works with the seat token"
LOCALE_TITLE = "The tenant's locale matches the instance"
SKIPPED_TITLE = "Playbooks ran"


@dataclass
class Deps:
    make_transport: Callable
    open_session: Callable
    make_store: Callable
    goldens: dict = field(default_factory=dict)
    clock: Callable = time.monotonic
    deadline_s: float = DEADLINE_SECONDS


def default_deps() -> Deps:
    from aptax import service
    from aptax.config import DB_PATH
    from aptax.store import Store
    return Deps(make_transport=service.make_transport, open_session=service.open_session,
                make_store=lambda: Store(DB_PATH), goldens=T.load_goldens())


def _user(me) -> str:
    if not isinstance(me, dict):
        return "?"
    user = me.get("user") if isinstance(me.get("user"), dict) else {}
    return str(me.get("email") or user.get("email") or "?")


def collect(env, deps: Deps, out: list) -> str:
    """Append tasks to `out` as they are decided, so a crash keeps what was collected."""
    instance = (env.get("AGENTSWITCH_INSTANCE") or "").strip()
    missing = [k for k in REQUIRED_ENV if not (env.get(k) or "").strip()]
    if missing:
        label = instance or "harness"
        out.append(T.make_task(label, "environment", ENV_TITLE, False, 0.0, "missing: " + ", ".join(missing)))
        return label
    if instance not in T.INSTANCES:
        out.append(T.make_task(instance, "environment", ENV_TITLE, False, 0.0,
                               f"unknown AGENTSWITCH_INSTANCE {instance!r}; expected one of {sorted(T.INSTANCES)}"))
        return instance
    tenant, regime = T.INSTANCES[instance]
    prefix = TENANTS[tenant]
    env[f"{prefix}_BASE_URL"] = env["AGENTSWITCH_BASE_URL"].strip()
    env[f"{prefix}_TOKEN"] = env["AGENTSWITCH_TOKEN"].strip()
    start = deps.clock()

    transport = deps.make_transport(tenant)
    try:
        tools = transport.tools_list()
    except Exception as exc:  # noqa: BLE001 — reported as a task
        out.append(T.make_task(instance, "mcp_tools_list", TOOLS_TITLE, False, 0.0, repr(exc)))
        out.append(T.make_task(instance, "playbooks_skipped", SKIPPED_TITLE, False, 0.0,
                               "not run: MCP tools/list failed"))
        return instance
    out.append(T.make_task(instance, "mcp_tools_list", TOOLS_TITLE, len(tools) > 0,
                           1.0 if tools else 0.0, f"{len(tools)} tools"))
    try:
        me = transport.rest("GET", "/api/auth/me")
        out.append(T.make_task(instance, "whoami", "The seat token resolves to a user", bool(me),
                               1.0 if me else 0.0, f"user={_user(me)}"))
    except Exception as exc:  # noqa: BLE001
        out.append(T.make_task(instance, "whoami", "The seat token resolves to a user", False, 0.0, repr(exc)))

    store = deps.make_store()
    try:
        _run_playbooks(instance, tenant, regime, transport, store, deps, start, out)
    finally:
        store.close()
    return instance


def _run_playbooks(instance, tenant, regime, transport, store, deps, start, out) -> None:
    try:
        session = deps.open_session(store, transport, tenant=tenant, trigger="on_request",
                                    mode="pipeline", dry_run=True)
    except Exception as exc:  # noqa: BLE001 — no run context, no playbooks
        out.append(T.make_task(instance, "locale_matches_instance", LOCALE_TITLE, False, 0.0, repr(exc)))
        out.append(T.make_task(instance, "playbooks_skipped", SKIPPED_TITLE, False, 0.0,
                               f"not run: no run context ({exc})"))
        return
    got = session.ctx.tax_regime
    out.append(T.make_task(instance, "locale_matches_instance", LOCALE_TITLE, got == regime,
                           1.0 if got == regime else 0.0, f"tax_regime={got} (expected {regime})"))
    routes = session.runner.routes()
    runnable = [r for r in routes if r.action == "run"]
    for r in routes:
        task = T.route_task(instance, r, got)
        if task:
            out.append(task)
    out.append(T.routing_floor_task(instance, tenant, len(runnable)))

    status = "completed"
    for r in runnable:
        figures = deps.goldens.get(r.manifest.id, [])
        if deps.clock() - start > deps.deadline_s:
            out.append(T.not_run_task(instance, r.manifest, "not run: harness time budget exhausted", bool(figures)))
            status = "failed"
            continue
        before = session.gateway.stats.get("failed", 0)
        try:
            run = session.runner.run_one(r.manifest)
            outcome = run.outcome
            error = run.error or (None if outcome is not None
                                  else f"not run: {run.route.action} {run.route.reason}".strip())
        except Exception as exc:  # noqa: BLE001 — one playbook's failure never stops the rest
            outcome, error = None, f"{type(exc).__name__}: {exc}"
        delta = session.gateway.stats.get("failed", 0) - before
        task = T.playbook_task(instance, r.manifest, outcome, error, delta, figures)
        if not task["passed"]:
            status = "failed"
        out.append(task)
    store.finish_run(session.run_id, status)


def write_results(doc, path: Path) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def main(env=None, deps: Deps | None = None, out_path: Path = RESULTS_PATH) -> int:
    env = os.environ if env is None else env
    tasks: list = []
    instance = (env.get("AGENTSWITCH_INSTANCE") or "").strip() or "harness"
    try:
        instance = collect(env, deps or default_deps(), tasks)
    except Exception:  # noqa: BLE001 — whatever happens, the server still gets a results file
        tasks.append(T.make_task(instance, "harness_crashed", "The harness finished without crashing", False, 0.0,
                                 traceback.format_exc()[-T.EVIDENCE_MAX:]))
    finally:
        doc = T.finalize(instance, tasks)
        write_results(doc, out_path)
        for t in doc["tasks"]:
            print(f"[{'PASS' if t['passed'] else 'FAIL'}] {t['id']}: {t['evidence'][:200]}", flush=True)
        print(doc["summary"], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

The tests' `make_transport` lambda records the tenant with `calls.setdefault("tenant", tenant) and transport`. That works because `setdefault` returns the tenant string, which is always truthy.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests -q`
Expected: all pass (`11` in `test_main.py`; `59` in total across the four files).

- [ ] **Step 5: Commit** (outside the sandbox)

```bash
git add team03-agent/harness/__main__.py team03-agent/tests_generated/harness_tests/test_main.py
git commit -m "Add harness entry point: run live playbooks, always write results.json

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Server config, gitignore, README

**Files:**
- Create: `agentswitch-harness.toml` (git root)
- Modify: `.gitignore` (git root, append)
- Create: `team03-agent/harness/README.md`
- Test: `team03-agent/tests_generated/harness_tests/test_toml.py`

**Interfaces:**
- Consumes: `harness.__main__.RESULTS_PATH` and `DEADLINE_SECONDS` (Task 4), and `harness.tasks.INSTANCES` (Task 3).

- [ ] **Step 1: Write the failing tests**

`team03-agent/tests_generated/harness_tests/test_toml.py`:

```python
"""LLM-generated, not graded. agentswitch-harness.toml agrees with the harness code."""

import subprocess
import sys
import tomllib
from pathlib import Path

import harness.__main__ as hm
from harness import tasks as T

AGENT_DIR = Path(__file__).resolve().parents[2]
GIT_ROOT = AGENT_DIR.parent
CFG = tomllib.loads((GIT_ROOT / "agentswitch-harness.toml").read_text(encoding="utf-8"))


def test_toml_values():
    assert CFG["install"] == "pip install -r team03-agent/requirements.txt"
    assert CFG["run"] == "cd team03-agent && python -m harness"
    assert CFG["instances"] == ["suryodaya", "keystone"]
    assert CFG["timeout_minutes"] == 20
    assert set(CFG["instances"]) <= set(T.INSTANCES)
    assert hm.DEADLINE_SECONDS < CFG["timeout_minutes"] * 60


def test_results_path_matches_toml():
    assert (GIT_ROOT / CFG["results"]).resolve() == hm.RESULTS_PATH


def test_requirements_cover_harness_imports():
    reqs = (AGENT_DIR / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "requests" in reqs and "pyyaml" in reqs


def test_results_file_is_gitignored():
    proc = subprocess.run(["git", "check-ignore", "-q", "team03-agent/results.json"], cwd=GIT_ROOT)
    assert proc.returncode == 0


def test_runs_from_another_cwd_and_writes_the_toml_path(tmp_path):
    """No server env vars → one failed task, written where the toml says even from another cwd."""
    target = GIT_ROOT / CFG["results"]
    target.unlink(missing_ok=True)
    proc = subprocess.run([sys.executable, "-m", "harness"], cwd=tmp_path,
                          env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(AGENT_DIR)},
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "harness:environment" in proc.stdout
    assert target.exists() and not (tmp_path / "results.json").exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_toml.py -q`
Expected: FAIL during collection with `FileNotFoundError: … agentswitch-harness.toml`.

- [ ] **Step 3: Implement**

`agentswitch-harness.toml` (git root):

```toml
# AgentSwitch server harness (Release 8.1). See team03-agent/harness/README.md.
install = "pip install -r team03-agent/requirements.txt"
run     = "cd team03-agent && python -m harness"
results = "team03-agent/results.json"
instances = ["suryodaya", "keystone"]
timeout_minutes = 20
```

Append to the git-root `.gitignore`:

```gitignore

# AgentSwitch harness output (python -m harness): live business data, regenerated each run.
team03-agent/results.json
team03-agent/results.json.tmp
```

`team03-agent/harness/README.md`:

````markdown
# harness — AgentSwitch server runs

`agentswitch-harness.toml` (git root) tells the AgentSwitch server how to run us.
"Our harness → Submit for a run" checks out the saved commit and runs `install`. It then
runs `cd team03-agent && python -m harness` once per instance (suryodaya, keystone)
against a fresh copy of that instance, and reads `team03-agent/results.json`. You get one
run every 3 days.

The harness runs every live aptax playbook in **dry-run**. Each playbook becomes one task:
`passed` means it ran with no error and no failed MCP call, and `score` is 1.0 when it
reproduced its figure in `goldens.yaml` (0.5 when it didn't). Blocked and spec-only
playbooks for the instance's own regime show up as failed tasks with the router's reason.
Design: `docs/superpowers/specs/2026-10-12-agentswitch-harness-design.md`.

## Run it locally (same env vars as the server)

```bash
source team03-agent/scripts/harness_env.sh suryodaya      # or keystone; reads team03-agent/.env
cd team03-agent && python -m harness && python -m harness.validate results.json
```

Use a fresh shell afterwards for other `aptax` commands: the script points `AGENTSWITCH_*`
at the instance you chose.
````

- [ ] **Step 4: Run the tests to verify they pass**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_toml.py -q`
Expected: `5 passed`. `test_runs_from_another_cwd…` runs from a temp dir with only `PATH`/`PYTHONPATH` set, so it can't reach the network or pick up a token. It replaces `team03-agent/results.json`, which is gitignored.

- [ ] **Step 5: Commit** (outside the sandbox)

```bash
git add agentswitch-harness.toml .gitignore team03-agent/harness/README.md \
        team03-agent/tests_generated/harness_tests/test_toml.py
git commit -m "Add agentswitch-harness.toml and harness README

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Local token helper `harness_env.sh`

**Files:**
- Create: `team03-agent/scripts/harness_env.sh`
- Test: `team03-agent/tests_generated/harness_tests/test_harness_env.py`

**Interfaces:**
- Produces: `source scripts/harness_env.sh suryodaya|keystone`, which exports `AGENTSWITCH_BASE_URL`, `AGENTSWITCH_TOKEN` and `AGENTSWITCH_INSTANCE`.
  - It returns 0 on success, 1 when credentials are missing or login fails, and 2 on bad usage.
  - Run without `source`, it exits 1.
  - `AGENTSWITCH_ENV_FILE` overrides where it looks for `.env`.

- [ ] **Step 1: Write the failing tests**

`team03-agent/tests_generated/harness_tests/test_harness_env.py`:

```python
"""LLM-generated, not graded. scripts/harness_env.sh against a fake curl (no network)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parents[2]
TOKEN = "abcdefgh12345678"
PASSWORD = 'pa"ss $HOME word'
FAKE_CURL = r'''#!/bin/bash
printf '%s\n' "$*" >> "$FAKE_LOG"
case "$*" in
  *api/auth/login*) cat > "$FAKE_BODY"; printf '%s\n%s' "$FAKE_LOGIN_BODY" "${FAKE_LOGIN_CODE:-200}" ;;
  *api/auth/me*) cat > /dev/null; printf '%s\n%s' '{"email": "team03@theschoolofai.in"}' "${FAKE_ME_CODE:-200}" ;;
  *) echo "unexpected curl call: $*" >&2; exit 7 ;;
esac
'''
PROBE = ('source scripts/harness_env.sh "$@"; rc=$?; '
         'printf "RC=%s\\nURL=%s\\nTOKEN=%s\\nINSTANCE=%s\\n" "$rc" "${AGENTSWITCH_BASE_URL:-}" '
         '"${AGENTSWITCH_TOKEN:-}" "${AGENTSWITCH_INSTANCE:-}"')
PROBE_KEYS = {"RC", "URL", "TOKEN", "INSTANCE"}


@pytest.fixture
def fake(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(FAKE_CURL)
    curl.chmod(0o755)
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "HOME": str(tmp_path),
           "FAKE_LOG": str(tmp_path / "argv.log"), "FAKE_BODY": str(tmp_path / "body.json"),
           "FAKE_LOGIN_BODY": json.dumps({"token": TOKEN}),
           "AGENTSWITCH_ENV_FILE": str(tmp_path / "no.env")}
    return tmp_path, env


def source(env, *args, shell="bash"):
    proc = subprocess.run([shell, "-c", PROBE, "probe", *args], cwd=AGENT_DIR, env=env,
                          capture_output=True, text=True, timeout=30)
    vals = {}
    script_lines = []
    for line in proc.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in PROBE_KEYS:
            vals[key] = value
        else:
            script_lines.append(line)
    return proc, vals, "\n".join(script_lines)


def test_success_keystone_exports_and_hides_secrets(fake):
    tmp, env = fake
    env.update(US_AGENTSWITCH_EMAIL="team03@theschoolofai.in", US_AGENTSWITCH_PASSWORD=PASSWORD)
    proc, vals, own_out = source(env, "keystone")
    assert vals == {"RC": "0", "URL": "https://class.agentswitch.theschoolofai.in", "TOKEN": TOKEN,
                    "INSTANCE": "keystone"}, proc.stderr
    assert json.loads((tmp / "body.json").read_text()) == {"email": "team03@theschoolofai.in",
                                                            "password": PASSWORD}
    assert PASSWORD not in (tmp / "argv.log").read_text()
    assert TOKEN not in (tmp / "argv.log").read_text()
    assert "instance=keystone user=team03@theschoolofai.in token=abcdefgh…" in own_out
    assert TOKEN not in own_out and TOKEN not in proc.stderr
    assert PASSWORD not in proc.stdout + proc.stderr


def test_suryodaya_uses_the_india_prefix_and_url(fake):
    _, env = fake
    env.update(AGENTSWITCH_EMAIL="a@b", AGENTSWITCH_PASSWORD="pw",
               US_AGENTSWITCH_EMAIL="x@y", US_AGENTSWITCH_PASSWORD="wrong")
    _, vals, _ = source(env, "suryodaya")
    assert vals["RC"] == "0" and vals["URL"] == "https://agentswitch.theschoolofai.in"


def test_reads_dotenv_when_env_is_unset(fake):
    tmp, env = fake
    dotenv = tmp / "team.env"
    dotenv.write_text('AGENTSWITCH_PASSWORD=india\nUS_AGENTSWITCH_EMAIL=team03@theschoolofai.in\n'
                      'US_AGENTSWITCH_PASSWORD="from file"\n')
    env["AGENTSWITCH_ENV_FILE"] = str(dotenv)
    _, vals, _ = source(env, "keystone")
    assert vals["RC"] == "0"
    assert json.loads((tmp / "body.json").read_text())["password"] == "from file"


def test_environment_beats_dotenv(fake):
    tmp, env = fake
    dotenv = tmp / "team.env"
    dotenv.write_text("US_AGENTSWITCH_EMAIL=file@x\nUS_AGENTSWITCH_PASSWORD=file\n")
    env.update(AGENTSWITCH_ENV_FILE=str(dotenv), US_AGENTSWITCH_EMAIL="env@x", US_AGENTSWITCH_PASSWORD="env")
    source(env, "keystone")
    assert json.loads((tmp / "body.json").read_text()) == {"email": "env@x", "password": "env"}


def test_login_failure_exports_nothing(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD="bad",
               FAKE_LOGIN_CODE="401", FAKE_LOGIN_BODY='{"detail": "Invalid credentials"}')
    proc, vals, _ = source(env, "keystone")
    assert vals == {"RC": "1", "URL": "", "TOKEN": "", "INSTANCE": ""}
    assert "HTTP 401" in proc.stderr and "Invalid credentials" in proc.stderr


def test_token_check_failure_exports_nothing(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD="pw", FAKE_ME_CODE="401")
    proc, vals, _ = source(env, "keystone")
    assert vals["RC"] == "1" and vals["TOKEN"] == ""
    assert "token check failed: HTTP 401" in proc.stderr


def test_missing_credentials(fake):
    tmp, env = fake
    proc, vals, _ = source(env, "keystone")
    assert vals["RC"] == "1"
    assert "US_AGENTSWITCH_EMAIL" in proc.stderr
    assert not (tmp / "argv.log").exists()


@pytest.mark.parametrize("args", [(), ("atlantis",)])
def test_bad_instance(fake, args):
    _, env = fake
    proc, vals, _ = source(env, *args)
    assert vals["RC"] == "2" and "usage" in proc.stderr


def test_refuses_to_run_unsourced(fake):
    _, env = fake
    proc = subprocess.run(["bash", "scripts/harness_env.sh", "keystone"], cwd=AGENT_DIR, env=env,
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 1 and "source" in proc.stderr


def test_warns_that_the_shell_now_targets_the_instance(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD="pw")
    proc, _, _ = source(env, "keystone")
    assert "AGENTSWITCH_* in this shell now target keystone" in proc.stderr


@pytest.mark.skipif(shutil.which("zsh") is None, reason="zsh not installed")
def test_works_in_zsh(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD=PASSWORD)
    proc, vals, _ = source(env, "keystone", shell="zsh")
    assert vals["RC"] == "0" and vals["TOKEN"] == TOKEN, proc.stderr
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_harness_env.py -q`
Expected: FAIL. Each test sees `RC=1` with "scripts/harness_env.sh: No such file or directory" on stderr, and `test_refuses_to_run_unsourced` gets returncode 127.

- [ ] **Step 3: Implement**

`team03-agent/scripts/harness_env.sh`:

```bash
# shellcheck shell=bash
# Recreate the AgentSwitch harness runner's environment on a laptop (local runs only).
#
#   source team03-agent/scripts/harness_env.sh suryodaya   # or keystone
#   cd team03-agent && python -m harness
#
# Logs in with the seat's email/password -- from the environment, else from
# team03-agent/.env (or the file in AGENTSWITCH_ENV_FILE) -- and exports what the server
# gives a run: AGENTSWITCH_BASE_URL, AGENTSWITCH_TOKEN, AGENTSWITCH_INSTANCE.
# The password reaches curl on stdin, never on a command line; the token is never printed
# in full or written to disk. Works in bash and zsh.

_ase_sourced=0
if [ -n "${ZSH_VERSION:-}" ]; then
  case "${ZSH_EVAL_CONTEXT:-}" in *:file*) _ase_sourced=1 ;; esac
elif [ -n "${BASH_VERSION:-}" ]; then
  [ "${BASH_SOURCE[0]}" != "$0" ] && _ase_sourced=1
fi
if [ "$_ase_sourced" != 1 ]; then
  echo "usage: source $0 suryodaya|keystone  (use 'source': run directly, the exports would be lost)" >&2
  exit 1
fi
unset _ase_sourced

_ase_dotenv() {  # _ase_dotenv KEY FILE -> KEY's value in FILE, surrounding quotes removed
  local v
  { [ -n "$2" ] && [ -f "$2" ]; } || return 0
  v=$(sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$2" | tail -n 1)
  v=${v%$'\r'}
  case "$v" in
    \"*\") v=${v#\"}; v=${v%\"} ;;
    \'*\') v=${v#\'}; v=${v%\'} ;;
  esac
  printf '%s' "$v"
}

_ase_json_field() {  # _ase_json_field KEY... < json -> first non-empty KEY at top level or under "user"
  python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
d = d if isinstance(d, dict) else {}
u = d.get("user") if isinstance(d.get("user"), dict) else {}
for k in sys.argv[1:]:
    v = d.get(k) or u.get(k)
    if v:
        print(v)
        break
' "$@"
}

_ase_main() {
  local instance="${1:-}" url prefix env_file email password resp code body token user
  case "$instance" in
    suryodaya) url="https://agentswitch.theschoolofai.in"; prefix="AGENTSWITCH" ;;
    keystone)  url="https://class.agentswitch.theschoolofai.in"; prefix="US_AGENTSWITCH" ;;
    *) echo "usage: source scripts/harness_env.sh suryodaya|keystone" >&2; return 2 ;;
  esac

  env_file="${AGENTSWITCH_ENV_FILE:-}"
  if [ -z "$env_file" ]; then
    if [ -f team03-agent/.env ]; then env_file="team03-agent/.env"; elif [ -f .env ]; then env_file=".env"; fi
  fi
  email=$(printenv "${prefix}_EMAIL")
  password=$(printenv "${prefix}_PASSWORD")
  [ -n "$email" ] || email=$(_ase_dotenv "${prefix}_EMAIL" "$env_file")
  [ -n "$password" ] || password=$(_ase_dotenv "${prefix}_PASSWORD" "$env_file")
  if [ -z "$email" ] || [ -z "$password" ]; then
    echo "set ${prefix}_EMAIL and ${prefix}_PASSWORD (in the environment or team03-agent/.env)" >&2
    return 1
  fi

  resp=$(AS_EMAIL="$email" AS_PASSWORD="$password" python3 -c \
           'import json, os; print(json.dumps({"email": os.environ["AS_EMAIL"], "password": os.environ["AS_PASSWORD"]}))' \
         | curl -sS -X POST "$url/api/auth/login" -H 'Content-Type: application/json' \
             --data-binary @- -w '\n%{http_code}') \
    || { echo "login request to $url failed" >&2; return 1; }
  code=${resp##*$'\n'}
  body=${resp%$'\n'*}
  if [ "$code" != "200" ]; then
    echo "login failed: HTTP $code $(printf '%s' "$body" | _ase_json_field detail error message)" >&2
    return 1
  fi
  token=$(printf '%s' "$body" | _ase_json_field token)
  if [ -z "$token" ]; then
    echo "login response has no token" >&2
    return 1
  fi

  resp=$(printf 'Authorization: Bearer %s\n' "$token" | curl -sS "$url/api/auth/me" -H @- -w '\n%{http_code}') \
    || { echo "token check against $url failed" >&2; return 1; }
  code=${resp##*$'\n'}
  body=${resp%$'\n'*}
  if [ "$code" != "200" ]; then
    echo "token check failed: HTTP $code" >&2
    return 1
  fi
  user=$(printf '%s' "$body" | _ase_json_field email)

  export AGENTSWITCH_BASE_URL="$url" AGENTSWITCH_TOKEN="$token" AGENTSWITCH_INSTANCE="$instance"
  echo "instance=$instance user=${user:-?} token=${token:0:8}…"
  echo "note: AGENTSWITCH_* in this shell now target $instance; use a fresh shell for other aptax commands" >&2
}

_ase_main "$@"
_ase_rc=$?
unset -f _ase_main _ase_dotenv _ase_json_field
return "$_ase_rc"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `../.venv/bin/python -m pytest tests_generated/harness_tests/test_harness_env.py -q`
Expected: `12 passed` (11 when zsh is missing, with 1 skipped).

- [ ] **Step 5: Commit** (outside the sandbox)

```bash
git add team03-agent/scripts/harness_env.sh team03-agent/tests_generated/harness_tests/test_harness_env.py
git commit -m "Add harness_env.sh: log in and export the harness runner's env vars

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Live verification and golden pruning (before the official submit)

This task needs the seat credentials in `team03-agent/.env` and network access to both AgentSwitch hosts. Everything runs in dry-run. It produces evidence and a pruned `goldens.yaml`, not new code.

**Files:**
- Modify: `team03-agent/harness/goldens.yaml` (prune or correct figures)

- [ ] **Step 1: Full offline suite**

Run (from `team03-agent/`): `../.venv/bin/python -m pytest -q && ../.venv/bin/python -m pytest tests_generated -q`
Expected: everything passes.

- [ ] **Step 2: Live run, Suryodaya** (from the git root)

```bash
source team03-agent/scripts/harness_env.sh suryodaya
cd team03-agent && time ../.venv/bin/python -m harness && ../.venv/bin/python -m harness.validate results.json \
  && cp results.json "$TMPDIR/results-suryodaya.json"; cd ..
```

Expected:
- the `instance=suryodaya …` line;
- one `[PASS]`/`[FAIL]` line per task;
- `real` well under 17m;
- `results.json: OK (N tasks)`;
- `suryodaya:routing_floor` PASS and `suryodaya:locale_matches_instance` PASS.

- [ ] **Step 3: Live run, Keystone** (in a fresh shell, from the git root)

```bash
source team03-agent/scripts/harness_env.sh keystone
cd team03-agent && time ../.venv/bin/python -m harness && ../.venv/bin/python -m harness.validate results.json \
  && cp results.json "$TMPDIR/results-keystone.json"; cd ..
```

Expected: the same checks for keystone.

- [ ] **Step 4: Resolve every score of 0.5 and every unexpected FAIL**

```bash
python3 -c 'import json,sys
for p in sys.argv[1:]:
    for t in json.load(open(p))["tasks"]:
        if not t["passed"] or t["score"] < 1: print(t["id"], t["score"], t["evidence"][:160])' \
  "$TMPDIR/results-suryodaya.json" "$TMPDIR/results-keystone.json"
```

For each golden that shows `NOT found`, read the playbook's summary in the evidence. Then do one of two things:
- If the playbook prints the figure in a different format (for example without the ₹ grouping), change the figure in `goldens.yaml` to the printed form.
- If the value itself has drifted, or the figure is for a period the playbook doesn't report today (the `as_of` is the tenant's today), **remove that entry**. Spec §4.4 says only reproduced figures stay.

A FAIL on a playbook that ran cleanly in earlier dry-runs counts as a bug. Use superpowers:systematic-debugging; don't edit the golden to hide it.

- [ ] **Step 5: Re-run whichever instance had a goldens change** (Step 2 or 3) and confirm every remaining golden shows `found`.

- [ ] **Step 6: Fresh-checkout simulation** (the install step uses PyPI)

```bash
rm -rf "$TMPDIR/hv" && python3 -m venv "$TMPDIR/hv"
"$TMPDIR/hv/bin/pip" install -q -r team03-agent/requirements.txt
source team03-agent/scripts/harness_env.sh keystone
PATH="$TMPDIR/hv/bin:$PATH" sh -c 'cd team03-agent && python -m harness && python -m harness.validate results.json' | tail -2
```

Expected: the summary line, then `OK`. This proves the toml's `install` and `run` work from the git root in a clean environment.

- [ ] **Step 7: Commit the pruned goldens** (outside the sandbox)

```bash
git add team03-agent/harness/goldens.yaml
git commit -m "Harness goldens: keep only figures reproduced by a live dry-run

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Hand over to the user for the official submit**

Report:
- each instance's summary line and runtime;
- the goldens that were kept and the ones removed;
- any FAILs, with their reasons.

The user then pushes the branch, saves it in "Our harness" and clicks Submit. Pushing and submitting are outward-facing actions, so wait for the user to ask.
