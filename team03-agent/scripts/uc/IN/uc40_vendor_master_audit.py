"""UC-40 — Vendor master audit (India).

Spec: docs/usecases/IN/uc-40-vendor-master-audit.md.
Question: "Are our vendor records complete and trustworthy enough to pay against, claim credit on and
deduct tax for?"

Statute: s.16(2)(a) + Rule 46 (credit needs the supplier's GSTIN on the invoice); s.25(6) (the GSTIN
embeds the PAN); s.206AA (no PAN → 20% TDS); MSMED s.15 / s.43B(h) (Udyam registration).

One finding per vendor (scripts/uc/common/vendor_master.py), led by the most serious problem:
  vendor_gstin_missing, vendor_gstin_invalid, vendor_gstin_pan_mismatch, vendor_gstin_state_mismatch,
  vendor_pan_missing, vendor_msme_no_missing, plus the shared vendor_type_conflict,
  vendor_address_missing, vendor_bank_missing, payment_account_mismatch, duplicate_vendor.
US 1099 fields on India parties are never read.
"""

import re

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.uc.common.vendor_master import population_summary, vendor_findings

GSTIN = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ORDER = ["vendor_gstin_invalid", "vendor_gstin_pan_mismatch", "payment_account_mismatch", "vendor_gstin_missing",
         "vendor_pan_missing", "vendor_bank_missing", "duplicate_vendor", "vendor_gstin_state_mismatch",
         "vendor_msme_no_missing", "vendor_type_conflict", "vendor_address_missing"]
SEVERITY = dict(zip(ORDER, (80, 75, 85, 70, 60, 60, 55, 45, 40, 35, 25)))
STATE_CODES = {"maharashtra": "27", "gujarat": "24", "karnataka": "29", "madhya pradesh": "23", "tamil nadu": "33",
               "delhi": "07", "uttar pradesh": "09", "telangana": "36", "kerala": "32", "punjab": "03",
               "rajasthan": "08", "west bengal": "19", "haryana": "06", "goa": "30", "andhra pradesh": "37"}


def gstin_checksum_ok(g: str) -> bool:
    total = 0
    for i, ch in enumerate(g[:14]):
        value = CHARS.index(ch) * (2 if i % 2 else 1)
        total += value // 36 + value % 36
    return CHARS[(36 - total % 36) % 36] == g[14]


def india_checks(party, use, data, ctx):
    hits = []
    gst, pan = str(party.get("gst_no") or "").upper(), str(party.get("pan") or "").upper()
    treatment = (party.get("gst_treatment") or "").lower()
    if gst:
        if not GSTIN.match(gst) or not gstin_checksum_ok(gst):
            hits.append(("vendor_gstin_invalid", f"has GSTIN {gst}, which fails the format or checksum"))
        else:
            if pan and gst[2:12] != pan:
                hits.append(("vendor_gstin_pan_mismatch", f"has GSTIN {gst} for PAN {gst[2:12]}, not its PAN {pan}"))
            states = {STATE_CODES.get(str(a.get("state") or "").strip().lower()) for a in party.get("addresses") or []}
            states.discard(None)
            if states and gst[:2] not in states:
                hits.append(("vendor_gstin_state_mismatch", f"has a GSTIN for state {gst[:2]} but an address in {sorted(states)}"))
    elif treatment in ("business_gst", "sez"):
        hits.append(("vendor_gstin_missing", f"is a registered ({treatment}) supplier with no GSTIN, so input credit "
                                             f"on its bills can't be supported"))
    if not pan and use["bills"]:
        hits.append(("vendor_pan_missing", "has no PAN, so TDS on it falls to the 20% no-PAN rate (s.206AA)"))
    if party.get("is_msme") and not party.get("msme_no"):
        hits.append(("vendor_msme_no_missing", "is marked MSME with no Udyam number"))
    return hits


class VendorMaster(Rule):
    id = "vendor_master"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        yield from vendor_findings(data, ctx, [india_checks], ORDER, SEVERITY)


class VendorMasterAudit(Playbook):

    @property
    def rules(self):
        return [VendorMaster()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(parties=fetcher.list("Party"), bills=fetcher.list("Bill"), payments=fetcher.list("PaymentMade"),
                       vendor_credits=fetcher.list("VendorCredit"))

    def context(self, data, findings, ctx):
        summary = population_summary(data)
        vendors = {d["vendor_id"] for k in ("bills", "payments", "vendor_credits") for d in data[k] if d.get("vendor_id")}
        rows = [p for p in data["parties"] if p["id"] in vendors]
        summary.update({"… with GSTIN": sum(1 for p in rows if p.get("gst_no")),
                        "… with PAN": sum(1 for p in rows if p.get("pan"))})
        return summary

    def summary(self, outcome, ctx):
        c = outcome.context
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule or rule in f.details["also"])  # noqa: E731
        return (f"Of {c['vendors used on documents']} vendors in use, {c['… with GSTIN']} have a GSTIN, {c['… with PAN']} a "
                f"PAN and {c['… with bank details']} bank details. {n('vendor_gstin_missing')} registered vendor(s) lack a "
                f"GSTIN; {n('vendor_pan_missing')} lack a PAN (20% TDS); {n('vendor_type_conflict')} are typed as customers "
                f"or not at all; {n('duplicate_vendor')} look duplicated.")
