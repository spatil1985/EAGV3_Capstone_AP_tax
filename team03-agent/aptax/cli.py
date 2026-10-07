"""Command line: `py -3 -m aptax <command>` from team03-agent/.

    py -3 -m aptax routes   --tenant in [--trigger scheduled --cadence daily]
    py -3 -m aptax run      --tenant in --playbook uc-12 [--as-of 2026-09-30] [--send]
    py -3 -m aptax call     --tenant us as_query entity=Bill op=count filters.status=open
    py -3 -m aptax ask      --tenant in "How many unpaid bills do we have?"
    py -3 -m aptax policy   SalarySlip.list
    py -3 -m aptax runs | journal <run_id> | refusals [--hours 24] | kill on|off|status
    py -3 -m aptax serve    [--host 127.0.0.1] [--port 8765]

Dry-run is the default: escalations are recorded as would-be writes and never sent.
`run --send` writes them to the shared ledger. T3 ledger writes are refused whatever the
flags. `ask` needs an LLM gateway plugged in: APTAX_LLM=package.module:factory.

`call` arguments are key=value pairs (dotted keys nest; values parse as JSON when they
can, so limit=5 is a number) or one JSON object. Pairs avoid PowerShell 5.1 stripping
the quotes out of JSON passed to native programs.

Credentials come from the environment or team03-agent/.env (never from this repo):
    in → AGENTSWITCH_EMAIL / _PASSWORD / _BASE_URL
    us → US_AGENTSWITCH_EMAIL / _PASSWORD / _BASE_URL

Exit codes: 0 done · 1 finished with errors or an unverified answer · 2 could not start ·
3 refused by the governor.
"""

import argparse
import json
import sys
from datetime import date

from aptax import service
from aptax.config import DB_PATH, KILL_FILE, TENANTS, kill_switch_on, load_dotenv
from aptax.llm import LLMNotConfigured, load_llm
from aptax.store import Store


def parse_pairs(items) -> dict:
    """['entity=Bill', 'filters.status=open', 'limit=5'] → {'entity': 'Bill', 'filters': {'status': 'open'}, 'limit': 5}"""
    items = list(items or [])
    if len(items) == 1 and items[0].lstrip().startswith("{"):
        value = json.loads(items[0])
        if not isinstance(value, dict):
            raise ValueError("arguments must be a JSON object")
        return value
    out: dict = {}
    for item in items:
        key, sep, raw = item.partition("=")
        if not sep or not key:
            raise ValueError(f"expected key=value, got {item!r}")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        node = out
        *parents, leaf = key.split(".")
        for p in parents:
            node = node.setdefault(p, {})
            if not isinstance(node, dict):
                raise ValueError(f"{key!r} nests under a non-object")
        node[leaf] = value
    return out


def _transports(args):
    return lambda tenant: service.make_transport(tenant, record=args.record, replay=args.replay)


def cmd_routes(args, store) -> int:
    out = service.routes(store, _transports(args), tenant=args.tenant, trigger=args.trigger,
                         cadence=args.cadence, vertical=args.vertical)
    ctx = out["ctx"]
    print(f"tenant={ctx.tenant} regime={ctx.tax_regime} vertical={ctx.vertical} ({ctx.vertical_source}) "
          f"tools listed={out['tools_listed']} · run {out['run_id']}")
    for r in out["routes"]:
        print(f"  {r.manifest.id:8} {r.manifest.capability:18} {r.action:8} {r.reason}")
    print("capabilities offered to the agent: " + ", ".join(out["offered"]))
    return 0


