"""UC-37 — Payments to non-resident vendors: s.195 TDS, treaty documents, Form 15CA/CB.

Spec: docs/usecases/IN/uc-37-non-resident-payments-tds-195.md.
Question: "Before we pay a foreign vendor, have we deducted the right tax and got the remittance
paperwork done?"

Statute (Income-tax Act 1961 numbering; renumbered from 1 April 2026 — confirm): s.195 TDS on sums
chargeable in India paid to a non-resident (s.115A rate, or the treaty rate with TRC + Form 10F);
s.206AA 20% floor without PAN; Rule 37BB Form 15CA/15CB; s.40(a)(i) disallowance if not deducted.

Non-residence needs real evidence: a non-India address or non-INR billing. `gst_treatment = overseas`
alone is not enough — it is set on Indian INR vendors (UC-21).

Rules:
  tds_195_not_deducted         non-resident, service lines (SAC 99…), no TDS → exposure at the s.115A rate
  dtaa_rate_without_documents  a reduced rate applied without TRC / Form 10F on file
  tds_206aa_rate_short         no PAN and a rate below 20%
  form_15ca_cb_missing         FY remittance to the vendor with no 15CA (and no 15CB above ₹5 lakh) on file
  overseas_tag_on_resident     (data_quality) tagged overseas but an Indian address and INR — UC-40
Documents not in the data model come from config/overrides/nonresident_docs.yaml.
"""

from decimal import Decimal

import yaml

from aptax.config import CONFIG_DIR
from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day, fy_start
from scripts.uc.common.lines import line_value
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tds import stored

OVERRIDES = CONFIG_DIR / "overrides" / "nonresident_docs.yaml"


