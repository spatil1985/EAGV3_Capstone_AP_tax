"""UC-30 — Multiple GST registrations: consistency, branch transfers, ISD.

Spec: docs/usecases/IN/uc-30-multiple-registrations.md.
Question: "We're registered in several states. Are our branches dealing with each other the way GST
requires?"

Statute: s.25(4)–(6) CGST Act — each state registration is a distinct person, but all share the PAN;
supplies between them are taxable (Schedule I para 2, valued under Rule 28); common input services
are distributed through an ISD (s.2(61), s.20).

Rules that run today (registration data):
  registration_pan_mismatch    a location GSTIN's PAN (chars 3–12) ≠ OrgProfile.pan
  registration_state_mismatch  GSTIN's first two digits ≠ the location's state code
  primary_gstin_mismatch       the primary location's GSTIN ≠ OrgProfile.gstin
  location_state_code_invalid  state code is not a 2-digit GST state code
Branch transfers, supplies from the wrong registration and ISD need the despatching / receiving
GSTIN on documents, which the platform doesn't record: reported in the context, not guessed.
"""

import re

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.uc.common.records import NOT_POSTED

GST_STATE = re.compile(r"^(0[1-9]|[1-3][0-9]|9[79])$")


def _row(rule, loc, ctx, severity, summary, **details):
    return Finding(finding_type="registration", rule=rule, severity=severity, entity_type="Location",
                   entity_id=loc.get("id") or loc.get("name"), entity_ref=loc.get("name"), currency=ctx.currency,
                   summary=summary, details={"gstin": loc.get("gstin"), "state_code": loc.get("state_code"), **details})


class Registrations(Rule):
    id = "registration"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        org = (data.get("org") or [{}])[0]
        pan, org_gstin = str(org.get("pan") or "").upper(), str(org.get("gstin") or "").upper()
        for loc in data.get("locations", []):
            gstin = str(loc.get("gstin") or "").upper()
            code = str(loc.get("state_code") or "").strip()
            name = loc.get("name")
            if code and not GST_STATE.match(code):
                yield _row("location_state_code_invalid", loc, ctx, 40,
                           f"{name}: state code '{code}' is not a GST state code.")
            if not gstin:
                continue
            if pan and gstin[2:12] != pan:
                yield _row("registration_pan_mismatch", loc, ctx, 70,
                           f"{name}: GSTIN {gstin} belongs to PAN {gstin[2:12]}, not the company's PAN {pan}. Every "
                           f"registration must share the PAN (s.25(6)); either the location or the company profile "
                           f"is wrong.", pan_in_gstin=gstin[2:12], company_pan=pan)
            if GST_STATE.match(code) and gstin[:2] != code:
                yield _row("registration_state_mismatch", loc, ctx, 55,
                           f"{name}: GSTIN {gstin} is for state {gstin[:2]}, but the location is in state {code}.")
            if loc.get("is_primary") and org_gstin and gstin != org_gstin:
                yield _row("primary_gstin_mismatch", loc, ctx, 65,
                           f"{name} is the primary location, but its GSTIN {gstin} differs from the company "
                           f"profile's {org_gstin}.", company_gstin=org_gstin)


class MultipleRegistrations(Playbook):

    @property
    def rules(self):
        return [Registrations()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(locations=fetcher.list("Location"), org=fetcher.list("OrgProfile"),
                       invoices=fetcher.list("Invoice", direction="receivable"))

    def context(self, data, findings, ctx):
        branch_states = {str(l.get("gstin") or "")[:2] for l in data["locations"] if l.get("gstin")}
        org_state = str(((data.get("org") or [{}])[0]).get("gstin") or "")[:2]
        pos: dict = {}
        for inv in data["invoices"]:
            if (inv.get("status") or "").lower() not in NOT_POSTED:
                p = str(inv.get("place_of_supply") or "")[:2]
                pos[p] = pos.get(p, 0) + 1
        overlap = {p: n for p, n in pos.items() if p in branch_states and p != org_state}
        return {"locations": len(data["locations"]),
                "sales to states where a branch GSTIN exists": overlap,
                "branch transfers / wrong-registration supplies / ISD":
                    "can't run: documents don't record the despatching or receiving GSTIN (not yet requested)"}

    def summary(self, outcome, ctx):
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        overlap = outcome.context["sales to states where a branch GSTIN exists"]
        return (f"{n('registration_pan_mismatch')} location GSTIN(s) don't belong to the company's PAN; "
                f"primary GSTIN mismatch: {n('primary_gstin_mismatch')}; {n('location_state_code_invalid')} invalid state "
                f"code(s); {n('registration_state_mismatch')} GSTIN/state mismatch(es). "
                + (f"{sum(overlap.values())} sale(s) go to states with a branch GSTIN ({overlap}); whether they were "
                   f"despatched from that branch can't be told. " if overlap else "")
                + "Branch-transfer and ISD checks can't run until documents record their registration.")
