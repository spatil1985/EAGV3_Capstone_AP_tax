"""UC-23 — Period GST liability (GSTR-3B): what we owe, by head, and how much in cash.

Spec: docs/usecases/IN/uc-23-period-gst-liability.md.
Question: "How much GST do we owe for this month, under each head, and how much of it must be
paid in cash?"

Period: the return period — the month before the run date (run with --as-of to pick another).

1. Output tax by head from posted receivable invoices dated in the period (tax source per
   document), minus outward credit notes in the period inside their s.34 window (items only, N128).
   Reverse-charge tax on period bills (notified services, genuine imports) is a separate cash line.
2. Eligible credit by head from posted bills in the period, ITC-eligible, not IMS-rejected, minus
   lines in s.17(5) blocked categories (UC-02) and registered-vendor credit notes in the period
   (clean heads only, UC-25).
3. Credit used in the statutory order (s.49, s.49A, Rule 88A): IGST credit → IGST, CGST, SGST;
   CGST credit → CGST, IGST; SGST credit → SGST, IGST; CGST never pays SGST and vice versa.
4. Rule 86B: taxable outward supplies (not exempt or zero-rated) above ₹50 lakh → at least 1% of
   output tax in cash.
5. Oracle: the period's GSTR-3B row; a head or taxable value off by more than ₹1 is
   stored_value_mismatch (the rows are round figures on this tenant — spec §6).

Rules: head_payable (context rows, one per head, citable), rcm_cash_liability, rule_86b_cash_floor,
stored_value_mismatch, data_quality (documents whose tax can't be sourced, excluded from totals).
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import CONTEXT, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.IN.uc02_blocked_credit import blocked_category
from scripts.uc.IN.uc19_credit_note_window import cutoff
from scripts.uc.common.dates import day, in_period, previous_period
from scripts.uc.common.lines import hsn, line_taxes, line_text
from scripts.uc.common.rcm import derived_liability, is_service_bill, notified_type, treatment
from scripts.uc.common.records import NOT_POSTED, party_of
from scripts.uc.common.tax import HEADS, clean_heads, doc_tax, untrusted_tax

ZERO_RATED = {"sez", "overseas", "deemed_export"}


def zero() -> dict:
    return {h: Decimal("0.00") for h in HEADS}


def _posted(doc) -> bool:
    return (doc.get("status") or "").lower() not in NOT_POSTED


def utilise(output: dict, credit: dict) -> tuple[dict, dict, dict]:
    """s.49 / s.49A / Rule 88A. Returns (cash payable, credit used, credit carried forward)."""
    out, cr = dict(output), dict(credit)
    used = zero()

    def take(src, dst):
        n = min(cr[src], out[dst])
        cr[src] -= n
        out[dst] -= n
        used[dst] += n

    for dst in ("igst", "cgst", "sgst"):
        take("igst", dst)
    take("cgst", "cgst")
    take("cgst", "igst")
    take("sgst", "sgst")
    take("sgst", "igst")
    take("cess", "cess")
    return out, used, cr


def compute(data: Dataset, ctx, period: str) -> dict:
    out, credit, rcm = zero(), zero(), Decimal("0.00")
    taxable_outward, dq = Decimal("0.00"), []
    invoices = data.index("invoices", "id")
    for inv in data.get("invoices", []):
        if inv.get("direction") != "receivable" or not _posted(inv) or not in_period(inv.get("date"), period):
            continue
        tax = doc_tax(inv)
        if tax is None:
            dq.append(("Invoice", inv))
            continue
        for h in HEADS:
            out[h] += tax[h]
        if (inv.get("gst_treatment") or "").lower() not in ZERO_RATED and tax["total"] > 0:
            taxable_outward += money(inv.get("taxable_value") or inv.get("net_total"))
    for cn in data.get("credit_notes", []):
        original = invoices.get(cn.get("invoice_id")) or {}
        if (not _posted(cn) or not in_period(cn.get("date"), period) or original.get("direction") != "receivable"
                or not day(original.get("date")) or day(cn["date"]) > cutoff(day(original["date"]), ctx)):
            continue
        tax = doc_tax(cn)
        if tax is None:
            dq.append(("CreditNote", cn))
            continue
        for h in HEADS:
            out[h] -= tax[h]

    parties, items = data.index("parties", "id"), data.index("items", "id")
    for bill in data.get("bills", []):
        if not _posted(bill) or not in_period(bill.get("date"), period):
            continue
        party = parties.get(bill.get("vendor_id"))
        if bill.get("is_reverse_charge") and (notified_type(bill, party) or (
                treatment(bill, party) == "overseas" and is_service_bill(bill))):
            kind = notified_type(bill, party)
            rcm += derived_liability(bill, ctx.constant(kind[2] if kind else "rcm_rate_services_pct"))
        if bill.get("itc_eligibility") == "ineligible" or (bill.get("ims_status") or "").lower() == "rejected":
            continue
        shares = line_taxes(bill)
        tax = doc_tax(bill)
        if tax is None or shares is None:
            dq.append(("Bill", bill))
            continue
        blocked = sum((s for line, s in shares if blocked_category(hsn(line, items), line_text(line, items))),
                      Decimal("0"))
        scale = (tax["total"] - blocked) / tax["total"] if tax["total"] > 0 else Decimal("0")
        for h in HEADS:
            credit[h] += (tax[h] * scale).quantize(CENTS)
    for vc in data.get("vendor_credits", []):
        # only a regular registered supplier's credit note carries GST we claimed (spec §5 step 2)
        if (not _posted(vc) or not in_period(vc.get("date"), period)
                or (vc.get("gst_treatment") or "").lower() != "business_gst"):
            continue
        heads = clean_heads(vc)
        if heads:
            for h in HEADS:
                credit[h] -= heads[h]
    credit = {h: max(v, Decimal("0.00")) for h, v in credit.items()}
    cash, used, carried = utilise({h: max(v, Decimal("0.00")) for h, v in out.items()}, credit)
    return {"output": out, "credit": credit, "used": used, "cash": cash, "carried": carried, "rcm": rcm,
            "taxable_outward": taxable_outward, "dq": dq}


def gstr3b(data, period: str) -> dict | None:
    mm_yyyy = f"{period[5:7]}-{period[:4]}"
    return next((r for r in data.get("returns", []) if r.get("return_type") == "GSTR-3B"
                 and r.get("return_period") == mm_yyyy), None)


class PeriodLiability(Rule):
    id = "period_liability"
    severity = 50

    def evaluate(self, data: Dataset, ctx):
        period = previous_period(ctx.as_of)
        r = compute(data, ctx, period)
        for head in HEADS:
            if r["output"][head] == 0 and r["credit"][head] == 0:
                continue
            yield Finding(
                finding_type="period_liability", rule="head_payable", severity=20, status=CONTEXT,
                entity_type="TaxPeriod", entity_id=f"{period}:{head}", entity_ref=f"{period} {head.upper()}",
                total_exposure=r["cash"][head], currency=ctx.currency,
                summary=f"{period} {head.upper()}: output {fmt(r['output'][head], ctx.currency)}, credit used "
                        f"{fmt(r['used'][head], ctx.currency)}, cash payable {fmt(r['cash'][head], ctx.currency)}.",
                details={"period": period, "head": head.upper(), "output_tax": str(r["output"][head]),
                         "eligible_credit": str(r["credit"][head]), "credit_used": str(r["used"][head]),
                         "cash_payable": str(r["cash"][head]), "credit_carried_forward": str(r["carried"][head])})
        if r["rcm"] > 0:
            yield Finding(
                finding_type="period_liability", rule="rcm_cash_liability", severity=60, entity_type="TaxPeriod",
                entity_id=f"{period}:rcm", entity_ref=f"{period} RCM", total_exposure=r["rcm"], currency=ctx.currency,
                summary=f"{period}: {fmt(r['rcm'], ctx.currency)} reverse-charge tax must be paid in cash (it can't "
                        f"come from the credit ledger).", details={"period": period})
        output_total = sum(r["output"].values(), Decimal("0"))
        cash_total = sum(r["cash"].values(), Decimal("0"))
        if r["taxable_outward"] > money(ctx.constant("rule_86b_turnover_inr")):
            floor = (output_total * Decimal(str(ctx.constant("rule_86b_cash_floor_pct"))) / 100).quantize(CENTS)
            if cash_total < floor:
                yield Finding(
                    finding_type="period_liability", rule="rule_86b_cash_floor", severity=70, entity_type="TaxPeriod",
                    entity_id=f"{period}:86b", entity_ref=f"{period} Rule 86B", total_exposure=floor - cash_total,
                    currency=ctx.currency,
                    summary=f"{period}: taxable outward supplies {fmt(r['taxable_outward'], ctx.currency)} exceed ₹50 "
                            f"lakh, so Rule 86B requires at least {fmt(floor, ctx.currency)} in cash; the credit "
                            f"computation leaves {fmt(cash_total, ctx.currency)}. Pay the difference in cash unless an "
                            f"exception (income tax paid, refunds) applies.",
                    details={"period": period, "taxable_outward": str(r["taxable_outward"]), "cash_floor": str(floor)})
        row = gstr3b(data, period)
        if row:
            diffs = {}
            ours = {"taxable": r["taxable_outward"], **{h: r["output"][h] for h in ("igst", "cgst", "sgst", "cess")}}
            theirs = {"taxable": money(row.get("taxable_amount")),
                      **{h: money(row.get(f"{h}_amount")) for h in ("igst", "cgst", "sgst", "cess")}}
            for k in ours:
                if abs(ours[k] - theirs[k]) > 1:
                    diffs[k] = {"ledger": str(ours[k]), "return": str(theirs[k])}
            if diffs:
                yield Finding(
                    finding_type="data_quality", rule="stored_value_mismatch", severity=40, status="data_quality",
                    entity_type="GSTReturn", entity_id=row["id"], entity_ref=f"GSTR-3B {row.get('return_period')}",
                    currency=ctx.currency,
                    summary=f"The {period} GSTR-3B row ({row.get('filing_status')}) does not reconcile to the ledger on "
                            f"{', '.join(diffs)} (e.g. taxable {fmt(theirs['taxable'], ctx.currency)} vs "
                            f"{fmt(ours['taxable'], ctx.currency)}); it can't be used as the oracle.",
                    details={"period": period, "differences": diffs, "net_tax_payable": row.get("net_tax_payable")})
        for entity, doc in r["dq"]:
            yield untrusted_tax(doc, entity, blocks="UC-23 period totals", currency=ctx.currency)


class PeriodGstLiability(Playbook):

    @property
    def rules(self):
        return [PeriodLiability()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice"), credit_notes=fetcher.list("CreditNote"),
                       bills=fetcher.list("Bill"), vendor_credits=fetcher.list("VendorCredit"),
                       parties=fetcher.list("Party"), items=fetcher.list("Item"), returns=fetcher.list("GSTReturn"))

    def context(self, data, findings, ctx):
        period = previous_period(ctx.as_of)
        r = compute(data, ctx, period)
        row = gstr3b(data, period) or {}
        return {"return period": period, "GSTR-3B due": f"{ctx.constant('gstr3b_due_day')} of the following month",
                "output tax": {h: str(v) for h, v in r["output"].items()},
                "eligible credit": {h: str(v) for h, v in r["credit"].items()},
                "cash payable": {h: str(v) for h, v in r["cash"].items()},
                "credit carried forward": {h: str(v) for h, v in r["carried"].items()},
                "reverse charge (cash)": str(r["rcm"]), "taxable outward supplies": str(r["taxable_outward"]),
                "documents excluded (tax unsourced)": len(r["dq"]),
                "Rule 86B": ("applies" if r["taxable_outward"] > money(ctx.constant("rule_86b_turnover_inr"))
                             else "not triggered"),
                "GSTR-3B row": {k: row.get(k) for k in ("filing_status", "taxable_amount", "net_tax_payable")}}

    def summary(self, outcome, ctx):
        c = outcome.context
        cash = {h: money(v) for h, v in c["cash payable"].items()}
        total = sum(cash.values(), Decimal("0")) + money(c["reverse charge (cash)"])
        parts = ", ".join(f"{h.upper()} {fmt(v, ctx.currency)}" for h, v in cash.items() if v)
        b86 = ("applies, cash below the 1% floor — see finding"
               if any(f.rule == "rule_86b_cash_floor" for f in outcome.findings)
               else ("applies, 1% cash floor met" if c["Rule 86B"] == "applies" else "not triggered"))
        oracle = ("does not reconcile" if any(f.entity_type == "GSTReturn" for f in outcome.findings)
                  else ("agrees" if c["GSTR-3B row"].get("filing_status") else "does not exist yet"))
        return (f"{c['return period']}: {fmt(total, ctx.currency)} payable in cash"
                + (f" ({parts})" if parts else "") + (f", including {fmt(money(c['reverse charge (cash)']), ctx.currency)} "
                                                      f"reverse charge" if money(c['reverse charge (cash)']) else "")
                + f"; Rule 86B {b86}; the GSTR-3B row "
                  f"{oracle}. {c['documents excluded (tax unsourced)']} document(s) excluded: tax can't be sourced.")