def cmd_run(args, store) -> int:
    if args.send:
        print("WARNING: --send writes escalations to the shared AgentSwitch ledger.", file=sys.stderr)
    out = service.run_playbooks(store, _transports(args), tenant=args.tenant, playbooks=args.playbook,
                                trigger=args.trigger, cadence=args.cadence, dry_run=not args.send,
                                as_of=date.fromisoformat(args.as_of) if args.as_of else None,
                                vertical=args.vertical)
    ctx = out["ctx"]
    print(f"run {out['run_id']} · {ctx.tenant} ({ctx.tax_regime}) · as of {ctx.as_of} · "
          f"{'dry-run' if ctx.dry_run else 'SENDING writes'}")
    for run in out["runs"]:
        status = run.error or (run.outcome.summary if run.outcome else run.route.reason)
        print(f"  {run.manifest.id:8} {run.route.action:8} {status}")
        if run.outcome:
            print(f"           new {run.new_count} · already known {len(run.outcome.findings) - run.new_count}")
        if run.escalation:
            data = run.escalation.get("data") or {}
            shown = "suppressed (dry-run)" if isinstance(data, dict) and data.get("suppressed") else run.escalation
            print(f"           escalation: {shown}")
    s = out["stats"]
    print(f"MCP calls {s['called']} · refused {s['refused']} · suppressed writes {s['suppressed']} · failed {s['failed']}")
    for path in out["paths"]:
        print(f"  → {path}")
    return 0 if out["status"] == "completed" else 1


def cmd_call(args, store) -> int:
    try:
        cargs = parse_pairs(args.args)
    except ValueError as exc:
        print(f"bad arguments: {exc}", file=sys.stderr)
        return 2
    out = service.call(store, _transports(args), tenant=args.tenant, capability=args.capability, args=cargs)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))
    return 0


def cmd_ask(args, store) -> int:
    try:
        llm = load_llm()
    except LLMNotConfigured as exc:
        print(exc, file=sys.stderr)
        return 2
    out = service.ask(store, _transports(args), tenant=args.tenant, question=" ".join(args.question), llm=llm)
    print(out["answer_md"])
    print(f"\nstatus {out['status']} · run {out['run_id']} · {out['turns']} model turn(s) · "
          f"{out['tool_calls']} capability call(s) · LLM ${out['usd']:.4f}")
    return 0 if out["status"] == "completed" else 1


def cmd_policy(args, _store) -> int:
    try:
        cargs = parse_pairs(args.args)
    except ValueError as exc:
        print(f"bad arguments: {exc}", file=sys.stderr)
        return 2
    v = service.policy_check(args.tool, cargs)
    rule = "" if v["rule_index"] is None or v["reason"].startswith("policy rule") else f" (rule {v['rule_index']})"
    print(f"{v['tool']} [{v['tier']}] → {'ALLOW' if v['allowed'] else 'DENY'}: {v['reason']}{rule}")
    if v["policy_error"]:
        print(f"policy file unreadable, denying everything: {v['policy_error']}")
    return 0 if v["allowed"] else 1


def cmd_runs(args, store) -> int:
    for r in store.recent_runs(args.limit):
        print(f"{r['run_id']:34} {r['tenant']:3} {r['mode']:9} {r['status']:11} {r['started_at']}")
    return 0


def cmd_journal(args, store) -> int:
    run = store.get_run(args.run_id)
    if not run:
        print(f"no run {args.run_id}", file=sys.stderr)
        return 2
    print(f"run {run['run_id']} · {run['tenant']} · {run['mode']} · {run['status']} · "
          f"started {run['started_at']} · finished {run['finished_at'] or '-'}")
    for e in store.journal_entries(args.run_id):
        payload = json.dumps(e["payload"], ensure_ascii=False, default=str)
        if not args.full and len(payload) > 300:
            payload = payload[:300] + "…"
        print(f"{e['seq']:>6} {e['ts']} {e['kind']:16} {payload}")
    if args.full and run.get("answer_md"):
        print("\n" + run["answer_md"])
    return 0


def cmd_refusals(args, store) -> int:
    from datetime import UTC, datetime, timedelta
    since = (datetime.now(UTC) - timedelta(hours=args.hours)).isoformat(timespec="seconds")
    rows = store.refusals(since)
    for r in rows:
        print(f"{r['ts']} {r['control']:18} {r['subscription_id'] or '-':10} {r['reason']}")
    print(f"{len(rows)} refusal(s) in the last {args.hours} h")
    return 0


