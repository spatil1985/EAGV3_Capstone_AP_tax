"""Rendering: code writes the tables and totals, the model writes only the narrative
(agent_design.md §4.6, principle 1).

- `render_answer`      the on_request answer: sections, evidence tables, caveats, status;
- `render_stopped`     what the caller sees when the loop ends without an answer;
- `write_run_reports`  runs/<run_id>/report.md and report.json for a deterministic
                       playbook run (CLI `run`, later the scheduled pipelines).

Free text from records reaches a human reader here, unwrapped but table-escaped; it was
data to the model and stays data on the page.
"""

import json
from collections import Counter
from decimal import Decimal

from aptax.domain.contracts import fmt

MAX_ROWS_PER_RULE = 15


def _plain(value) -> str:
    if isinstance(value, dict) and set(value) == {"untrusted"}:
        value = value["untrusted"]
    text = "—" if value in (None, "") else str(value)
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _money(value, currency: str) -> str:
    try:
        return fmt(Decimal(str(value)), currency)
    except Exception:  # noqa: BLE001 — a non-amount is shown as written
        return _plain(value)


def describe(ledger, ident: str) -> str:
    """One line saying what an evidence id is."""
    if ident in ledger.items:
        ev = ledger.items[ident]
        data = ev.data if isinstance(ev.data, dict) else {}
        if ev.capability == "as_query":
            filters = ", ".join(f"{k}={v}" for k, v in (data.get("filters") or {}).items())
            what = f"{data.get('entity')} {data.get('op')}" + (f" ({filters})" if filters else "")
            tail = f"total {data['total']}" if data.get("total") is not None else "record"
            return f"`{ident}` as_query {what} → {tail}"
        if "playbook" in data and "total_findings" in data:
            return f"`{ident}` {ev.capability} ({data['playbook']}) → {data['total_findings']} finding(s)"
        args = ", ".join(f"{k}={v}" for k, v in ev.args.items())
        return f"`{ident}` {ev.capability}" + (f" ({args})" if args else "")
    if ident in ledger.findings:
        row = ledger.findings[ident]
        return (f"`{ident}` finding [{_plain(row.get('rule'))}] {_plain(row.get('entity_ref'))} "
                f"from {ledger.finding_source.get(ident, '?')}")
    return f"`{ident}` (unknown)"


def _playbook_table(ident: str, data: dict, currency: str) -> list[str]:
    lines = [f"**{ident} · {data.get('capability')} ({data.get('playbook')})** — {_plain(data.get('summary'))}", ""]
    by_rule = data.get("by_rule") or {}
    if by_rule:
        lines += ["| Rule | Findings | Exposure |", "|---|---:|---:|"]
        lines += [f"| `{rule}` | {v.get('count')} | {_money(v.get('exposure'), currency)} |"
                  for rule, v in by_rule.items()]
        lines.append("")
    rows = data.get("top_findings") or []
    if rows:
        lines += ["| Finding | Rule | Ref | Counterparty | Exposure |", "|---|---|---|---|---:|"]
        lines += [f"| `{r.get('finding_id')}` | `{r.get('rule')}` | {_plain(r.get('entity_ref'))} | "
                  f"{_plain(r.get('counterparty_name'))} | {_money(r.get('total_exposure'), r.get('currency') or currency)} |"
                  for r in rows]
        if data.get("truncated"):
            lines.append(f"| … | | | | {data.get('total_findings', 0) - len(rows)} more (get_findings) |")
        lines.append("")
    return lines


def _footer(ctx, stats: dict) -> str:
    mode = "dry-run: no writes sent" if ctx.dry_run else "writes enabled"
    return (f"*Run `{ctx.run_id}` · tenant `{ctx.tenant}` ({ctx.tax_regime}, {ctx.currency}) · as of "
            f"{ctx.as_of} · {mode} · {stats.get('tool_calls', 0)} capability call(s) · "
            f"{stats.get('turns', 0)} model turn(s) · LLM ${stats.get('usd', 0.0):.4f}*")


def render_answer(*, ctx, question: str, sections, caveats, ledger, report, stats: dict) -> str:
    lines = [f"## Answer — {ctx.tenant.upper()} · {ctx.tax_regime} · as of {ctx.as_of}", "", f"> {_plain(question)}", ""]
    shown = set()
    for n, s in enumerate(sections, 1):
        lines += [f"### {n}. {_plain(s.question)}", "", s.narrative, ""]
        for ident in s.evidence_ids:
            ev = ledger.items.get(ident)
            if ev and ident not in shown and isinstance(ev.data, dict) and "by_rule" in ev.data:
                lines += _playbook_table(ident, ev.data, ctx.currency)
                shown.add(ident)
        if s.evidence_ids:
            lines += ["*Evidence: " + " · ".join(describe(ledger, i) for i in s.evidence_ids) + "*", ""]
    if caveats:
        lines += ["### Caveats", ""] + [f"- {c}" for c in caveats] + [""]
    lines.append("---")
    if report.ok:
        lines.append("**Status: verified** — every number in the sections above appears in the evidence it cites.")
    else:
        lines.append("**Status: unverified** — the evidence check failed:")
        lines += [f"- {p}" for p in report.problems]
    lines += ["", _footer(ctx, stats)]
    return "\n".join(lines)


