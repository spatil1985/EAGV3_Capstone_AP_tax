"""US-16 — Vendor master audit (US instance of UC-40).

Spec: docs/usecases/US/us-16-vendor-master-audit.md.
Question: "Are our vendor records (TIN, W-9, 1099 settings) complete enough to pay and report on?"

Statute: IRC §6109 / Form W-9 (TIN for information returns); IRC §3406 (24% backup withholding without
a TIN); 1099 scope excludes corporations except attorneys and medical payments.

One finding per vendor (scripts/uc/common/vendor_master.py), with the US checks:
  vendor_tin_missing, vendor_tin_format_invalid, tin_type_classification_conflict, w9_missing,
  form_1099_flag_conflict, form_1099_box_conflict, plus the shared vendor_type_conflict,
  vendor_address_missing, vendor_bank_missing, payment_account_mismatch, duplicate_vendor.
`tin` is redacted for our role (`_redacted_fields`): a redacted TIN is not reported missing. India-only
fields (gst_no, pan, msme_*) are never read.
"""

import re

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.uc.common.vendor_master import population_summary, vendor_findings

CORPORATE = {"c_corporation", "s_corporation", "llc_c_corp", "llc_s_corp"}
NON_CORPORATE = {"individual_sole_proprietor", "llc_partnership", "partnership", "llc_single_member"}
ORDER = ["vendor_tin_format_invalid", "tin_type_classification_conflict", "payment_account_mismatch", "vendor_tin_missing",
         "w9_missing", "form_1099_flag_conflict", "form_1099_box_conflict", "vendor_bank_missing", "duplicate_vendor",
         "vendor_type_conflict", "vendor_address_missing"]
SEVERITY = dict(zip(ORDER, (75, 70, 85, 70, 65, 55, 45, 60, 55, 30, 40)))
SERVICE_WORDS = re.compile(r"consult|machining|welding|sign|graphic|service|repair|install|design", re.I)


def us_checks(party, use, data, ctx):
    hits = []
    cls = (party.get("us_tax_classification") or "").lower()
    redacted = "tin" in (party.get("_redacted_fields") or [])
    tin, tin_type = re.sub(r"\D", "", str(party.get("tin") or "")), (party.get("tin_type") or "").lower()
    if not tin and not redacted and use["payments"]:
        hits.append(("vendor_tin_missing", "has no TIN on file (backup withholding risk — US-06)"))
    elif tin and len(tin) != 9:
        hits.append(("vendor_tin_format_invalid", f"has a {tin_type or 'TIN'} that is not 9 digits"))
    if cls in CORPORATE and tin_type == "ssn":
        hits.append(("tin_type_classification_conflict", f"is a {cls} with an SSN as its TIN"))
    if party.get("is_1099_vendor") and not party.get("w9_on_file"):
        hits.append(("w9_missing", "is a 1099 vendor with no W-9 on file"))
    if party.get("is_1099_vendor") and cls in CORPORATE:
        hits.append(("form_1099_flag_conflict", f"is flagged for 1099 but is a {cls} (only attorneys/medical are)"))
    elif not party.get("is_1099_vendor") and cls in NON_CORPORATE and use["payments"]:
        hits.append(("form_1099_flag_conflict", f"is a {cls} receiving payments but not flagged for 1099"))
    box = (party.get("form_1099_box") or "").upper()
    supplies = " ".join(str(l.get("description") or "") for b in data.get("bills", []) if b.get("vendor_id") == party["id"]
                        for l in b.get("items") or []) + " " + str(party.get("name") or "")
    if box.startswith("MISC-1") and SERVICE_WORDS.search(supplies):
        hits.append(("form_1099_box_conflict", "is set to box MISC-1 (Rents) but supplies services; NEC-1 is likely"))
    return hits


class VendorMasterUS(Rule):
    id = "vendor_master"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        yield from vendor_findings(data, ctx, [us_checks], ORDER, SEVERITY)


class VendorMasterAuditUS(Playbook):

    @property
    def rules(self):
        return [VendorMasterUS()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(parties=fetcher.list("Party"), bills=fetcher.list("Bill"), payments=fetcher.list("PaymentMade"),
                       vendor_credits=[])

    def context(self, data, findings, ctx):
        summary = population_summary(data)
        vendors = {d["vendor_id"] for k in ("bills", "payments") for d in data[k] if d.get("vendor_id")}
        rows = [p for p in data["parties"] if p["id"] in vendors]
        summary.update({"… with W-9": sum(1 for p in rows if p.get("w9_on_file")),
                        "… TIN redacted for our role": sum(1 for p in rows if "tin" in (p.get("_redacted_fields") or []))})
        return summary

    def summary(self, outcome, ctx):
        c = outcome.context
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule or rule in f.details["also"])  # noqa: E731
        return (f"Of {c['vendors used on documents']} vendors in use, {c['… with W-9']} have a W-9 and "
                f"{c['… with bank details']} bank details. {n('w9_missing')} lack a W-9; {n('form_1099_box_conflict')} have a "
                f"doubtful 1099 box; {n('form_1099_flag_conflict')} have a 1099 flag that contradicts their classification; "
                f"{n('vendor_bank_missing')} have no bank details, so payment destinations can't be checked.")
