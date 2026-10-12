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

STARTED = time.monotonic()          # the server's clock starts with the process, not with collect()
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
    started: float | None = None    # None: count from collect()


def default_deps() -> Deps:
    from aptax import service
    from aptax.config import DB_PATH
    from aptax.store import Store
    return Deps(make_transport=service.make_transport, open_session=service.open_session,
                make_store=lambda: Store(DB_PATH), goldens=T.load_goldens(), started=STARTED)


def _user(me) -> str:
    if not isinstance(me, dict):
        return "?"
    user = me.get("user") if isinstance(me.get("user"), dict) else {}
    return str(me.get("email") or user.get("email") or "?")


def collect(env, deps: Deps, out: list, checkpoint: Callable = lambda: None) -> str:
    """Append tasks to `out` as they are decided, so a crash keeps what was collected.

    `checkpoint()` runs after each playbook, so a run the server kills still leaves a file.
    """
    instance = (env.get("AGENTSWITCH_INSTANCE") or "").strip().lower()
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
    start = deps.started if deps.started is not None else deps.clock()

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
        _run_playbooks(instance, tenant, regime, transport, store, deps, start, out, checkpoint)
    finally:
        store.close()
    return instance


def _run_playbooks(instance, tenant, regime, transport, store, deps, start, out, checkpoint) -> None:
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
    checkpoint()

    status = "completed"
    for r in runnable:
        figures = deps.goldens.get(r.manifest.id, [])
        if deps.clock() - start > deps.deadline_s:
            out.append(T.not_run_task(instance, r.manifest, "not run: harness time budget exhausted", bool(figures)))
            status = "failed"
            continue
        before = session.gateway.stats.get("failed", 0)
        try:  # one playbook's failure — running it or scoring it — never stops the rest
            run = session.runner.run_one(r.manifest)
            outcome = run.outcome
            error = run.error or (None if outcome is not None
                                  else f"not run: {run.route.action} {run.route.reason}".strip())
            task = T.playbook_task(instance, r.manifest, outcome, error,
                                   session.gateway.stats.get("failed", 0) - before, figures)
        except Exception as exc:  # noqa: BLE001
            task = T.playbook_task(instance, r.manifest, None, f"{type(exc).__name__}: {exc}", 0, figures)
        if not task["passed"]:
            status = "failed"
        out.append(task)
        checkpoint()
    store.finish_run(session.run_id, status)


def write_results(doc, path: Path) -> None:
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def main(env=None, deps: Deps | None = None, out_path: Path = RESULTS_PATH) -> int:
    env = os.environ if env is None else env
    tasks: list = []
    instance = (env.get("AGENTSWITCH_INSTANCE") or "").strip().lower() or "harness"

    def checkpoint() -> None:
        doc = T.finalize(instance, tasks)
        doc["summary"] += " · partial (run in progress or stopped early)"
        write_results(doc, out_path)

    try:
        instance = collect(env, deps or default_deps(), tasks, checkpoint)
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
