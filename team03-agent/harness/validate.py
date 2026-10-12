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
