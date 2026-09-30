"""CLI and composition root: `py -3 -m harness <command>` from team03-agent/.

    py -3 -m harness routes --tenant in
    py -3 -m harness run --tenant in --playbook uc-12
    py -3 -m harness run --tenant in --trigger scheduled --cadence daily
    py -3 -m harness run --tenant in --playbook uc-12 --record runs/rec-uc12
    py -3 -m harness run --tenant in --playbook uc-12 --replay runs/rec-uc12 --as-of 2026-09-30

Dry-run is the default: T1 writes (escalations) are recorded in the trace, not sent.
`--commit` sends them. T3 ledger writes are refused whatever the flags.

Credentials come from the environment (never from this repo):
    in → AGENTSWITCH_EMAIL / _PASSWORD / _BASE_URL
    us → US_AGENTSWITCH_EMAIL / _PASSWORD / _BASE_URL

This module is the only place the concrete classes are chosen and wired together;
everything else depends on the small interfaces (Transport, Policy, Rule, Playbook,
FindingStore, ReportRenderer).
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from harness.context import ROOT, ContextError, RunContext
from harness.gateway import ToolGateway
from harness.registry import Registry
from harness.report import EscalationWriter, JsonReport, MarkdownReport
from harness.runner import Runner
from harness.state import LocalJsonStore, MemoryStore
from harness.trace import AnomalyLog, CallCounter, EventBus, JsonlTraceWriter
from harness.transport import LiveTransport, RecordingTransport, ReplayTransport
from scripts.fetch import Fetcher

ENV_PREFIX = {"in": "AGENTSWITCH", "us": "US_AGENTSWITCH"}


def build_transport(args):
    if args.replay:
        return ReplayTransport(Path(args.replay))
    from scripts.agentswitch_client import AgentSwitchClient
    transport = LiveTransport(AgentSwitchClient.from_env(ENV_PREFIX[args.tenant]))
    return RecordingTransport(transport, Path(args.record)) if args.record else transport


def build_context(args, transport) -> RunContext:
    return RunContext.build(
        transport, tenant=args.tenant, trigger=args.trigger,
        as_of=date.fromisoformat(args.as_of) if args.as_of else None,
        dry_run=not args.commit, vertical=args.vertical,
    )


def cmd_routes(args) -> int:
    ctx = build_context(args, build_transport(args))
    print(f"tenant={ctx.tenant} regime={ctx.tax_regime} vertical={ctx.vertical} "
          f"({ctx.vertical_source}) trigger={args.trigger}/{args.cadence or '-'}")
    for route in Registry().route(ctx, trigger=args.trigger, cadence=args.cadence,
                                  ids=args.playbook or None):
        print(f"  {route.manifest.id:8} {route.action:8} {route.reason}")
    return 0


def cmd_run(args) -> int:
    transport = build_transport(args)
    ctx = build_context(args, transport)

    bus, counter = EventBus(), CallCounter()
    bus.subscribe(JsonlTraceWriter(ctx.run_dir))
    bus.subscribe(counter)

    gateway = ToolGateway(transport, bus, ctx.run_id, dry_run=ctx.dry_run,
                          allow_workflow=args.allow_workflow)
    # Dry-run and committed runs keep separate memories, so a rehearsal never
    # swallows the escalation a real run should send.
    store = (MemoryStore() if args.replay else
             LocalJsonStore(ROOT / "runs" / ("state.dry-run.json" if ctx.dry_run else "state.json")))
    anomalies = AnomalyLog(ctx.run_dir)

    runner = Runner(registry=Registry(), gateway=gateway, fetcher=Fetcher(gateway),
                    store=store, anomaly_log=anomalies,
                    renderers=[MarkdownReport(), JsonReport()],
                    escalations=EscalationWriter(gateway))
    result, paths = runner.run(ctx, trigger=args.trigger, cadence=args.cadence,
                               ids=args.playbook or None)

    print(result.headline())
    for run in result.runs:
        status = run.error or (run.outcome.summary if run.outcome else run.route.reason)
        print(f"  {run.route.manifest.id:8} {run.route.action:8} {status}")
        if run.escalation:
            print(f"           escalation: {'suppressed (dry-run)' if ctx.dry_run else run.escalation}")
    print(f"MCP calls: {counter.called} · refused: {len(counter.refused)} · "
          f"suppressed writes: {len(counter.suppressed)} · anomalies: {anomalies.count}")
    for path in paths + [str(ctx.run_dir / "trace.jsonl")]:
        print(f"  → {path}")
    return 1 if any(r.error for r in result.runs) else 0


def main(argv=None) -> int:
    # Windows consoles default to cp1252, which cannot print ₹.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="python -m harness", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name, handler in (("run", cmd_run), ("routes", cmd_routes)):
        p = sub.add_parser(name)
        p.set_defaults(handler=handler)
        p.add_argument("--tenant", choices=ENV_PREFIX, default="in")
        p.add_argument("--playbook", action="append", help="playbook id, repeatable (e.g. uc-12)")
        p.add_argument("--trigger", choices=["on_request", "scheduled", "event"], default="on_request")
        p.add_argument("--cadence", choices=["daily", "weekly", "monthly"])
        p.add_argument("--as-of", help="evaluate as of YYYY-MM-DD (default today)")
        p.add_argument("--vertical", help="override vertical profile (default manufacturing)")
        p.add_argument("--commit", action="store_true", help="send T1 writes (escalations)")
        p.add_argument("--allow-workflow", action="store_true", help="permit T2 workflow calls")
        src = p.add_mutually_exclusive_group()
        src.add_argument("--record", help="save every response under this directory")
        src.add_argument("--replay", help="serve responses from a --record directory (offline)")
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except ContextError as exc:
        print(f"run aborted: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
