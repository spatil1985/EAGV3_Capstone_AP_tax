"""What the model is allowed to see of a result (agent_design.md §4.6, G9).

- **Clip** like S17 `planner._clip`: strings ≤ 4,000 chars, lists ≤ 12 items, dicts ≤ 30
  keys, depth ≤ 9 — so one big result can't flood the context.
- **Wrap free text as untrusted**: vendor notes, descriptions and the like arrive as
  `{"untrusted": "..."}`. The charter tells the model such text is data, never instructions.
- **Shape playbook outcomes**: counts and exposure by rule, plus the top 10 rows by
  exposure and a `run_ref` for paging (`get_findings`). Full rows go only to the report.
"""

from collections import defaultdict
from decimal import Decimal

FREE_TEXT_FIELDS = {"notes", "description", "terms", "reason", "remarks", "memo", "purpose",
                    "narration", "final_comments", "subject", "comment", "comments", "title", "payee",
                    "customer_notes", "terms_and_conditions", "resolution_note", "summary",
                    "counterparty_name"}
PRIVATE_PREFIXES = ("_permissions", "_readonly_fields", "_can_")


def clip(value, *, chars: int = 4_000, depth: int = 0):
    if depth > 9:
        return "<depth-limit>"
    if isinstance(value, str):
        return value if len(value) <= chars else value[:chars] + f"…<{len(value) - chars} chars>"
    if isinstance(value, list):
        out = [clip(v, chars=chars, depth=depth + 1) for v in value[:12]]
        if len(value) > 12:
            out.append(f"…<{len(value) - 12} more items>")
        return out
    if isinstance(value, dict):
        items = list(value.items())
        out = {str(k): clip(v, chars=chars, depth=depth + 1) for k, v in items[:30]}
        if len(items) > 30:
            out["…"] = f"<{len(items) - 30} more keys>"
        return out
    if isinstance(value, Decimal):
        return str(value)
    return value


def wrap_untrusted(value, *, depth: int = 0):
    """Wrap free-text fields (recursively) so the model can tell data from instructions."""
    if depth > 9:
        return value
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if str(k).startswith(PRIVATE_PREFIXES):
                continue
            if k in FREE_TEXT_FIELDS and isinstance(v, str) and v:
                out[k] = {"untrusted": v}
            else:
                out[k] = wrap_untrusted(v, depth=depth + 1)
        return out
    if isinstance(value, list):
        return [wrap_untrusted(v, depth=depth + 1) for v in value]
    return value


def shape_record(record: dict) -> dict:
    return clip(wrap_untrusted(record))


def shape_outcome(manifest, outcome, run_ref: str, *, top: int = 10) -> dict:
    counts, exposure = defaultdict(int), defaultdict(lambda: Decimal("0"))
    for f in outcome.findings:
        counts[f.rule] += 1
        exposure[f.rule] += f.total_exposure
    ranked = sorted(outcome.findings, key=lambda f: f.total_exposure, reverse=True)
    rows = [{"finding_id": f.fingerprint, "rule": f.rule, "entity_type": f.entity_type,
             "entity_ref": f.entity_ref, "total_exposure": str(f.total_exposure), "currency": f.currency,
             "counterparty_name": f.counterparty_name, "summary": f.summary} for f in ranked[:top]]
    return {
        "playbook": manifest.id, "capability": manifest.capability, "run_ref": run_ref,
        "summary": outcome.summary,
        "total_findings": len(outcome.findings),
        "by_rule": {r: {"count": counts[r], "exposure": str(exposure[r])} for r in counts},
        "top_findings": wrap_untrusted(rows),
        "truncated": len(outcome.findings) > top,
        "context": clip(outcome.context),
    }
