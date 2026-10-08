"""UC-29 — Turnover-based GST obligations: which apply this year, and are we meeting them?

Spec: docs/usecases/IN/uc-29-turnover-based-obligations.md.
Question: "Given our turnover, which GST obligations apply to us this year, and are we meeting them?"

Aggregate annual turnover (AATO, previous FY, PAN level, taxes excluded) switches obligations on:
e-invoicing above ₹5 crore (Rule 48(4); an invoice without IRN is not a valid tax invoice, Rule 48(5)),
6-digit HSN above ₹5 crore, QRMP only up to ₹5 crore, GSTR-9 optional up to ₹2 crore, GSTR-9C above
₹5 crore, composition up to ₹1.5 crore, the s.194Q buyer test above ₹10 crore.

Turnover comes from live receivable invoices minus credit notes; when the ledger starts mid-year the
figure is a floor, and a line it doesn't clear is "undeterminable", never "does not apply".

Rules:
  einvoice_required_not_generated  AATO above the line, e-invoicing not enabled / no IRN: aggregate of
                                   the current FY's B2B, SEZ and export invoices (GST-28 is a
                                   platform-documented gap, but the exposure is real)
  qrmp_ineligible                  quarterly filing with AATO above ₹5 crore
  threshold_will_cross             the current FY's run rate crosses a line the previous FY didn't
  data_quality                     e-invoicing switched on in OrgProfile but off in its preferences
The obligation matrix is in the run context.
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day, fy_label, fy_start
from scripts.uc.common.records import NOT_POSTED

LINES = [  # (obligation, constant, applies when AATO is above?)
    ("e-invoicing (IRN)", "aato_einvoice_inr", True),
    ("6-digit HSN on B2B invoices", "hsn_aato_inr", True),
    ("GSTR-9C reconciliation", "aato_gstr9c_inr", True),
    ("GSTR-9 annual return mandatory", "aato_gstr9_optional_inr", True),
    ("s.194Q buyer TDS", "tds_194q_buyer_turnover_inr", True),
    ("QRMP quarterly filing allowed", "aato_qrmp_max_inr", False),
    ("composition scheme available", "aato_composition_max_inr", False),
]
EINVOICE_TREATMENTS = {"business_gst", "sez", "overseas", "deemed_export"}


def line_value(name, ctx, on):
    if name == "hsn_aato_inr":
        return money(ctx.rule("aato_einvoice_inr", on))
    return money(ctx.rule(name, on))


def turnover(data, start: date, end: date) -> tuple[Decimal, date | None]:
    total, first = Decimal("0"), None
    for inv in data.get("invoices", []):
        d = day(inv.get("date"))
        if (inv.get("direction") == "receivable" and d and start <= d <= end
                and (inv.get("status") or "").lower() not in NOT_POSTED):
            total += money(inv.get("taxable_value"))
            first = min(first, d) if first else d
    for cn in data.get("credit_notes", []):
        d = day(cn.get("date"))
        if d and start <= d <= end and (cn.get("status") or "").lower() not in NOT_POSTED:
            total -= money(cn.get("taxable_value"))
    return total, first


class TurnoverObligations(Rule):
    id = "turnover_obligation"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        cur_start = fy_start(ctx.as_of, "gst")
        prev_start = date(cur_start.year - 1, 4, 1)
        prev, prev_first = turnover(data, prev_start, date(cur_start.year, 3, 31))
        floor = prev_first is None or prev_first > prev_start
        einv_line = line_value("aato_einvoice_inr", ctx, ctx.as_of)
        org = (data.get("org") or [{}])[0]
        prefs = (data.get("einvoice_prefs") or [{}])[0]
        if prev > einv_line and not prefs.get("enabled"):
            invs = [i for i in data.get("invoices", []) if i.get("direction") == "receivable"
                    and (i.get("status") or "").lower() not in NOT_POSTED and (day(i.get("date")) or cur_start) >= cur_start
                    and (i.get("gst_treatment") or "").lower() in EINVOICE_TREATMENTS and not i.get("irn")]
            value = sum((money(i.get("grand_total")) for i in invs), Decimal("0"))
            tax = sum((money(i.get("total_tax")) for i in invs), Decimal("0"))
            yield Finding(
                finding_type="turnover_obligation", rule="einvoice_required_not_generated", severity=85,
                entity_type="Invoices", entity_id=f"einvoice:{fy_label(ctx.as_of, 'gst')}",
                entity_ref=f"{len(invs)} invoices", total_exposure=tax, currency=ctx.currency,
                summary=f"{fy_label(prev_start, 'gst')} turnover is {'at least ' if floor else ''}"
                        f"{fmt(prev, ctx.currency)}, above the {fmt(einv_line, ctx.currency)} line, so e-invoicing is "
                        f"mandatory. {len(invs)} B2B/SEZ/export invoice(s) this FY ({fmt(value, ctx.currency)}) carry no "
                        f"IRN and are not valid tax invoices for the buyers' credit (Rule 48(5)). The platform can't "
                        f"generate IRNs today (GST-28, documented).",
                details={"aato_previous_fy": str(prev), "aato_is_floor": floor, "invoices": len(invs),
                         "invoice_value": str(value), "einvoicing_enabled": prefs.get("enabled"),
                         "platform_gap": "GST-28 (locale not_yet_supported)"})
        if org.get("enable_e_invoicing") and not prefs.get("enabled"):
            yield Finding(
                finding_type=DATA_QUALITY, rule="classification_conflict", status=DATA_QUALITY, severity=15,
                entity_type="EInvoicingPreferences", entity_id=prefs.get("id") or "einvoicing",
                entity_ref="e-invoicing settings", currency=ctx.currency,
                summary=f"OrgProfile.enable_e_invoicing is on but EInvoicingPreferences.enabled is off "
                        f"(sandbox_mode {prefs.get('sandbox_mode')}): the settings contradict each other.",
                details={"org_enable_e_invoicing": org.get("enable_e_invoicing"), "prefs": {
                    k: prefs.get(k) for k in ("enabled", "auto_generate_irn", "sandbox_mode")}})
        frequency = (data.get("locale") or {}).get("gst_filing_frequency")
        if frequency == "quarterly" and prev > money(ctx.constant("aato_qrmp_max_inr")):
            yield Finding(
                finding_type="turnover_obligation", rule="qrmp_ineligible", severity=70, entity_type="Locale",
                entity_id="filing_frequency", entity_ref="quarterly filing", currency=ctx.currency,
                summary=f"Filing is quarterly, but turnover {fmt(prev, ctx.currency)} is above ₹5 crore: QRMP is not "
                        f"available; file monthly.", details={"aato_previous_fy": str(prev)})
        cur, cur_first = turnover(data, cur_start, ctx.as_of)
        months = max(1, (ctx.as_of.year - cur_start.year) * 12 + ctx.as_of.month - cur_start.month + 1)
        projected = cur / months * 12
        for name, const, above in LINES:
            limit = line_value(const, ctx, ctx.as_of)
            if (prev <= limit) and projected > limit:
                yield Finding(
                    finding_type="turnover_obligation", rule="threshold_will_cross", severity=50,
                    entity_type="Obligation", entity_id=const, entity_ref=name, currency=ctx.currency,
                    summary=f"At this year's run rate ({fmt(projected, ctx.currency)} projected), turnover crosses the "
                            f"{fmt(limit, ctx.currency)} line for {name}; it changes from next FY.",
                    details={"current_fy_to_date": str(cur), "months": months, "projected": str(projected),
                             "line": str(limit), "applies_above": above})


class TurnoverBasedObligations(Playbook):

    @property
    def rules(self):
        return [TurnoverObligations()]

    def fetch(self, ctx, fetcher) -> Dataset:
        locale = fetcher.rest_get("/api/accounting/locale")
        return Dataset(invoices=fetcher.list("Invoice", direction="receivable"), credit_notes=fetcher.list("CreditNote"),
                       org=fetcher.list("OrgProfile"), einvoice_prefs=fetcher.list("EInvoicingPreferences"),
                       locations=fetcher.list("Location"), locale=locale.get("locale", locale))

    def context(self, data, findings, ctx):
        cur_start = fy_start(ctx.as_of, "gst")
        prev_start = date(cur_start.year - 1, 4, 1)
        prev, first = turnover(data, prev_start, date(cur_start.year, 3, 31))
        floor = first is None or first > prev_start
        matrix = {}
        for name, const, above in LINES:
            limit = line_value(const, ctx, ctx.as_of)
            if prev > limit:
                verdict = "applies" if above else "does not apply"
            elif floor:
                verdict = "undeterminable (turnover is a floor)"
            else:
                verdict = "does not apply" if above else "applies"
            matrix[name] = f"{verdict} (line {limit})"
        return {f"turnover {fy_label(prev_start, 'gst')}": str(prev), "turnover is a floor": floor,
                "ledger starts": str(first) if first else None,
                f"turnover {fy_label(ctx.as_of, 'gst')} to date": str(turnover(data, cur_start, ctx.as_of)[0]),
                "obligation matrix": matrix, "GSTINs under the PAN (Location)": len(data["locations"]),
                "filing frequency": (data.get("locale") or {}).get("gst_filing_frequency")}

    def summary(self, outcome, ctx):
        c = outcome.context
        key = next(k for k in c if k.startswith("turnover FY") and "to date" not in k)
        einv = next((f for f in outcome.findings if f.rule == "einvoice_required_not_generated"), None)
        return (f"{key.replace('turnover ', '')} turnover is {'at least ' if c['turnover is a floor'] else ''}"
                f"{fmt(money(c[key]), ctx.currency)}. "
                + (f"E-invoicing is mandatory: {einv.details['invoices']} invoice(s) this FY carry no IRN. "
                   if einv else "")
                + f"Obligations: {c['obligation matrix']}.")
