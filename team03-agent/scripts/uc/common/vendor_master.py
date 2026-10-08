"""Vendor-master audit shared by UC-40 (India) and US-16 (US).

The population is every Party actually used as a vendor (on a bill, payment or vendor credit), not
`contact_type = vendor`, which misses most of them on this platform. One finding per vendor, led by
its most serious problem; the rest are listed in `also`, and `affected_documents` (count and value of
the documents relying on the record) drives the exposure and the ranking.

Jurisdiction checks are passed in as functions `check(party, usage, data, ctx) -> list[(rule, text)]`.
"""

import re
from decimal import Decimal

from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.records import NOT_POSTED

LEGAL_SUFFIX = re.compile(r"\b(pvt|private|ltd|limited|llp|llc|inc|corp|co|company|the)\b\.?", re.I)


def usage(data) -> dict:
    out: dict = {}
    for entity, key, amount in (("bills", "vendor_id", "grand_total"), ("payments", "vendor_id", "amount"),
                                ("vendor_credits", "vendor_id", "grand_total")):
        for doc in data.get(entity, []):
            if (doc.get("status") or "").lower() in NOT_POSTED - {"draft"} or not doc.get(key):
                continue
            row = out.setdefault(doc[key], {"bills": 0, "payments": 0, "vendor_credits": 0, "value": Decimal("0"),
                                            "payment_accounts": set()})
            row[entity] += 1
            row["value"] += abs(money(doc.get(amount)))
            if entity == "payments" and doc.get("vendor_bank_account_number"):
                row["payment_accounts"].add(str(doc["vendor_bank_account_number"]))
    return out


def norm_name(name) -> str:
    return re.sub(r"[^a-z0-9]", "", LEGAL_SUFFIX.sub("", str(name or "").lower()))


def common_checks(party, use, data, ctx) -> list:
    hits = []
    if (party.get("contact_type") or "") not in ("vendor", "both") or (party.get("gst_treatment") or "") == "consumer":
        hits.append(("vendor_type_conflict", f"is used as a vendor but typed {party.get('contact_type') or 'blank'}"
                                             f"{' / consumer' if party.get('gst_treatment') == 'consumer' else ''}"))
    if not party.get("addresses"):
        hits.append(("vendor_address_missing", "has no address"))
    bank = party.get("vendor_bank_account_number") or party.get("bank_details")
    if not bank:
        hits.append(("vendor_bank_missing", "has no bank details, so payments can't be checked against it"))
    elif use["payment_accounts"] and str(party.get("vendor_bank_account_number")) not in use["payment_accounts"]:
        hits.append(("payment_account_mismatch", "was paid to an account not on its master record"))
    return hits


def duplicates(parties) -> dict:
    keys: dict = {}
    for p in parties:
        for label, value in (("GSTIN", p.get("gst_no")), ("PAN", p.get("pan")), ("TIN", p.get("tin") or p.get("tax_id")),
                             ("bank", p.get("vendor_bank_account_number")), ("email", p.get("email")),
                             ("phone", p.get("phone")), ("name", norm_name(p.get("name")))):
            if value:
                keys.setdefault((label, str(value).strip().lower()), []).append(p["id"])
    out: dict = {}
    for (label, _), ids in keys.items():
        if len(ids) > 1:
            for pid in ids:
                out.setdefault(pid, set()).add(label)
    return out


def vendor_findings(data, ctx, checks, order, severity):
    used = usage(data)
    parties = {p["id"]: p for p in data.get("parties", [])}
    dups = duplicates([parties[i] for i in used if i in parties])
    for pid, use in used.items():
        party = parties.get(pid)
        if not party:
            continue
        hits = common_checks(party, use, data, ctx)
        for check in checks:
            hits += check(party, use, data, ctx)
        if pid in dups:
            hits.append(("duplicate_vendor", f"shares {', '.join(sorted(dups[pid]))} with another vendor"))
        if not hits:
            continue
        hits.sort(key=lambda h: order.index(h[0]))
        lead, text = hits[0]
        docs = f"{use['bills']} bill(s), {use['payments']} payment(s), {use['vendor_credits']} credit(s)"
        yield Finding(
            finding_type="vendor_master", rule=lead, severity=severity.get(lead, 40), entity_type="Party",
            entity_id=pid, entity_ref=party.get("name"), total_exposure=use["value"], currency=ctx.currency,
            counterparty_id=pid, counterparty_name=party.get("name"),
            summary=f"{party.get('name')} {text}" + (f"; also {len(hits) - 1} other gap(s)" if len(hits) > 1 else "")
                    + f". {docs} ({fmt(use['value'], ctx.currency)}) rely on this record.",
            details={"also": [h[0] for h in hits[1:]], "problems": [t for _, t in hits],
                     "affected_documents": {"bills": use["bills"], "payments": use["payments"],
                                            "vendor_credits": use["vendor_credits"], "value": str(use["value"])}})


def population_summary(data) -> dict:
    used = usage(data)
    parties = {p["id"]: p for p in data.get("parties", [])}
    rows = [parties[i] for i in used if i in parties]
    count = lambda pred: sum(1 for p in rows if pred(p))  # noqa: E731
    return {"vendors used on documents": len(rows),
            "… typed vendor": count(lambda p: p.get("contact_type") == "vendor"),
            "… with bank details": count(lambda p: p.get("vendor_bank_account_number") or p.get("bank_details")),
            "… with an address": count(lambda p: p.get("addresses"))}
