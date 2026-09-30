"""Outputs: rendered reports and escalations (harness_plan.md §4.9).

Pattern: **Strategy** — `ReportRenderer` implementations turn one `RunResult` into
one file each. The runner loops over whatever renderers it was given; adding a CSV or
Slack renderer is a new class, not a change here.

Numbers in every output come from Finding rows (principle 1: code writes the numbers).
"""

import json
from abc import ABC, abstractmethod
from collections import Counter
from decimal import Decimal

from scripts.money import fmt

MAX_ROWS_PER_RULE = 15


class ReportRenderer(ABC):
    filename: str

    @abstractmethod
    def render(self, result) -> str: ...

    def write(self, result) -> str:
        path = result.ctx.run_dir / self.filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(result), encoding="utf-8")
        return str(path)


class JsonReport(ReportRenderer):
    filename = "report.json"

    def render(self, result):
        ctx = result.ctx
        return json.dumps({
            "run_id": ctx.run_id, "tenant": ctx.tenant, "trigger": ctx.trigger,
            "as_of": str(ctx.as_of), "dry_run": ctx.dry_run, "tax_regime": ctx.tax_regime,
            "summary": result.headline(),
            "playbooks": [{
                "id": r.route.manifest.id, "action": r.route.action, "reason": r.route.reason,
                "error": r.error, "summary": r.outcome.summary if r.outcome else None,
                "context": r.outcome.context if r.outcome else None,
                "new_findings": r.new_count, "repeat_findings": r.repeat_count,
                "findings": [f.to_dict() for f in r.outcome.findings] if r.outcome else [],
            } for r in result.runs],
        }, indent=1, default=str)


class MarkdownReport(ReportRenderer):
    filename = "report.md"

    def render(self, result):
        ctx = result.ctx
        lines = [result.headline(), "",
                 f"*run `{ctx.run_id}` · tenant `{ctx.tenant}` ({ctx.tax_regime}, {ctx.currency}) · "
                 f"as of {ctx.as_of} · trigger `{ctx.trigger}` · "
                 f"{'**dry-run**: no writes sent' if ctx.dry_run else 'writes enabled'}*", ""]
        for run in result.runs:
            m = run.route.manifest
            lines.append(f"## {m.id.upper()} — {m.title}")
            if run.route.action != "run":
                lines += [f"*{run.route.action}: {run.route.reason}*", ""]
                continue
            if run.error:
                lines += [f"**Error:** {run.error}", ""]
                continue
            out = run.outcome
            lines += [out.summary, "",
                      f"New this period: **{run.new_count}** · already reported: {run.repeat_count}"
                      f" · anomalies logged: {len(out.anomalies)}", ""]
            if out.context:
                lines += ["| Context | Value |", "|---|---|"]
                lines += [f"| {k} | {v} |" for k, v in out.context.items()]
                lines.append("")
            by_rule = Counter(f.rule for f in out.findings)
            for rule, count in by_rule.items():
                rows = [f for f in out.findings if f.rule == rule]
                exposure = sum((f.total_exposure for f in rows), Decimal("0"))
                lines += [f"### `{rule}` — {count} · {fmt(exposure, ctx.currency)}", "",
                          "| Ref | Counterparty | Exposure | Summary |", "|---|---|---|---|"]
                for f in rows[:MAX_ROWS_PER_RULE]:
                    lines.append(f"| {f.entity_ref} | {f.counterparty_name or '—'} | "
                                 f"{fmt(f.total_exposure, f.currency)} | {f.summary} |")
                if count > MAX_ROWS_PER_RULE:
                    lines.append(f"| … | | | {count - MAX_ROWS_PER_RULE} more in report.json |")
                lines.append("")
        return "\n".join(lines)


class EscalationWriter:
    """One escalation per playbook per run, built from NEW finding rows only.

    Goes through the gateway as a T1 annotate call, so `--dry-run` (the default)
    suppresses it and the trace records what would have been sent.
    The AgentEscalation.create argument shape is from its live inputSchema (2026-09-30).
    """

    def __init__(self, gateway):
        self._gw = gateway

    def write(self, ctx, run) -> dict | None:
        m = run.route.manifest
        new = [f for f in run.outcome.findings if f.fingerprint in run.new_fingerprints]
        if m.escalate != "new_findings" or not new:
            return None
        body = [run.outcome.summary, "", f"{len(new)} new finding(s), run {ctx.run_id}:"]
        body += [f"- [{f.rule}] {f.entity_ref}: {f.summary}" for f in new[:25]]
        if len(new) > 25:
            body.append(f"- … {len(new) - 25} more in runs/{ctx.run_id}/report.json")
        result = self._gw.call_tool("AgentEscalation.create", {
            "company_id": ctx.company_id,
            "subject": f"[{m.id.upper()}] {len(new)} new: {m.title}"[:200],
            "reason": "\n".join(body),
            "reason_code": "other",
        })
        return {"ok": result.ok, "data": result.data, "error": result.error}
