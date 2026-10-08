"""UC-16 — Stock expiry and the s.17(5)(h) blocked credit on write-off.

Spec: docs/usecases/IN/uc-16-drug-expiry-blocked-credit.md.
Question: "What stock is about to expire, and what credit do we lose when it does?"

Statute: s.17(5)(h) CGST Act — no ITC on goods lost, stolen, destroyed, written off or given as
gifts; credit already taken on expired stock that is written off must be reversed.

Rules:
  expiry_warning           a batch-tracked item with a shelf life whose latest receipt (bill
                           date, the proxy — no Batch/StockEntry tool is exposed, N426 T2.2/T2.3)
                           expires within 30 days, or has expired; exposure = that bill's ITC on it
  missing_required_field   (data_quality) a shelf-life item that is not batch-tracked: undatable
  classification_conflict  a shelf-life item typed `services` (a service can't expire)

The write-off reversal (s17_5_h_writeoff) needs a stock-adjustment event that is not exposed; it
is not emitted until it is.
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.lines import line_taxes
from scripts.uc.common.records import NOT_POSTED

WARN_DAYS = 30


def shelf_items(data):
    return [i for i in data.get("items", []) if money(i.get("shelf_life_days")) > 0]


def latest_receipt(item_id, bills):
    best = None
    for bill in bills:
        if (bill.get("status") or "").lower() in NOT_POSTED or not day(bill.get("date")):
            continue
        for idx, line in enumerate(bill.get("items") or []):
            if line.get("item_id") == item_id and (best is None or day(bill["date"]) > day(best[0]["date"])):
                best = (bill, idx, line)
    return best


class ExpiryWarning(Rule):
    id = "expiry_warning"
    severity = 55

    def evaluate(self, data: Dataset, ctx):
        for item in shelf_items(data):
            if not item.get("batch_tracked"):
                continue
            hit = latest_receipt(item["id"], data.get("bills", []))
            if not hit:
                continue
            bill, idx, line = hit
            expiry = day(bill["date"]) + timedelta(days=int(money(item["shelf_life_days"])))
            left = (expiry - ctx.as_of).days
            if left > WARN_DAYS:
                continue
            shares = line_taxes(bill)
            itc = shares[idx][1] if shares else Decimal("0.00")
            qty = money(line.get("qty"))
            yield Finding(
                finding_type="stock_expiry", rule=self.id, severity=70 if left < 0 else self.severity,
                entity_type="Item", entity_id=item["id"], entity_ref=item.get("name"),
                total_exposure=itc, reversal_base_amount=itc, currency=ctx.currency,
                summary=(f"{item.get('name')}: the lot received on {bill['date']} ({bill.get('number')}, {qty} unit(s)) "
                         + (f"expired on {expiry}" if left < 0 else f"expires on {expiry} ({left} days)")
                         + f". If written off, {fmt(itc, ctx.currency)} ITC must be reversed (s.17(5)(h))."),
                details={"item_id": item["id"], "expiry_estimate": str(expiry), "days_to_expiry": left, "qty": str(qty),
                         "itc_at_risk": str(itc), "per_unit_tax": str((itc / qty).quantize(CENTS)) if qty else None,
                         "basis": "bill_date_proxy", "bill": bill.get("number"),
                         "tax_source": "trusted" if shares is not None else "unsourced (tax lines inconsistent)",
                         "shelf_life_days": item.get("shelf_life_days")})


class Undatable(Rule):
    id = "missing_required_field"
    severity = 5

    def evaluate(self, data, ctx):
        for item in shelf_items(data):
            problems = []
            if not item.get("batch_tracked"):
                problems.append(("missing_required_field", "has a shelf life but is not batch-tracked, so its "
                                                           "stock can't be dated"))
            if item.get("product_type") == "services":
                problems.append(("classification_conflict", "has a shelf life but is typed services"))
            for rule, text in problems:
                yield Finding(finding_type=DATA_QUALITY, rule=rule, entity_type="Item", entity_id=item["id"],
                              entity_ref=item.get("name"), status=DATA_QUALITY, severity=self.severity,
                              currency=ctx.currency, summary=f"{item.get('name')} {text}.",
                              details={"field": "batch_tracked" if rule == "missing_required_field" else "product_type",
                                       "blocks": "UC-16 expiry date"})


class ExpiryBlockedCredit(Playbook):

    @property
    def rules(self):
        return [ExpiryWarning(), Undatable()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(items=fetcher.list("Item"), bills=fetcher.list("Bill"))

    def context(self, data, findings, ctx):
        items = shelf_items(data)
        return {"items with a shelf life": len(items),
                "… batch-tracked": sum(1 for i in items if i.get("batch_tracked")),
                "receipt dates": "bill date proxy — Batch/StockEntry not exposed (N426 T2.2, T2.3)",
                "write-off events": "not exposed; the s.17(5)(h) reversal row is not emitted yet"}

    def summary(self, outcome, ctx):
        warn = [f for f in outcome.findings if f.rule == "expiry_warning"]
        itc = sum((f.total_exposure for f in warn), Decimal("0"))
        expired = sum(1 for f in warn if f.details["days_to_expiry"] < 0)
        dq = len(outcome.findings) - len(warn)
        unsourced = sum(1 for f in warn if f.details.get("tax_source", "").startswith("unsourced"))
        return (f"{len(warn)} lot(s) expired or expiring within {WARN_DAYS} days ({expired} already expired); "
                f"{fmt(itc, ctx.currency)} ITC to reverse if they are written off"
                + (f" ({unsourced} lot(s) on bills whose tax can't be sourced)" if unsourced else "")
                + f". {dq} item(s) can't be dated or "
                f"are mis-typed. Dates are estimates from bill dates.")
