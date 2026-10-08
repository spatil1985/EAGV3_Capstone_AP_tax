"""UC-26 — GSTR-1 readiness: every sale in the right table, with the right kind of GST.

Spec: docs/usecases/IN/uc-26-gstr1-readiness.md.
Question: "Is every sale this month going into the right part of GSTR-1, with the right kind of GST?"

Statute: s.37 + Rule 59 (GSTR-1 tables: 4 B2B, 5 B2CL, 6 exports/SEZ, 7 B2CS, 8 nil/exempt, 9 notes);
s.7–8 IGST Act (inter-state → IGST, intra-state → CGST+SGST by place of supply); Notification
78/2020-CT (HSN digits); Notification 12/2024-CT (B2CL threshold ₹1 lakh — confirm).

Rules (on every live receivable invoice — a standing audit):
  wrong_tax_head_for_pos        supplier state ≠ place of supply but CGST/SGST charged, or the reverse
  b2b_without_gstin             business_gst sale with no recipient GSTIN on invoice or party
  hsn_missing / hsn_digits_short  a live line with no HSN, or fewer digits than required
  table_classification_missing  gst_treatment blank, so no table can be chosen
  stored_value_mismatch         the filing period's GSTR-1 row vs the ledger (taxable, documents)
The filing period's table preview (count and taxable value per table) is in the run context.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day, in_period, previous_period
from scripts.uc.common.records import NOT_POSTED, party_of
from scripts.uc.common.tax import doc_tax

EXPORTS = {"sez", "deemed_export", "overseas"}
B2C = {"consumer", "unregistered_business", "unregistered"}


def live_sales(data):
    return [i for i in data.get("invoices", []) if i.get("direction") == "receivable"
            and (i.get("status") or "").lower() not in NOT_POSTED]


def supplier_state(data) -> str | None:
    org = (data.get("org") or [{}])[0]
    gstin = str(org.get("gstin") or "")
    return gstin[:2] if len(gstin) >= 2 else None


def pos_code(inv) -> str:
    return str(inv.get("place_of_supply") or "").strip()[:2]


def table_for(inv, data, ctx) -> str:
    t = (inv.get("gst_treatment") or "").lower()
    if t in EXPORTS:
        return "6"
    if t == "business_gst":
        return "4"
    inter = supplier_state(data) and pos_code(inv) and pos_code(inv) != supplier_state(data)
    limit = money(ctx.rule("gstr1_b2cl_threshold_inr", day(inv.get("date"))))
    if t in B2C and inter and money(inv.get("grand_total")) > limit:
        return "5"
    return "7" if t else "unclassified"


class Gstr1Readiness(Rule):
    id = "outward_return"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        home = supplier_state(data)
        parties = data.index("parties", "id")
        min_digits = int(ctx.constant("hsn_min_digits_above_5cr"))
        for inv in live_sales(data):
            number = inv.get("number")
            pid, pname = party_of(inv, data)
            base = dict(entity_type="Invoice", entity_id=inv["id"], entity_ref=number, currency=ctx.currency,
                        counterparty_id=pid, counterparty_name=pname)
            treatment = (inv.get("gst_treatment") or "").lower()
            tax = doc_tax(inv)
            pos = pos_code(inv)
            if tax and home and pos and treatment not in EXPORTS:
                local = tax["cgst"] + tax["sgst"]
                if pos != home and local > 0:
                    yield Finding(finding_type="outward_return", rule="wrong_tax_head_for_pos", severity=75,
                                  total_exposure=local, **base,
                                  summary=f"{number} ({inv.get('date')}) has place of supply {pos}, outside {home}, but "
                                          f"was charged CGST+SGST {fmt(local, ctx.currency)} where IGST was due: pay it "
                                          f"again as IGST and claim back the wrong-head tax.",
                                  details={"place_of_supply": pos, "supplier_state": home, "charged": "CGST+SGST",
                                           "taxable_value": str(money(inv.get("taxable_value")))})
                elif pos == home and tax["igst"] > 0:
                    yield Finding(finding_type="outward_return", rule="wrong_tax_head_for_pos", severity=75,
                                  total_exposure=tax["igst"], **base,
                                  summary=f"{number} is intra-state (place of supply {pos}) but was charged IGST "
                                          f"{fmt(tax['igst'], ctx.currency)}; CGST+SGST were due.",
                                  details={"place_of_supply": pos, "supplier_state": home, "charged": "IGST"})
            if treatment == "business_gst" and not inv.get("gst_no") and not (parties.get(pid) or {}).get("gst_no"):
                yield Finding(finding_type="outward_return", rule="b2b_without_gstin", severity=60, **base,
                              total_exposure=money(inv.get("taxable_value")),
                              summary=f"{number} is a B2B sale to {pname} with no recipient GSTIN: it can't go into "
                                      f"Table 4, and the customer can't claim the credit.", details={})
            if not treatment:
                yield Finding(finding_type=DATA_QUALITY, rule="table_classification_missing", status=DATA_QUALITY,
                              severity=30, **base,
                              summary=f"{number} has no gst_treatment, so its GSTR-1 table can't be chosen.",
                              details={"field": "gst_treatment"})
            for i, line in enumerate(inv.get("items") or []):
                code = "".join(ch for ch in str(line.get("hsn_or_sac") or "") if ch.isdigit())
                if not code:
                    rule, text = "hsn_missing", "has no HSN/SAC"
                elif len(code) < min_digits and treatment == "business_gst":
                    rule, text = "hsn_digits_short", f"has a {len(code)}-digit HSN; {min_digits} are required"
                else:
                    continue
                yield Finding(finding_type="outward_return", rule=rule, severity=35, **base,
                              summary=f"{number} line {i + 1} {text} (Table 12 HSN summary).",
                              details={"line_index": i, "hsn_or_sac": line.get("hsn_or_sac")})
        period = previous_period(ctx.as_of)
        row = next((r for r in data.get("returns", []) if r.get("return_type") == "GSTR-1"
                    and r.get("return_period") == f"{period[5:]}-{period[:4]}"), None)
        if row:
            docs = [i for i in live_sales(data) if in_period(i.get("date"), period)]
            taxable = sum((money(i.get("taxable_value")) for i in docs), Decimal("0"))
            if abs(taxable - money(row.get("taxable_amount"))) > 1 or len(docs) != int(money(row.get("total_transactions"))):
                yield Finding(finding_type=DATA_QUALITY, rule="stored_value_mismatch", status=DATA_QUALITY, severity=40,
                              entity_type="GSTReturn", entity_id=row["id"], entity_ref=f"GSTR-1 {row.get('return_period')}",
                              currency=ctx.currency,
                              summary=f"The {period} GSTR-1 row ({row.get('filing_status')}) says "
                                      f"{fmt(money(row.get('taxable_amount')), ctx.currency)} over "
                                      f"{int(money(row.get('total_transactions')))} documents; the ledger has "
                                      f"{fmt(taxable, ctx.currency)} over {len(docs)}.",
                              details={"period": period, "ledger_taxable": str(taxable), "ledger_documents": len(docs)})


class Gstr1ReadinessAudit(Playbook):

    @property
    def rules(self):
        return [Gstr1Readiness()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice", direction="receivable"), parties=fetcher.list("Party"),
                       org=fetcher.list("OrgProfile"), returns=fetcher.list("GSTReturn"))

    def context(self, data, findings, ctx):
        period = previous_period(ctx.as_of)
        preview: dict = {}
        for inv in live_sales(data):
            if in_period(inv.get("date"), period):
                row = preview.setdefault(f"Table {table_for(inv, data, ctx)}", [0, Decimal("0")])
                row[0] += 1
                row[1] += money(inv.get("taxable_value"))
        tables: dict = {}
        for inv in live_sales(data):
            tables[table_for(inv, data, ctx)] = tables.get(table_for(inv, data, ctx), 0) + 1
        return {"live receivable invoices": len(live_sales(data)), "supplier state": supplier_state(data),
                f"GSTR-1 preview {period}": {k: f"{n} docs, {v}" for k, (n, v) in sorted(preview.items())},
                "all live invoices by table": dict(sorted(tables.items()))}

    def summary(self, outcome, ctx):
        wrong = [f for f in outcome.findings if f.rule == "wrong_tax_head_for_pos"]
        tax = sum((f.total_exposure for f in wrong), Decimal("0"))
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"{len(wrong)} invoice(s) charged the wrong kind of GST for their place of supply "
                f"({fmt(tax, ctx.currency)}); {n('b2b_without_gstin')} B2B sale(s) lack a GSTIN; "
                f"{n('hsn_missing') + n('hsn_digits_short')} line(s) have missing or short HSN. Tables: "
                f"{outcome.context['all live invoices by table']}.")