def render_stopped(*, ctx, question: str, reason: str, ledger, stats: dict, text: str | None = None) -> str:
    lines = [f"## No verified answer — {ctx.tenant.upper()} · {ctx.tax_regime}", "", f"> {_plain(question)}", "",
             f"The agent stopped: **{reason}**.", ""]
    if text:
        lines += ["The model replied without using submit_answer, so this text was **not checked** "
                  "against any evidence:", "", "> " + text.strip().replace("\n", "\n> "), ""]
    if ledger.items:
        lines += ["Evidence gathered before it stopped:", ""]
        lines += [f"- {describe(ledger, i)}" for i in ledger.items] + [""]
    lines += ["---", _footer(ctx, stats)]
    return "\n".join(lines)


# -- deterministic playbook runs --------------------------------------------------------

def _run_json(ctx, runs, stats) -> dict:
    return {
        "run_id": ctx.run_id, "tenant": ctx.tenant, "trigger": ctx.trigger, "as_of": str(ctx.as_of),
        "dry_run": ctx.dry_run, "tax_regime": ctx.tax_regime, "vertical": ctx.vertical, "stats": stats,
        "playbooks": [{
            "id": r.manifest.id, "action": r.route.action, "reason": r.route.reason, "error": r.error,
            "summary": r.outcome.summary if r.outcome else None,
            "context": r.outcome.context if r.outcome else None,
            "new_findings": r.new_count,
            "repeat_findings": (len(r.outcome.findings) - r.new_count) if r.outcome else 0,
            "escalation": r.escalation,
            "findings": [f.to_dict() for f in r.outcome.findings] if r.outcome else [],
        } for r in runs],
    }


def _run_markdown(ctx, runs, stats) -> str:
    mode = "**dry-run**: no writes sent" if ctx.dry_run else "writes enabled"
    lines = [f"# Playbook run {ctx.run_id}", "",
             f"*tenant `{ctx.tenant}` ({ctx.tax_regime}, {ctx.currency}) · vertical {ctx.vertical} · "
             f"as of {ctx.as_of} · trigger `{ctx.trigger}` · {mode}*", ""]
    for run in runs:
        m = run.manifest
        lines.append(f"## {m.id.upper()} — {m.title}")
        if run.route.action != "run":
            lines += [f"*{run.route.action}: {run.route.reason}*", ""]
            continue
        if run.error:
            lines += [f"**Error:** {run.error}", ""]
            continue
        out = run.outcome
        lines += [_plain(out.summary), "",
                  f"New: **{run.new_count}** · already known: {len(out.findings) - run.new_count} · "
                  f"anomalies: {len(out.anomalies)}", ""]
        if out.context:
            lines += ["| Context | Value |", "|---|---|"] + [f"| {k} | {_plain(v)} |" for k, v in out.context.items()] + [""]
        for rule, count in Counter(f.rule for f in out.findings).items():
            rows = [f for f in out.findings if f.rule == rule]
            exposure = sum((f.total_exposure for f in rows), Decimal("0"))
            lines += [f"### `{rule}` — {count} · {fmt(exposure, ctx.currency)}", "",
                      "| Ref | Counterparty | Exposure | Summary |", "|---|---|---:|---|"]
            lines += [f"| {_plain(f.entity_ref)} | {_plain(f.counterparty_name)} | {fmt(f.total_exposure, f.currency)} | "
                      f"{_plain(f.summary)} |" for f in rows[:MAX_ROWS_PER_RULE]]
            if count > MAX_ROWS_PER_RULE:
                lines.append(f"| … | | | {count - MAX_ROWS_PER_RULE} more in report.json |")
            lines.append("")
    lines.append(f"*MCP calls {stats.get('called', 0)} · refused {stats.get('refused', 0)} · "
                 f"suppressed writes {stats.get('suppressed', 0)} · failed {stats.get('failed', 0)}*")
    return "\n".join(lines)


def write_run_reports(ctx, runs, stats: dict) -> list[str]:
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, body in (("report.md", _run_markdown(ctx, runs, stats)),
                       ("report.json", json.dumps(_run_json(ctx, runs, stats), indent=1, default=str))):
        path = ctx.run_dir / name
        path.write_text(body, encoding="utf-8")
        paths.append(str(path))
    return paths
