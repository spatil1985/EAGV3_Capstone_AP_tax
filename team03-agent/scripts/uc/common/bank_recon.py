"""Bank-to-payables reconciliation shared by UC-43 (India) and US-19 (US).

Match each bank debit to a PaymentMade: by matched_voucher_id; else by bank/reference number; else by
normalised payee = vendor name, equal amount (±1) and date within ±5 days.
  bank_debit_unrecorded  a debit to a vendor with no payment in AP (the vendor's open bills of the same
                         amount are at risk of being paid twice)
  payment_not_in_bank    aggregate: AP payments inside the bank window with no matching debit
  match_without_voucher  (data_quality) aggregate: debits 'matched' to no voucher
  unidentified_debit     no payee, uncategorised, older than 7 days
"""

import re
from decimal import Decimal

from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.records import NOT_POSTED

TOLERANCE = Decimal("1.00")
DAYS = 5


def norm(name) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\b(pvt|ltd|limited|llc|inc|co)\b", "", str(name or "").lower()))


def match_debit(txn, payments, vendor_names, used: set):
    vid = txn.get("matched_voucher_id")
    if txn.get("matched_voucher_type") == "PaymentMade" and vid:
        return next((p for p in payments if p["id"] == vid), None), "voucher"
    ref = str(txn.get("reference") or "").strip()
    if ref:
        hit = next((p for p in payments if p["id"] not in used and ref in
                    (str(p.get("bank_reference_number") or ""), str(p.get("reference_number") or ""))), None)
        if hit:
            return hit, "reference"
    when, amount, payee = day(txn.get("date")), money(txn.get("amount")), norm(txn.get("payee"))
    for p in payments:
        if p["id"] in used or not payee or norm(vendor_names.get(p.get("vendor_id")) or p.get("_vendor_id_display")) != payee:
            continue
        if abs(money(p.get("amount")) - amount) <= TOLERANCE and day(p.get("date")) and when and \
                abs((day(p["date"]) - when).days) <= DAYS:
            return p, "payee+amount+date"
    return None, None


def recon(data, ctx):
    payments = [p for p in data.get("payments", []) if (p.get("status") or "").lower() not in NOT_POSTED]
    parties = data.index("parties", "id")
    names = {pid: p.get("name") for pid, p in parties.items()}
    vendor_by_name = {norm(p.get("name")): pid for pid, p in parties.items()}
    debits = [t for t in data.get("bank_transactions", []) if (t.get("type") or "") == "debit"]
    used, rows = set(), []
    for txn in debits:
        hit, how = match_debit(txn, payments, names, used)
        if hit:
            used.add(hit["id"])
        rows.append((txn, hit, how))
    dates = [day(t.get("date")) for t in data.get("bank_transactions", []) if day(t.get("date"))]
    window = (min(dates), max(dates)) if dates else (None, None)
    missing = [p for p in payments if p["id"] not in used and window[0] and day(p.get("date"))
               and window[0] <= day(p["date"]) <= window[1]]
    return {"debits": debits, "rows": rows, "missing": missing, "window": window, "vendor_by_name": vendor_by_name}


def recon_findings(data, ctx):
    r = recon(data, ctx)
    open_bills = [b for b in data.get("bills", []) if (b.get("status") or "").lower() in ("open", "overdue")
                  and money(b.get("balance_due")) > 0]
    no_voucher = []
    for txn, hit, how in r["rows"]:
        if (txn.get("categorization_status") or "") == "matched" and not txn.get("matched_voucher_id"):
            no_voucher.append(txn)
        if hit:
            continue
        amount = money(txn.get("amount"))
        vendor = r["vendor_by_name"].get(norm(txn.get("payee")))
        if vendor:
            same = [b.get("number") for b in open_bills if b.get("vendor_id") == vendor
                    and abs(money(b.get("balance_due")) - amount) <= TOLERANCE]
            yield Finding(
                finding_type="bank_reconciliation", rule="bank_debit_unrecorded", severity=75 if same else 65,
                entity_type="BankTransaction", entity_id=txn["id"], entity_ref=txn.get("reference") or txn["id"],
                total_exposure=amount, currency=ctx.currency, counterparty_id=vendor, counterparty_name=txn.get("payee"),
                summary=f"{fmt(amount, ctx.currency)} left the bank to {txn.get('payee')} on {txn.get('date')} with no "
                        f"payment recorded in AP" + (f"; open bill(s) {', '.join(same)} of the same amount could be paid "
                                                     f"again" if same else "") + ".",
                details={"bank_transaction_id": txn["id"], "categorization_status": txn.get("categorization_status"),
                         "match_attempts": ["voucher", "reference", "payee+amount+date"],
                         "open_bills_same_amount": same})
        elif not txn.get("payee") and (txn.get("categorization_status") or "") == "uncategorized" and \
                day(txn.get("date")) and (ctx.as_of - day(txn["date"])).days > 7:
            yield Finding(
                finding_type="bank_reconciliation", rule="unidentified_debit", severity=50, entity_type="BankTransaction",
                entity_id=txn["id"], entity_ref=txn.get("reference") or txn["id"], total_exposure=amount,
                currency=ctx.currency,
                summary=f"{fmt(amount, ctx.currency)} debited on {txn.get('date')} ({txn.get('description')}) has no "
                        f"payee and is uncategorised: ask treasury.", details={"description": txn.get("description")})
    if r["missing"]:
        total = sum((money(p.get("amount")) for p in r["missing"]), Decimal("0"))
        yield Finding(
            finding_type="bank_reconciliation", rule="payment_not_in_bank", severity=60, entity_type="PaymentMade",
            entity_id="unmatched-payments", entity_ref=f"{len(r['missing'])} payments", total_exposure=total,
            currency=ctx.currency,
            summary=f"{len(r['missing'])} AP payment(s) dated inside the bank window ({r['window'][0]} … {r['window'][1]}), "
                    f"{fmt(total, ctx.currency)}, never appear as a bank debit.",
            details={"count": len(r["missing"]), "payments": [p.get("number") for p in r["missing"]][:50],
                     "paid_through_set": sum(1 for p in r["missing"] if p.get("paid_through"))})
    if no_voucher:
        yield Finding(
            finding_type=DATA_QUALITY, rule="match_without_voucher", status=DATA_QUALITY, severity=20,
            entity_type="BankTransaction", entity_id="matched-no-voucher", entity_ref=f"{len(no_voucher)} debits",
            currency=ctx.currency,
            summary=f"{len(no_voucher)} bank debit(s) say 'matched' but point to no voucher: the bank says matched, "
                    f"but to nothing.", details={"count": len(no_voucher), "transactions": [t["id"] for t in no_voucher][:50]})


def recon_context(data, ctx) -> dict:
    r = recon(data, ctx)
    return {"bank window": f"{r['window'][0]} … {r['window'][1]}", "bank debits": len(r["debits"]),
            "bank debits total": str(sum((money(t.get("amount")) for t in r["debits"]), Decimal("0"))),
            "matched to a payment": sum(1 for _, hit, _ in r["rows"] if hit),
            "payments in AP": len(data.get("payments", []))}
