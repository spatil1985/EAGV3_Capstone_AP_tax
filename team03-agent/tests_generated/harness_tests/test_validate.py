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
