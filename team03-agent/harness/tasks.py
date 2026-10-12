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