def docs_on_file() -> dict:
    try:
        raw = yaml.safe_load(OVERRIDES.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    return {v.get("vendor_id"): v for v in raw.get("vendors") or [] if v.get("vendor_id")}


def countries(party) -> set:
    return {str(a.get("country") or "").strip().lower() for a in (party or {}).get("addresses") or []
            if a.get("country")}


def residence(doc, party) -> tuple[bool, list]:
    evidence = []
    abroad = {c for c in countries(party) if c not in ("india", "in", "ind")}
    if abroad:
        evidence.append(f"address in {', '.join(sorted(abroad))}")
    if (doc.get("currency_code") or "INR").upper() != "INR":
        evidence.append(f"billed in {doc.get('currency_code')}")
    return bool(evidence), evidence


class NonResident(Rule):
    id = "nonresident_withholding"
    severity = 75

    def evaluate(self, data: Dataset, ctx):
        parties, docs = data.index("parties", "id"), data.get("docs", {})
        rate = Decimal(str(ctx.constant("tds_195_rate_fts_royalty_pct")))
        floor = Decimal(str(ctx.constant("tds_rate_206aa_pct")))
        start = fy_start(ctx.as_of, ctx.tax_regime)
        remitted: dict = {}
        for bill in data.get("bills", []):
            if (bill.get("status") or "").lower() in NOT_POSTED:
                continue
            party = parties.get(bill.get("vendor_id"))
            foreign, evidence = residence(bill, party)
            number = ref(bill, "number")
            vid, vname = party_of(bill, data)
            base = dict(entity_type="Bill", entity_id=bill["id"], entity_ref=number, currency=ctx.currency,
                        counterparty_id=vid, counterparty_name=vname)
            tagged = (bill.get("gst_treatment") or (party or {}).get("gst_treatment") or "").lower() == "overseas"
            if tagged and not foreign:
                yield Finding(finding_type=DATA_QUALITY, rule="overseas_tag_on_resident", status=DATA_QUALITY,
                              severity=15, **base,
                              summary=f"{number} ({vname}) is tagged overseas, but the vendor has no foreign address "
                                      f"and bills in INR; not treated as a non-resident payment (fix the tag — UC-40).",
                              details={"countries": sorted(countries(party))})
                continue
            if not foreign:
                continue
            services = [l for l in bill.get("items") or [] if str(l.get("hsn_or_sac") or "").startswith("99")]
            if not services:
                continue          # goods purchases are generally outside s.195
            value = sum((line_value(l) for l in services), Decimal("0"))
            amount, pct, _ = stored(bill)
            on_file = docs.get(bill.get("vendor_id"), {})
            if day(bill.get("date")) and day(bill["date"]) >= start:
                remitted[bill.get("vendor_id")] = remitted.get(bill.get("vendor_id"), Decimal("0")) + money(bill.get("grand_total"))
            if amount <= 0:
                due = (value * rate / 100).quantize(CENTS)
                yield Finding(finding_type="nonresident_withholding", rule="tds_195_not_deducted", severity=85,
                              total_exposure=due, **base,
                              summary=f"{number} ({vname}, {', '.join(evidence)}) pays a non-resident "
                                      f"{fmt(value, ctx.currency)} for services with no TDS: about "
                                      f"{fmt(due, ctx.currency)} due at {rate}% (lower with treaty documents). Without "
                                      f"it the expense is disallowed (s.40(a)(i)).",
                              details={"evidence": evidence, "service_value": str(value), "rate_pct": str(rate)})
            elif pct and pct < rate and not (on_file.get("trc_valid_to") and on_file.get("form_10f")):
                yield Finding(finding_type="nonresident_withholding", rule="dtaa_rate_without_documents", severity=70,
                              total_exposure=(value * (rate - pct) / 100).quantize(CENTS), **base,
                              summary=f"{number} ({vname}) applies {pct}% (a treaty rate) without a tax residency "
                                      f"certificate and Form 10F on file.", details={"rate_applied": str(pct)})
            if amount > 0 and pct and pct < floor and not (party or {}).get("pan"):
                yield Finding(finding_type="nonresident_withholding", rule="tds_206aa_rate_short", severity=65, **base,
                              summary=f"{number} ({vname}) deducts {pct}% from a vendor with no PAN; s.206AA requires "
                                      f"at least {floor}% unless Rule 37BC documents are on file.",
                              details={"rate_applied": str(pct)})
        threshold = money(ctx.constant("form_15cb_threshold_inr"))
        for vendor, total in remitted.items():
            on_file = docs.get(vendor, {})
            need_cb = total > threshold
            if not on_file.get("form_15ca") or (need_cb and not on_file.get("form_15cb")):
                name = (parties.get(vendor) or {}).get("name")
                yield Finding(finding_type="nonresident_withholding", rule="form_15ca_cb_missing", severity=55,
                              entity_type="Party", entity_id=vendor, entity_ref=name, total_exposure=total,
                              currency=ctx.currency, counterparty_id=vendor, counterparty_name=name,
                              summary=f"{fmt(total, ctx.currency)} is payable to non-resident {name} this FY with no Form "
                                      f"15CA" + (" / 15CB (needed above ₹5 lakh)" if need_cb else "") + " reference on file.",
                              details={"fy_total": str(total), "needs_15cb": need_cb})


class NonResidentPayments(Playbook):

    @property
    def rules(self):
        return [NonResident()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"), docs=docs_on_file())

    def context(self, data, findings, ctx):
        parties = data.index("parties", "id")
        foreign = [b for b in data["bills"] if residence(b, parties.get(b.get("vendor_id")))[0]]
        return {"bills tagged overseas": sum(1 for b in data["bills"] if (b.get("gst_treatment") or "") == "overseas"),
                "bills with real non-resident evidence": len(foreign),
                "treaty / 15CA-CB documents on file": len(data["docs"])}

    def summary(self, outcome, ctx):
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"{n('tds_195_not_deducted')} payment(s) to genuine non-residents lack s.195 TDS; "
                f"{n('dtaa_rate_without_documents')} use a treaty rate without documents; {n('form_15ca_cb_missing')} "
                f"vendor(s) lack Form 15CA/CB. {n('overseas_tag_on_resident')} bill(s) tagged overseas are from Indian, "
                f"INR vendors and were not treated as non-resident.")
