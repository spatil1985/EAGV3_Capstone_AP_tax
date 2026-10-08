"""US-03 — Economic nexus monitoring.

Spec: docs/usecases/US/us-03-economic-nexus-monitoring.md.
Question: "Are we approaching a new state's sales tax registration obligation anywhere?"

Statute: South Dakota v. Wayfair (2018) — a remote seller must collect once its sales into a state pass
the economic-nexus threshold (typically $100,000 and/or 200 transactions, current or prior calendar
year); missed, it owes the uncollected tax itself.

Rules (calendar year to date; state = the invoice's tax-row state_code, else the customer's address):
  nexus_threshold_crossed      unregistered state over its amount or transaction threshold
  nexus_threshold_approaching  unregistered state at ≥ 80% of either threshold
  nexus_unmonitored            sales into a state with no TaxNexus row at all
  stored_value_mismatch        TaxNexus.ytd_* ≠ the recompute (the N4 regression guard)
  missing_required_field       an invoice whose state can't be placed
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day

APPROACH = Decimal("0.8")


def invoice_state(inv, parties) -> str | None:
    for row in inv.get("taxes") or []:
        if row.get("state_code"):
            return str(row["state_code"]).upper()
    party = parties.get(inv.get("party_id")) or {}
    for a in party.get("addresses") or []:
        if a.get("state"):
            return str(a["state"]).upper()[:2]
    return None


def ytd(data, ctx) -> tuple[dict, list]:
    parties = data.index("parties", "id")
    start = date(ctx.as_of.year, 1, 1)
    by, unplaced = {}, []
    for inv in data.get("invoices", []):
        d = day(inv.get("date"))
        if (inv.get("direction", "receivable") != "receivable" or not d or not (start <= d <= ctx.as_of)
                or (inv.get("status") or "").lower() in ("draft", "void", "cancelled")):
            continue
        state = invoice_state(inv, parties)
        if not state:
            unplaced.append(inv)
            continue
        row = by.setdefault(state, {"sales": Decimal("0"), "count": 0, "crossed_on": None})
        row["sales"] += money(inv.get("net_total"))
        row["count"] += 1
    return by, unplaced


class Nexus(Rule):
    id = "nexus"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        by, unplaced = ytd(data, ctx)
        nexus = {str(n.get("state_code")).upper(): n for n in data.get("nexus", [])}
        rates = {}
        for j in data.get("jurisdictions", []):
            rates[str(j.get("state_code")).upper()] = rates.get(str(j.get("state_code")).upper(), Decimal("0")) + \
                money(j.get("rate_percentage"))
        for state, row in sorted(by.items()):
            n = nexus.get(state)
            if not n:
                yield Finding(finding_type="nexus", rule="nexus_unmonitored", severity=60, entity_type="State",
                              entity_id=state, entity_ref=state, total_exposure=row["sales"], currency=ctx.currency,
                              summary=f"{fmt(row['sales'], ctx.currency)} of sales ({row['count']} invoices) went to {state} "
                                      f"this year, but no nexus record watches that state.", details=row)
                continue
            stored_sales, stored_count = money(n.get("ytd_sales_amount")), int(money(n.get("ytd_transaction_count")))
            if abs(stored_sales - row["sales"]) > 1 or stored_count != row["count"]:
                yield Finding(finding_type=DATA_QUALITY, rule="stored_value_mismatch", status=DATA_QUALITY, severity=40,
                              entity_type="TaxNexus", entity_id=n["id"], entity_ref=state, currency=ctx.currency,
                              summary=f"{state} nexus counters say {fmt(stored_sales, ctx.currency)} / {stored_count}; "
                                      f"invoices give {fmt(row['sales'], ctx.currency)} / {row['count']}.",
                              details={"stored": [str(stored_sales), stored_count], "recomputed": [str(row["sales"]), row["count"]]})
            if n.get("is_registered"):
                continue
            amount_line = money(n.get("economic_threshold_amount"))
            count_line = int(money(n.get("economic_threshold_transactions")))
            over = (amount_line and row["sales"] > amount_line) or (count_line and row["count"] >= count_line)
            near = (amount_line and row["sales"] >= amount_line * APPROACH) or \
                   (count_line and row["count"] >= count_line * APPROACH)
            if over or near:
                risk = ((row["sales"] - amount_line) * rates.get(state, Decimal("0")) / 100).quantize(CENTS) if over else Decimal("0")
                yield Finding(
                    finding_type="nexus", rule="nexus_threshold_crossed" if over else "nexus_threshold_approaching",
                    severity=85 if over else 55, entity_type="TaxNexus", entity_id=n["id"], entity_ref=state,
                    total_exposure=max(risk, Decimal("0")), currency=ctx.currency,
                    summary=f"{state}: {fmt(row['sales'], ctx.currency)} / {row['count']} transactions this year against a "
                            f"{fmt(amount_line, ctx.currency)} / {count_line} threshold — "
                            + ("economic nexus is crossed and we aren't registered: register and start collecting."
                               if over else "at 80% or more of the threshold; plan registration."),
                    details={"ytd_sales": str(row["sales"]), "ytd_count": row["count"], "threshold": str(amount_line),
                             "threshold_transactions": count_line, "status": n.get("status")})
        if unplaced:
            yield Finding(finding_type=DATA_QUALITY, rule="missing_required_field", status=DATA_QUALITY, severity=20,
                          entity_type="Invoices", entity_id="unplaced", entity_ref=f"{len(unplaced)} invoices",
                          currency=ctx.currency,
                          summary=f"{len(unplaced)} invoice(s) have no tax row and a customer with no address, so their "
                                  f"state can't be placed.", details={"invoices": [i.get("number") for i in unplaced][:50]})


class EconomicNexus(Playbook):

    @property
    def rules(self):
        return [Nexus()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice"), parties=fetcher.list("Party"),
                       nexus=fetcher.list("TaxNexus"), jurisdictions=fetcher.list("TaxJurisdiction"))

    def context(self, data, findings, ctx):
        by, _ = ytd(data, ctx)
        nexus = {str(n.get("state_code")).upper(): n for n in data["nexus"]}
        return {"YTD sales by state": {s: f"{r['sales']} / {r['count']}" for s, r in sorted(by.items())},
                "registered": sorted(s for s, n in nexus.items() if n.get("is_registered")),
                "monitoring": sorted(s for s, n in nexus.items() if not n.get("is_registered"))}

    def summary(self, outcome, ctx):
        crossed = [f.entity_ref for f in outcome.findings if f.rule == "nexus_threshold_crossed"]
        near = [f.entity_ref for f in outcome.findings if f.rule == "nexus_threshold_approaching"]
        unmon = [f.entity_ref for f in outcome.findings if f.rule == "nexus_unmonitored"]
        mismatch = any(f.rule == "stored_value_mismatch" for f in outcome.findings)
        if not (crossed or near or unmon):
            return (f"No unregistered state is near an economic-nexus threshold; all sales this year are in "
                    f"{', '.join(outcome.context['registered'])}, where we are registered. "
                    + ("Platform counters disagree with invoices." if mismatch else "Platform counters agree with invoices."))
        return (f"Nexus crossed in {crossed or 'no state'}; approaching in {near or 'no state'}; unmonitored sales into "
                f"{unmon or 'no state'}." + (" Platform counters disagree with invoices." if mismatch else ""))
