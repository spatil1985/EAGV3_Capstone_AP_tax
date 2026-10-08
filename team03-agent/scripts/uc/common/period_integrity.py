"""Period integrity shared by UC-28 (India) and US-15 (US): documents entered into a filed, locked or
closed period, or back-dated well after the event.

A "closed window" is (scope, last covered date, closed-at time, closed-by ref):
  filed    a filed return — covers its period, closed at its filed date
  locked   a TransactionLock — module scope, covers dates ≤ lock_date, closed at the lock's created_at
  closed   a closed AccountingPeriod — covers from..to, closed at closed_at
A document is caught when its date falls inside a window and its created_at is after the window closed.
"""

from datetime import datetime

from scripts.findings import Finding
from scripts.money import money
from scripts.uc.common.dates import day, month_bounds

# entity → (module scope for locks, tax/amount field)
DOCS = {
    "Invoice": ("sales", "total_tax"), "CreditNote": ("sales", "total_tax"),
    "Bill": ("purchases", "total_tax"), "VendorCredit": ("purchases", "total_tax"),
    "PaymentMade": ("banking", "amount"), "Expense": ("purchases", "tax_amount"),
}


def ts(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None) if value else None
    except ValueError:
        return None


def windows(returns=(), locks=(), periods=(), return_scopes=("sales", "purchases")) -> list[dict]:
    out = []
    for r in returns:
        if (r.get("filing_status") or "").lower() != "filed" or not r.get("filed_date"):
            continue
        rp = str(r.get("return_period") or "")
        if len(rp) != 7:
            continue
        start, end = month_bounds(f"{rp[3:]}-{rp[:2]}")
        out.append({"kind": "filed", "scopes": set(return_scopes), "from": start, "to": end,
                    "closed_at": ts(r["filed_date"]), "ref": f"{r.get('return_type')} {rp}", "id": r.get("id")})
    for lk in locks:
        if not day(lk.get("lock_date")):
            continue
        module = (lk.get("module") or "all").lower()
        out.append({"kind": "locked", "scopes": {"sales", "purchases", "banking"} if module in ("all", "accountant")
                    else {module}, "from": None, "to": day(lk["lock_date"]), "closed_at": ts(lk.get("created_at")),
                    "ref": f"lock {module} ≤ {lk['lock_date']}", "id": lk.get("id")})
    for p in periods:
        if (p.get("status") or "").lower() != "closed" or not day(p.get("to_date")):
            continue
        out.append({"kind": "closed", "scopes": {"sales", "purchases", "banking"}, "from": day(p.get("from_date")),
                    "to": day(p["to_date"]), "closed_at": ts(p.get("closed_at")),
                    "ref": f"period {p.get('from_date')}–{p.get('to_date')}", "id": p.get("id")})
    return out


RULE = {"filed": "entered_after_filing", "locked": "entered_into_locked_period", "closed": "entered_into_closed_period"}


def integrity_findings(docs_by_entity: dict, wins: list[dict], ctx, *, backdate_days: int):
    for entity, docs in docs_by_entity.items():
        scope, amount_field = DOCS[entity]
        for doc in docs:
            if (doc.get("status") or "").lower() in ("draft", "void", "cancelled"):
                continue
            when, created = day(doc.get("date")), ts(doc.get("created_at"))
            if not when or not created:
                continue
            number = doc.get("number") or doc.get("id")
            amount = money(doc.get(amount_field))
            hit = False
            for w in wins:
                if scope not in w["scopes"] or not w["closed_at"]:
                    continue
                if (w["from"] is None or when >= w["from"]) and when <= w["to"] and created > w["closed_at"]:
                    hit = True
                    days_after = (created - w["closed_at"]).days
                    yield Finding(
                        finding_type="period_integrity", rule=RULE[w["kind"]], severity=80 if w["kind"] == "filed" else 65,
                        entity_type=entity, entity_id=doc["id"], entity_ref=number, total_exposure=amount,
                        currency=ctx.currency,
                        summary=f"{entity} {number} dated {when} was entered on {created.date()}, {days_after} day(s) "
                                f"after {w['ref']} closed that period"
                                + (" — it belongs in the next return/amendment, with interest on any tax understated."
                                   if w["kind"] == "filed" else "; the platform let it through."),
                        details={"period_closed_by": w["ref"], "closed_by_id": w["id"], "days_after_close": days_after,
                                 "document_date": str(when), "created_at": str(created)})
                    break
            lag = (created.date() - when).days
            if not hit and lag > backdate_days:
                yield Finding(
                    finding_type="period_integrity", rule="backdated_document", severity=45, entity_type=entity,
                    entity_id=doc["id"], entity_ref=number, total_exposure=amount, currency=ctx.currency,
                    summary=f"{entity} {number} is dated {when} but was entered {lag} days later, on {created.date()}.",
                    details={"document_date": str(when), "created_at": str(created), "lag_days": lag})


def control_gaps(wins: list[dict]) -> list[str]:
    """Filed periods whose lock/close came later than the filing: documents could slip in meanwhile."""
    gaps = []
    for w in wins:
        if w["kind"] != "filed":
            continue
        guards = [g for g in wins if g["kind"] != "filed" and g["to"] >= w["to"] and g["closed_at"]]
        first = min((g["closed_at"] for g in guards), default=None)
        if first is None:
            gaps.append(f"{w['ref']} filed {w['closed_at'].date()} but no lock or close covers it")
        elif first > w["closed_at"]:
            gaps.append(f"{w['ref']} filed {w['closed_at'].date()}, locked/closed only on {first.date()} "
                        f"({(first - w['closed_at']).days} days open)")
    return gaps
