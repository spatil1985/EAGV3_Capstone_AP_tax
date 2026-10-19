"""LLM-generated, not graded. harness.__main__: orchestration, failure paths, results file."""

import itertools
import json

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
            goldens=None, clock=None, open_session=None, make_store=None, started=None):
    session = FakeSession(regime, routes, behaviours)
    store = FakeStore()
    calls = {}

    def fake_open_session(st, tr, **kwargs):
        calls.update(kwargs)
        return session

    deps = Deps(make_transport=lambda tenant: calls.setdefault("tenant", tenant) and (transport or FakeTransport()),
                open_session=open_session or fake_open_session,
                make_store=make_store or (lambda: store),
                goldens=goldens or {}, clock=clock or (lambda: 0.0), deadline_s=100.0, started=started)
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
    assert "keystone:us-09" not in by_id and "keystone:uc-05" not in by_id   # blocked/other-regime: omitted
    assert by_id["keystone:routing_floor"]["passed"] is False      # 2 < 18
    assert by_id["keystone:routing_floor"]["evidence"].endswith("not run here (blocked/spec-only): us-09")
    assert doc["summary"] == "keystone: 4/6 passed · goldens 1/1 exact"
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


def test_spent_budget_marks_remaining_playbooks_not_run(tmp_path):
    transport = FakeTransport()

    def spends_the_budget(gw, m):
        transport.budget_exhausted = "HTTP 429 budget_exhausted"
        return FakeRun(FakeRoute(m), None, "BudgetExhausted: HTTP 429 budget_exhausted")

    _, by_id, session, store, *_ = harness(tmp_path, [FakeRoute(US01), FakeRoute(US02)],
                                           {"us-01": spends_the_budget, "us-02": ok("b")}, transport=transport)
    assert by_id["keystone:us-01"]["passed"] is False
    assert by_id["keystone:us-02"]["evidence"] == "not run: platform token budget exhausted (HTTP 429 budget_exhausted)"
    assert session.runner.ran == ["us-01"]
    assert store.finished == [("run-1", "failed")]


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


def test_task_building_error_fails_only_that_playbook(tmp_path):
    """A context json.dumps can't serialise (a tuple dict key) must not lose later playbooks."""
    def odd_context(gw, m):
        return FakeRun(FakeRoute(m), FakeOutcome("ok", context={("a", "b"): 1}))
    _, by_id, session, *_ = harness(tmp_path, [FakeRoute(US01), FakeRoute(US02)],
                                    {"us-01": odd_context, "us-02": ok("fine")})
    assert by_id["keystone:us-01"]["passed"] is True
    assert by_id["keystone:us-02"]["passed"] is True
    assert "keystone:harness_crashed" not in by_id


def test_results_are_checkpointed_after_every_playbook(tmp_path):
    """If the server kills the run mid-way, the file already holds what was decided."""
    seen = {}

    def peek(gw, m):
        seen["doc"] = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
        return FakeRun(FakeRoute(m), FakeOutcome("b"))
    harness(tmp_path, [FakeRoute(US01), FakeRoute(US02)], {"us-01": ok("a"), "us-02": peek})
    ids = [t["id"] for t in seen["doc"]["tasks"]]
    assert "keystone:us-01" in ids and "keystone:us-02" not in ids
    assert "partial" in seen["doc"]["summary"]
    assert validate(seen["doc"]) == []


def test_instance_name_is_case_insensitive(tmp_path):
    _, by_id, _, _, calls, _ = harness(tmp_path, [], {}, env={**ENV, "AGENTSWITCH_INSTANCE": " KeyStone "})
    assert calls["tenant"] == "us"
    assert by_id["keystone:locale_matches_instance"]["passed"] is True


def test_deadline_counts_from_process_start(tmp_path):
    """Time spent before collect() (imports, setup) counts against the server's limit."""
    _, by_id, session, *_ = harness(tmp_path, [FakeRoute(US01)], {"us-01": ok("a")},
                                    clock=lambda: 1000.0, started=0.0)
    assert by_id["keystone:us-01"]["evidence"] == "not run: harness time budget exhausted"
    assert session.runner.ran == []
