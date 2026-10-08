"""US-05 — Sourcing and rate correctness on sales.

Spec: docs/usecases/US/us-05-sourcing-and-rate-correctness.md.
Question: "Are we charging each customer the right state and local rate for where the sale is sourced?"

Statute: destination sourcing taxes a sale where the buyer receives it; Ohio R.C. 5739.033 sets its own
intrastate rules (whether Keystone's in-state deliveries source to the customer's county is the open
statutory question — US README caveat). Rates are hand-entered by platform design (README rule 3), so
this checks consistency with the configured jurisdictions, never "the correct rate".

Rules (non-exempt tax rows; destination = the customer's address, since invoices carry no ship-to):
  tax_amount_wrong          row amount ≠ net × rate / 100 (± $0.05)
  rate_drift                row rate ≠ the jurisdiction's configured rate on the invoice date
  state_sourcing_mismatch   the row's state ≠ the customer's state
  local_sourcing_mismatch   a destination-sourced county/city row for a customer outside that county
  local_rate_unconfigured   (context) a customer in a county with no configured local jurisdiction
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import CONTEXT, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day

# City → county for the places Keystone's customers are in (playbook table; extend as customers appear).
CITY_COUNTY = {
    ("OH", "canton"): "Stark", ("OH", "massillon"): "Stark", ("OH", "north canton"): "Stark",
    ("OH", "alliance"): "Stark", ("OH", "louisville"): "Stark", ("OH", "hartville"): "Stark",
    ("OH", "columbus"): "Franklin", ("OH", "youngstown"): "Mahoning", ("OH", "toledo"): "Lucas",
    ("OH", "cleveland"): "Cuyahoga", ("OH", "akron"): "Summit", ("OH", "cincinnati"): "Hamilton",
    ("OH", "dayton"): "Montgomery",
}


def destination(inv, parties):
    party = parties.get(inv.get("party_id")) or {}
    for a in party.get("addresses") or []:
        if a.get("state"):
            state = str(a["state"]).upper()[:2]
            county = a.get("county") or CITY_COUNTY.get((state, str(a.get("city") or "").strip().lower()))
            return state, a.get("city"), (county or "").replace(" County", "") or None
    return None, None, None


class Sourcing(Rule):
    id = "sales_tax_rate"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        parties = data.index("parties", "id")
        juris = data.index("jurisdictions", "id")
        unconfigured: dict = {}
        for inv in data.get("invoices", []):
            if (inv.get("status") or "").lower() in ("draft", "void", "cancelled"):
                continue
            net = money(inv.get("net_total"))
            state, city, county = destination(inv, parties)
            base = dict(entity_type="Invoice", entity_id=inv["id"], entity_ref=inv.get("number"), currency=ctx.currency,
                        counterparty_id=inv.get("party_id"), counterparty_name=inv.get("_party_id_display"))
            rows = [r for r in inv.get("taxes") or [] if not r.get("is_exempt")]
            local_states = set()
            for r in rows:
                rate, amount = money(r.get("rate")), money(r.get("amount"))
                expected = (net * rate / 100).quantize(CENTS)
                j = juris.get(r.get("jurisdiction_id")) or {}
                if abs(expected - amount) > Decimal("0.05"):
                    yield Finding(finding_type="sales_tax_rate", rule="tax_amount_wrong", severity=65,
                                  total_exposure=abs(expected - amount), **base,
                                  summary=f"{inv.get('number')}: {r.get('jurisdiction_name')} charged {fmt(amount, ctx.currency)}; "
                                          f"{rate}% of {fmt(net, ctx.currency)} is {fmt(expected, ctx.currency)}.",
                                  details={"jurisdiction": r.get("jurisdiction_name")})
                configured = money(j.get("rate_percentage")) if j else None
                if configured is not None and j and configured != rate:
                    yield Finding(finding_type="sales_tax_rate", rule="rate_drift", severity=55, **base,
                                  summary=f"{inv.get('number')}: {r.get('jurisdiction_name')} at {rate}%, but the "
                                          f"jurisdiction is configured at {configured}%.",
                                  details={"row_rate": str(rate), "configured": str(configured)})
                row_state = str(r.get("state_code") or "").upper()
                if state and row_state and row_state != state:
                    yield Finding(finding_type="sales_tax_rate", rule="state_sourcing_mismatch", severity=75,
                                  total_exposure=amount, **base,
                                  summary=f"{inv.get('number')} charged {row_state} tax to a customer in {state}.",
                                  details={"row_state": row_state, "customer_state": state})
                level = (r.get("jurisdiction_level") or j.get("jurisdiction_level") or "").lower()
                if level in ("county", "city") and (j.get("sourcing") or "destination") == "destination":
                    local_states.add(row_state)
                    jcounty = str(j.get("county") or r.get("jurisdiction_name") or "").replace(" County", "").split(" (")[0]
                    if county and jcounty and county.lower() != jcounty.lower():
                        yield Finding(
                            finding_type="sales_tax_rate", rule="local_sourcing_mismatch", severity=self.severity,
                            total_exposure=amount, **base,
                            summary=f"{inv.get('number')} ({inv.get('_party_id_display')}, {city} — {county} County): "
                                    f"charged {r.get('jurisdiction_name')} {rate}% ({fmt(amount, ctx.currency)}) although "
                                    f"the jurisdiction is destination-sourced. Either the sourcing setting is wrong, or "
                                    f"the customer was charged the wrong county's rate.",
                            details={"customer_city": city, "customer_state": state, "customer_county": county,
                                     "jurisdiction": r.get("jurisdiction_name"), "configured_sourcing": j.get("sourcing")})
            if rows and county and state not in local_states and not any(
                    str(j.get("county") or "").replace(" County", "").lower() == county.lower()
                    for j in data.get("jurisdictions", [])):
                unconfigured.setdefault((state, county), []).append(inv.get("number"))
        for (state, county), invs in sorted(unconfigured.items()):
            yield Finding(finding_type="sales_tax_rate", rule="local_rate_unconfigured", severity=15, status=CONTEXT,
                          entity_type="County", entity_id=f"{state}:{county}", entity_ref=f"{county} County, {state}",
                          currency=ctx.currency,
                          summary=f"{len(invs)} taxed invoice(s) to {county} County, {state}, where no local jurisdiction "
                                  f"is configured (rates are manual by platform design — not a bug).",
                          details={"invoices": invs[:20]})


class SourcingAndRate(Playbook):

    @property
    def rules(self):
        return [Sourcing()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice"), parties=fetcher.list("Party"),
                       jurisdictions=fetcher.list("TaxJurisdiction"))

    def summary(self, outcome, ctx):
        local = [f for f in outcome.findings if f.rule == "local_sourcing_mismatch"]
        tax = sum((f.total_exposure for f in local), Decimal("0"))
        other = sum(1 for f in outcome.findings if f.rule in ("tax_amount_wrong", "rate_drift", "state_sourcing_mismatch"))
        return (f"{other} arithmetic, rate or state-sourcing error(s). "
                + (f"{len(local)} invoice(s) to customers outside the county were charged that county's destination-"
                   f"sourced tax ({fmt(tax, ctx.currency)}): either the sourcing setting is wrong, or these customers were "
                   f"charged the wrong county's rate." if local else "Local sourcing is consistent."))
