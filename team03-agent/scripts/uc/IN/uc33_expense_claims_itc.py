"""UC-33 — GST credit claimed on expense claims.

Spec: docs/usecases/IN/uc-33-expense-claims-itc.md.
Question: "Are we claiming GST credit on expense claims where the law says we can't?"

Statute: s.17(5)(g) (goods/services for personal consumption), s.17(5)(a)/(b) (vehicles, food,
clubs, health, travel benefits), s.16(2)(a) (credit needs a tax invoice with the supplier's GSTIN),
Schedule III (salaries are not a supply), s.9(3) notified RCM list.

One finding per expense, led by its most serious rule; the others are listed in `also`:
  itc_on_personal_expense     is_personal with credit claimed
  itc_blocked_category        account or description in a s.17(5) category (UC-02's table)
  gst_on_non_supply           tax on salaries, wages, PF/ESI, loan or interest accounts
  itc_without_supplier_gstin  credit claimed with no GSTIN on the expense or the vendor
  rcm_on_registered_supplier  reverse charge on a business_gst supplier outside the notified list
  classification_conflict     sez/deemed_export treatment on a purchase (outward categories)
  tax_exceeds_possible_rate   (data_quality) tax above 40% of the amount; excluded from totals
"""

import re
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.IN.uc02_blocked_credit import blocked_category

CLAIMING = {"input", "input_services", "capital_goods"}
NON_SUPPLY = re.compile(r"salar|wage|payroll|\bEPF\b|provident|\bESI|gratuity|loan|interest", re.I)
ORDER = ["itc_on_personal_expense", "itc_blocked_category", "gst_on_non_supply", "itc_without_supplier_gstin",
         "rcm_on_registered_supplier", "classification_conflict", "tax_exceeds_possible_rate"]
SEVERITY = dict(zip(ORDER, (85, 75, 70, 60, 45, 35, 10)))
MAX_RATE = Decimal("0.40")


def checks(exp, parties) -> list[str]:
    hits = []
    tax, amount = money(exp.get("tax_amount")), money(exp.get("amount"))
    claiming = exp.get("itc_eligibility") in CLAIMING and tax > 0
    text = f"{exp.get('_account_id_display') or ''} {exp.get('description') or ''} {exp.get('expense_type') or ''}"
    if claiming and exp.get("is_personal"):
        hits.append("itc_on_personal_expense")
    if claiming and blocked_category(str(exp.get("hsn_or_sac") or ""), text.lower()):
        hits.append("itc_blocked_category")
    if tax > 0 and NON_SUPPLY.search(str(exp.get("_account_id_display") or "")):
        hits.append("gst_on_non_supply")
    if claiming and not exp.get("gst_no") and not (parties.get(exp.get("vendor_id")) or {}).get("gst_no"):
        hits.append("itc_without_supplier_gstin")
    if exp.get("is_reverse_charge") and (exp.get("gst_treatment") or "").lower() == "business_gst":
        hits.append("rcm_on_registered_supplier")
    if (exp.get("gst_treatment") or "").lower() in ("sez", "deemed_export"):
        hits.append("classification_conflict")
    if amount > 0 and tax / amount > MAX_RATE:
        hits.append("tax_exceeds_possible_rate")
    return hits


class ExpenseItc(Rule):
    id = "expense_itc"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        parties = data.index("parties", "id")
        for exp in data.get("expenses", []):
            if (exp.get("status") or "").lower() in ("draft", "void", "cancelled"):
                continue
            hits = checks(exp, parties)
            if not hits:
                continue
            hits.sort(key=ORDER.index)
            lead = hits[0]
            tax, amount = money(exp.get("tax_amount")), money(exp.get("amount"))
            dq = "tax_exceeds_possible_rate" in hits
            label = exp.get("number") or exp.get("entry_number") or exp["id"]
            text = {
                "itc_on_personal_expense": "is a personal expense claiming GST credit, which s.17(5)(g) blocks",
                "itc_blocked_category": f"is in a blocked s.17(5) category ({exp.get('_account_id_display')})",
                "gst_on_non_supply": f"carries GST on {exp.get('_account_id_display')}, which is not a supply",
                "itc_without_supplier_gstin": "claims credit with no supplier GSTIN (s.16(2)(a))",
                "rcm_on_registered_supplier": "is flagged reverse charge on a registered supplier",
                "classification_conflict": f"uses the outward category '{exp.get('gst_treatment')}' on a purchase",
                "tax_exceeds_possible_rate": "carries more tax than any GST rate allows",
            }[lead]
            yield Finding(
                finding_type=DATA_QUALITY if lead == "tax_exceeds_possible_rate" else "expense_itc", rule=lead,
                severity=SEVERITY[lead], status=DATA_QUALITY if lead == "tax_exceeds_possible_rate" else "finding",
                entity_type="Expense", entity_id=exp["id"], entity_ref=label,
                total_exposure=Decimal("0") if dq else tax, reversal_base_amount=Decimal("0") if dq else tax,
                currency=ctx.currency,
                summary=f"Expense {label} ({exp.get('date')}, {fmt(amount, ctx.currency)}, tax {fmt(tax, ctx.currency)}) "
                        f"{text}." + (" Its tax is also above 40% of the amount, so it is excluded from totals."
                                      if dq and lead != "tax_exceeds_possible_rate" else ""),
                details={"also": hits[1:], "amount": str(amount), "tax_amount": str(tax),
                         "itc_eligibility": exp.get("itc_eligibility"), "account": exp.get("_account_id_display"),
                         "excluded_from_totals": dq},
            )


class ExpenseClaimsItc(Playbook):

    @property
    def rules(self):
        return [ExpenseItc()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(expenses=fetcher.list("Expense"), parties=fetcher.list("Party"))

    @staticmethod
    def sort_key(f):
        return (ORDER.index(f.rule), -f.total_exposure)

    def context(self, data, findings, ctx):
        exps = data["expenses"]
        return {"expenses": len(exps), "with tax": sum(1 for e in exps if money(e.get("tax_amount")) > 0),
                "claiming credit": sum(1 for e in exps if e.get("itc_eligibility") in CLAIMING)}

    def summary(self, outcome, ctx):
        def agg(rule):
            rows = [f for f in outcome.findings if f.rule == rule or rule in f.details.get("also", [])]
            return len(rows), sum((f.total_exposure for f in rows if f.rule == rule), Decimal("0"))
        p, ptax = agg("itc_on_personal_expense")
        g, _ = agg("itc_without_supplier_gstin")
        dq, _ = agg("tax_exceeds_possible_rate")
        ns, nstax = agg("gst_on_non_supply")
        return (f"{p} personal expense claim(s) carry {fmt(ptax, ctx.currency)} of GST credit that s.17(5)(g) blocks "
                f"(excluding implausible tax). {ns} carry GST on non-supplies; {g} claim credit with no supplier GSTIN; "
                f"{dq} expense record(s) carry more tax than any GST rate allows.")
