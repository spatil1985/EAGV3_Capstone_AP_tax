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


def test_own_not_run_keeps_only_our_regime_routes_that_do_not_run():
    us09 = FakeManifest("us-09", tax_regimes=("sales_use_tax",))
    uc07, uc08 = FakeManifest("uc-07"), FakeManifest("uc-08")
    routes = [FakeRoute(UC23, "run"), FakeRoute(US01, "skip", "tax_regime gst not in"),
              FakeRoute(us09, "blocked", "x"), FakeRoute(uc07, "skip", "vertical manufacturing not in ['school']"),
              FakeRoute(uc08, "blocked", "blocked by F18")]
    assert [r.manifest.id for r in T.own_not_run(routes, "gst")] == ["uc-07", "uc-08"]


def test_all_regime_manifest_is_ours():
    m = FakeManifest("uc-99", tax_regimes=("all",))
    assert [r.manifest.id for r in T.own_not_run([FakeRoute(m, "spec", "x")], "sales_use_tax")] == ["uc-99"]


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


def test_routing_floor_lists_playbooks_that_do_not_run():
    t = T.routing_floor_task("x", "in", 36, ["uc-07", "uc-08"])
    assert t["passed"] is True
    assert t["evidence"] == "36 playbooks routed to run (floor 36); not run here (blocked/spec-only): uc-07, uc-08"


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
