"""UC-39 — TDS deductor setup and section coverage.

Spec: docs/usecases/IN/uc-39-tds-deductor-setup.md.
Question: "Are we set up to deduct TDS at all, and are we deducting under every section that applies
to what we pay?"

Statute (Income-tax Act 1961 numbering — confirm): s.203A (TAN required to deduct and deposit), ss.194A
(interest), 194H (commission), 194R (business perquisites); s.40(a)(ia) disallows 30% of an expense
when TDS was not deducted. Interest under MSMED s.16 is also not deductible at all (MSMED s.23).

Rules:
  tan_missing               TDS switched on with no TAN: nothing can be deposited or reported
  tds_section_code_invalid  a bill with TDS fields whose code isn't a statutory section (seeded codes like
                            C5341/9637) or whose rate matches no section
  tds_section_not_applied   per payee per FY: interest / commission / perquisite accounts above the
                            section threshold with no TDS (expenses and bill lines, by account name)
TDS deposits (challans) aren't tracked on the platform (GST-18), so deposit timeliness is context only.
"""

import re
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import add_months, day, fy_start
from scripts.uc.common.records import NOT_POSTED
from scripts.uc.common.tds import stored

VALID_SECTION = re.compile(r"^19[2-6][A-Z]{0,2}(\(\w+\))?$|^206[A-Z]{0,2}", re.I)
STATUTORY_RATES = {Decimal(x) for x in ("0.1", "1", "2", "5", "10", "20", "30")}
COVERAGE = [  # (section, account pattern, threshold constant, rate constant)
    ("194A", re.compile(r"interest", re.I), "tds_194a_threshold_inr", "tds_194a_rate_pct"),
    ("194H", re.compile(r"commission|brokerage", re.I), "tds_194h_threshold_inr", "tds_194h_rate_pct"),
    ("194R", re.compile(r"gift|sample|perquisite|sponsored travel", re.I), "tds_194r_threshold_inr", "tds_194r_rate_pct"),
]


def payments(data, ctx):
    """(payee id, payee name, account text, amount, tds) for this FY's expenses and bill lines."""
    start = fy_start(ctx.as_of, ctx.tax_regime)
    for e in data.get("expenses", []):
        if (e.get("status") or "").lower() in ("draft", "void", "cancelled") or (day(e.get("date")) or start) < start:
            continue
        yield (e.get("vendor_id") or e.get("claimant_email") or e["id"], e.get("_vendor_id_display") or e.get("claimant_email"),
               str(e.get("_account_id_display") or ""), money(e.get("amount")), money(e.get("tds_amount")))
    for b in data.get("bills", []):
        if (b.get("status") or "").lower() in NOT_POSTED or (day(b.get("date")) or start) < start:
            continue
        tds = stored(b)[0]
        for line in b.get("items") or []:
            yield (b.get("vendor_id"), b.get("_vendor_id_display"), str(line.get("account_id") or ""),
                   money(line.get("taxable_amount") or line.get("amount")), tds)


