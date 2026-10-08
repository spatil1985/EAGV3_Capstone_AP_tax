"""UC-04 — MSME 45-day payment exposure.

Spec: docs/usecases/IN/uc-04-msme-45-day-exposure.md.
Question: "Which small suppliers are we about to pay late, and what will it cost us?"

Statute: MSMED Act s.15 (pay within the agreed period, at most 45 days from acceptance),
s.16 (compound interest at 3 × RBI bank rate, monthly rests); Income-tax Act s.43B(h)
(an unpaid amount owed to a micro/small enterprise past the s.15 period is not deductible
until paid — 1961 Act numbering, confirm under the 2025 Act).

Rules:
  msme_45_day_breach       unpaid, posted bill from an MSME vendor past its deadline
                           (min(date + 45, due_date)). Exposure = penal interest + the s.43B(h)
                           disallowance (balance due) for micro/small vendors.
  msme_45_day_due_soon     not yet late, deadline within the warning window — pay these first.
  data_quality             negative grand_total (N7) → no figures computed on a corrupt base;
                           MSME vendor with blank Udyam number (s.43B(h) can't be evidenced).
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.msme import COVERED_TYPES, deadline, is_msme, penal_interest
from scripts.uc.common.records import NOT_POSTED, party_of, ref

WARN_DAYS = 7


def _vendor(bill, data):
    return data.index("parties", "id").get(bill.get("vendor_id"))


def _open_msme_bills(data):
    for bill in data.get("bills", []):
        if ((bill.get("status") or "").lower() in NOT_POSTED or money(bill.get("balance_due")) <= 0):
            continue
        vendor = _vendor(bill, data)
        if is_msme(vendor):
            yield bill, vendor


class MsmeBreach(Rule):
    id = "msme_45_day_breach"
    severity = 80

    def evaluate(self, data: Dataset, ctx):
        for bill, vendor in _open_msme_bills(data):
            due = deadline(bill, ctx)
            if not due or ctx.as_of <= due:
                continue
            number = ref(bill, "bill_number", "number")
            vid, vname = party_of(bill, data)
            if money(bill.get("grand_total")) < 0:
                yield Finding(finding_type=DATA_QUALITY, rule="stored_value_mismatch", entity_type="Bill",
                              entity_id=bill["id"], entity_ref=number, status=DATA_QUALITY, severity=10,
                              currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                              summary=f"{number} ({vname}) is past the MSME deadline but its grand_total is "
                                      f"negative (N7); no interest or disallowance computed on a corrupt base.",
                              details={"field": "grand_total", "observed": str(bill.get("grand_total")),
                                       "data_quality_flag": "n7_tds_corruption", "blocks": "UC-04 exposure"})
                continue
            balance = money(bill.get("balance_due"))
            overdue = (ctx.as_of - due).days
            interest = penal_interest(balance, overdue, ctx)
            mtype = (vendor.get("msme_type") or "").lower()
            covered = mtype in COVERED_TYPES
            disallow = balance if covered else Decimal("0.00")
            yield Finding(
                finding_type="msme_45_day_exposure", rule=self.id, severity=self.severity,
                entity_type="Bill", entity_id=bill["id"], entity_ref=number,
                interest_amount=interest, total_exposure=interest + disallow, currency=ctx.currency,
                counterparty_id=vid, counterparty_name=vname,
                summary=f"{number} ({vname}, {mtype or 'type unknown'}) — {overdue} days past the MSME "
                        f"deadline {due}, {fmt(interest, ctx.currency)} penal interest"
                        + (f", {fmt(disallow, ctx.currency)} at risk of s.43B(h) disallowance if unpaid "
                           f"by year-end" if covered else "") + ".",
                details={"vendor_msme_no": vendor.get("msme_no"), "msme_type": mtype,
                         "trigger_date": bill.get("date"), "deadline": str(due), "overdue_days": overdue,
                         "balance_due": str(balance), "penal_interest_amount": str(interest),
                         "bank_rate_pct": ctx.rule("rbi_bank_rate_pct"), "s43b_h_applicable": covered,
                         "s43b_h_disallowance_amount": str(disallow),
                         "s43b_h_caveat": None if vendor.get("msme_no") else "subject to Udyam confirmation (msme_no blank)"},
            )


class MsmeDueSoon(Rule):
    id = "msme_45_day_due_soon"
    severity = 45

    def evaluate(self, data, ctx):
        for bill, vendor in _open_msme_bills(data):
            due = deadline(bill, ctx)
            if not due or not (ctx.as_of <= due <= ctx.as_of + timedelta(days=WARN_DAYS)):
                continue
            number = ref(bill, "bill_number", "number")
            vid, vname = party_of(bill, data)
            balance = money(bill.get("balance_due"))
            yield Finding(
                finding_type="msme_45_day_exposure", rule=self.id, severity=self.severity,
                entity_type="Bill", entity_id=bill["id"], entity_ref=number, total_exposure=balance,
                currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                summary=f"{number} ({vname}) must be paid by {due} ({(due - ctx.as_of).days} days) to stay "
                        f"inside the MSME limit; {fmt(balance, ctx.currency)} due.",
                details={"deadline": str(due), "balance_due": str(balance),
                         "msme_type": (vendor.get("msme_type") or "").lower()},
            )


class UdyamMissing(Rule):
    id = "missing_required_field"
    severity = 5

    def evaluate(self, data, ctx):
        for party in data.get("parties", []):
            if is_msme(party) and not party.get("msme_no"):
                yield Finding(
                    finding_type=DATA_QUALITY, rule=self.id, entity_type="Party", entity_id=party["id"],
                    entity_ref=party.get("name"), status=DATA_QUALITY, severity=self.severity,
                    currency=ctx.currency, counterparty_id=party["id"], counterparty_name=party.get("name"),
                    summary=f"{party.get('name')} is marked MSME ({party.get('msme_type')}) with no Udyam "
                            f"number; s.43B(h) can't be evidenced.",
                    details={"field": "msme_no", "blocks": "UC-04 s.43B(h)"})


class Msme45DayExposure(Playbook):

    @property
    def rules(self):
        return [MsmeBreach(), MsmeDueSoon(), UdyamMissing()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"))

    def context(self, data, findings, ctx):
        msme = [p for p in data["parties"] if is_msme(p)]
        open_bills = list(_open_msme_bills(data))
        return {"MSME vendors": len(msme),
                "… by type": {t: sum(1 for p in msme if (p.get("msme_type") or "") == t) for t in ("micro", "small", "medium")},
                "open MSME bills": len(open_bills),
                "open MSME balance": str(sum((money(b.get("balance_due")) for b, _ in open_bills), Decimal("0"))),
                "RBI bank rate used (%)": ctx.rule("rbi_bank_rate_pct")}

    def summary(self, outcome, ctx):
        late = [f for f in outcome.findings if f.rule == "msme_45_day_breach"]
        soon = [f for f in outcome.findings if f.rule == "msme_45_day_due_soon"]
        interest = sum((f.interest_amount for f in late), Decimal("0"))
        disallow = sum((money(f.details["s43b_h_disallowance_amount"]) for f in late), Decimal("0"))
        head = (f"{len(late)} MSME bill(s) are past the 45-day limit: {fmt(interest, ctx.currency)} penal interest "
                f"and {fmt(disallow, ctx.currency)} at risk of s.43B(h) disallowance." if late
                else "No MSME bill is past its payment deadline.")
        return head + (f" {len(soon)} more fall due within {WARN_DAYS} days." if soon else "")
