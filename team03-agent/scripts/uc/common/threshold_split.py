"""Approval-threshold splitting shared by UC-44 (India) and US-20 (US).

Threshold per document type from config/overrides/approval_thresholds.yaml (ApprovalPolicy is 403),
else inferred from ApprovalRequest bands. Same-vendor documents within W days, each below the threshold,
together at or above it, none approved → split_candidate, with a strength score (similar amounts, same
creator, entered minutes apart, no or a single PO). Recurring standing orders are excluded.
"""

from datetime import datetime
from decimal import Decimal

import yaml

from aptax.config import CONFIG_DIR
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day

OVERRIDES = CONFIG_DIR / "overrides" / "approval_thresholds.yaml"
WINDOW_DAYS = 3
APPROVED = {"approved", "pending_approval", "rejected"}


def thresholds(tenant: str) -> dict:
    try:
        raw = yaml.safe_load(OVERRIDES.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    return raw.get(tenant) or {}


def _ts(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None) if v else None
    except ValueError:
        return None


def groups(docs):
    by_vendor: dict = {}
    for d in docs:
        if (d.get("status") or "").lower() in ("void", "cancelled") or d.get("recurring_bill_id") or not day(d.get("date")):
            continue
        by_vendor.setdefault(d.get("vendor_id"), []).append(d)
    for vendor, rows in by_vendor.items():
        rows.sort(key=lambda d: (d["date"], d.get("created_at") or ""))
        i = 0
        while i < len(rows):
            start = day(rows[i]["date"])
            group = [r for r in rows[i:] if (day(r["date"]) - start).days <= WINDOW_DAYS]
            if len(group) > 1:
                yield vendor, group
            i += len(group)


def strength(group) -> tuple[str, list]:
    reasons = []
    amounts = [money(d.get("grand_total")) for d in group]
    if max(amounts) - min(amounts) <= max(amounts) * Decimal("0.2"):
        reasons.append("similar amounts")
    if len({d.get("created_by") for d in group if d.get("created_by")}) == 1:
        reasons.append("same creator")
    times = sorted(t for t in (_ts(d.get("created_at")) for d in group) if t)
    if len(times) == len(group) and (times[-1] - times[0]).total_seconds() <= 600:
        reasons.append("entered within 10 minutes")
    if len({d.get("purchase_order_id") for d in group}) <= 1:
        reasons.append("no PO or a single PO")
    return ("high" if len(reasons) >= 3 else "medium" if len(reasons) == 2 else "low"), reasons


def split_findings(docs, doc_type: str, limit: dict | None, ctx):
    if not limit:
        return
    threshold = money(limit["threshold"])
    for vendor, group in groups(docs):
        amounts = [money(d.get("grand_total")) for d in group]
        if not all(0 < a < threshold for a in amounts) or sum(amounts) < threshold:
            continue
        if any((d.get("approval_status") or "").lower() in APPROVED for d in group):
            continue
        level, reasons = strength(group)
        name = group[0].get("_vendor_id_display") or vendor
        total = sum(amounts, Decimal("0"))
        refs = [d.get("number") for d in group]
        yield Finding(
            finding_type="approval_control", rule="split_candidate", severity={"high": 70, "medium": 55, "low": 40}[level],
            entity_type=doc_type, entity_id=f"{vendor}:{group[0]['date']}", entity_ref=f"{name} {group[0]['date']}",
            total_exposure=total, currency=ctx.currency, counterparty_id=vendor, counterparty_name=name,
            summary=f"{name} received {len(group)} {doc_type.lower()}(s) within {WINDOW_DAYS} days from {group[0]['date']} "
                    f"({', '.join(fmt(a, ctx.currency) for a in amounts)}), each under the {fmt(threshold, ctx.currency)} "
                    f"approval limit but {fmt(total, ctx.currency)} together, and none went through approval. Check "
                    f"whether this was one purchase ({level} strength: {', '.join(reasons) or 'amounts only'}). "
                    f"Threshold {limit.get('source')}.",
            details={"vendor_id": vendor, "window_days": WINDOW_DAYS, "documents": refs, "sum": str(total),
                     "threshold": str(threshold), "threshold_source": limit.get("source"), "strength": level,
                     "strength_reasons": reasons})


def infer_threshold(requests, doc_type: str):
    """Approval-history edge (UC-44 step 1): the highest amount under one policy when the next policy's
    amounts all lie above it. Returns (edge, bands) or (None, bands) when the bands overlap or are single."""
    bands: dict = {}
    for r in requests:
        if r.get("document_type") == doc_type and r.get("policy_id") and r.get("document_amount") is not None:
            bands.setdefault(r["policy_id"], []).append(money(r["document_amount"]))
    ranges = sorted((min(v), max(v), pid, len(v)) for pid, v in bands.items())
    summary = [{"policy_id": pid, "count": n, "from": str(lo), "to": str(hi)} for lo, hi, pid, n in ranges]
    for (lo1, hi1, _, n1), (lo2, _, _, n2) in zip(ranges, ranges[1:]):
        if n1 > 1 and n2 > 1 and hi1 < lo2:
            return hi1, summary
    return None, summary