class TdsSetup(Rule):
    id = "tds_setup"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        org = (data.get("org") or [{}])[0]
        if org.get("enable_tds") and not org.get("tan"):
            yield Finding(finding_type="tds_setup", rule="tan_missing", severity=85, entity_type="OrgProfile",
                          entity_id=org.get("id") or "org", entity_ref="company TDS setup", currency=ctx.currency,
                          summary="TDS is switched on but the company has no TAN: TDS can't be deposited or reported "
                                  "(s.203A).", details={"enable_tds": org.get("enable_tds"), "tan": None})
        for bill in data.get("bills", []):
            if (bill.get("status") or "").lower() in NOT_POSTED - {"draft"} or (bill.get("status") or "") == "void":
                continue
            amount, pct, section = stored(bill)
            code = bill.get("_suspect_tds_section_code") or bill.get("tds_section_code")
            if amount <= 0 and not pct:
                continue
            valid_code = bool(section and VALID_SECTION.match(str(section))) or bool(code and VALID_SECTION.match(str(code)))
            valid_rate = pct in STATUTORY_RATES
            if not (valid_code and valid_rate):
                yield Finding(finding_type=DATA_QUALITY, rule="tds_section_code_invalid", status=DATA_QUALITY,
                              severity=40, entity_type="Bill", entity_id=bill["id"], entity_ref=bill.get("number"),
                              currency=ctx.currency,
                              summary=f"{bill.get('number')} carries TDS ({pct}%) under code '{code}', which is not a "
                                      f"statutory section" + ("" if valid_rate else f", and {pct}% matches no section's rate")
                                      + ".", details={"tds_section_code": code, "tds_section": section,
                                                      "tds_percentage": str(pct)})
        totals: dict = {}
        for payee, name, account, amount, tds in payments(data, ctx):
            for section, pattern, threshold, rate in COVERAGE:
                if pattern.search(account):
                    row = totals.setdefault((section, payee), {"name": name, "total": Decimal("0"),
                                                               "tds": Decimal("0"), "accounts": set()})
                    row["total"] += amount
                    row["tds"] += tds
                    row["accounts"].add(account)
        for (section, payee), row in sorted(totals.items(), key=lambda kv: -kv[1]["total"]):
            _, _, threshold, rate_name = next(c for c in COVERAGE if c[0] == section)
            limit, rate = money(ctx.rule(threshold)), Decimal(str(ctx.rule(rate_name)))
            if row["total"] <= limit or row["tds"] > 0:
                continue
            due = (row["total"] * rate / 100).quantize(CENTS)
            msme = any("msme" in a.lower() for a in row["accounts"])
            yield Finding(
                finding_type="tds_setup", rule="tds_section_not_applied", severity=self.severity, entity_type="Payee",
                entity_id=f"{section}:{payee}", entity_ref=f"{row['name']} ({section})", total_exposure=due,
                currency=ctx.currency, counterparty_id=payee, counterparty_name=row["name"],
                summary=f"{fmt(row['total'], ctx.currency)} paid to {row['name']} this FY on {', '.join(sorted(row['accounts']))} "
                        f"is above the {section} threshold ({fmt(limit, ctx.currency)}) with no TDS: "
                        f"{fmt(due, ctx.currency)} due at {rate}%, and 30% of the expense is disallowed (s.40(a)(ia))."
                        + (" MSME interest under MSMED s.16 is not deductible at all (MSMED s.23)." if msme else ""),
                details={"section": section, "payee_id": payee, "fy_total": str(row["total"]), "threshold": str(limit),
                         "rate": str(rate), "tds_due": str(due),
                         "disallowance_risk": str((row["total"] * Decimal("0.30")).quantize(CENTS))})


class TdsDeductorSetup(Playbook):

    @property
    def rules(self):
        return [TdsSetup()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(org=fetcher.list("OrgProfile"), prefs=fetcher.list("DirectTaxPreferences"),
                       bills=fetcher.list("Bill"), expenses=fetcher.list("Expense"), payments=fetcher.list("PaymentMade"))

    def context(self, data, findings, ctx):
        prefs = (data.get("prefs") or [{}])[0]
        nxt = add_months(ctx.as_of.replace(day=1), 1).replace(day=7)
        return {"auto_apply_tds": prefs.get("auto_apply_tds"), "default_tds_section": prefs.get("default_tds_section"),
                "payments with TDS": sum(1 for p in data["payments"] if money(p.get("tds_amount")) > 0),
                "next TDS deposit due": str(nxt),
                "deposits": "challans not tracked on the platform (GST-18); can't be verified"}

    def summary(self, outcome, ctx):
        tan = any(f.rule == "tan_missing" for f in outcome.findings)
        bad = sum(1 for f in outcome.findings if f.rule == "tds_section_code_invalid")
        miss = [f for f in outcome.findings if f.rule == "tds_section_not_applied"]
        due = sum((f.total_exposure for f in miss), Decimal("0"))
        return (("TDS is switched on but the company has no TAN. " if tan else "")
                + f"{bad} bill(s) carry TDS under a non-statutory section code. {len(miss)} payee(s) are above a "
                  f"194A/194H/194R threshold with no TDS ({fmt(due, ctx.currency)} due).")