def cmd_kill(args, _store) -> int:
    if args.state == "on":
        KILL_FILE.write_text("stopped from the CLI\n", encoding="utf-8")
    elif args.state == "off" and KILL_FILE.exists():
        KILL_FILE.unlink()
    print(f"kill switch {'ON' if kill_switch_on() else 'off'} ({KILL_FILE})")
    return 0


def cmd_serve(args, store) -> int:
    from aptax.api import serve
    serve(store, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="py -3 -m aptax", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=str(DB_PATH), help="SQLite store (default runs/aptax.sqlite)")
    sub = parser.add_subparsers(dest="command", required=True)

    def live(p):
        p.add_argument("--tenant", choices=sorted(TENANTS), default="in")
        src = p.add_mutually_exclusive_group()
        src.add_argument("--record", help="save every AgentSwitch response under this directory (in runs/)")
        src.add_argument("--replay", help="serve AgentSwitch responses from a --record directory (offline)")

    p = sub.add_parser("routes", help="which playbooks would run, and why not")
    live(p)
    p.add_argument("--trigger", choices=["on_request", "scheduled", "event"])
    p.add_argument("--cadence", choices=["daily", "weekly", "monthly"])
    p.add_argument("--vertical", help="override the vertical from OrgProfile.industry")
    p.set_defaults(handler=cmd_routes)

    p = sub.add_parser("run", help="run playbooks deterministically (no LLM)")
    live(p)
    p.add_argument("--playbook", action="append", help="playbook id or capability, repeatable (e.g. uc-12)")
    p.add_argument("--trigger", choices=["on_request", "scheduled", "event"], default="on_request")
    p.add_argument("--cadence", choices=["daily", "weekly", "monthly"])
    p.add_argument("--as-of", help="evaluate as of YYYY-MM-DD (default: today in the tenant's timezone)")
    p.add_argument("--vertical", help="override the vertical from OrgProfile.industry")
    p.add_argument("--send", action="store_true", help="send escalations (default: dry-run, never sent)")
    p.set_defaults(handler=cmd_run)

    p = sub.add_parser("call", help="run one capability the way the agent loop would")
    live(p)
    p.add_argument("capability", help="e.g. as_query, as_context, eway, explain_use_case")
    p.add_argument("args", nargs="*", help="key=value pairs or one JSON object")
    p.set_defaults(handler=cmd_call)

    p = sub.add_parser("ask", help="answer a question with the agent loop (needs APTAX_LLM)")
    live(p)
    p.add_argument("question", nargs="+")
    p.set_defaults(handler=cmd_ask)

    p = sub.add_parser("policy", help="the policy verdict for one tool call (no network)")
    p.add_argument("tool", help="e.g. SalarySlip.list, Bill.update, endpoint.approvals.check_sla")
    p.add_argument("args", nargs="*", help="key=value pairs or one JSON object, e.g. dry_run=true")
    p.set_defaults(handler=cmd_policy, no_store=True)

    p = sub.add_parser("runs", help="recent runs")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(handler=cmd_runs)

    p = sub.add_parser("journal", help="a run's append-only journal")
    p.add_argument("run_id")
    p.add_argument("--full", action="store_true", help="untruncated payloads and the stored answer")
    p.set_defaults(handler=cmd_journal)

    p = sub.add_parser("refusals", help="work the controls prevented")
    p.add_argument("--hours", type=int, default=24)
    p.set_defaults(handler=cmd_refusals)

    p = sub.add_parser("kill", help="the out-of-band kill switch (config/kill)")
    p.add_argument("state", choices=["on", "off", "status"])
    p.set_defaults(handler=cmd_kill, no_store=True)

    p = sub.add_parser("serve", help="HTTP API on 127.0.0.1 (stdlib server)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(handler=cmd_serve)
    return parser


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):      # Windows consoles default to cp1252, which cannot print ₹
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    load_dotenv()
    args = build_parser().parse_args(argv)
    store = None if getattr(args, "no_store", False) else Store(args.db)
    try:
        return args.handler(args, store)
    except service.Refused as exc:
        print(f"refused by {exc.control}: {exc.reason}", file=sys.stderr)
        return 3
    except service.ServiceError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()
