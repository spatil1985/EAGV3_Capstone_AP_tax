# UC-14 — Clinic: Healthcare Exempt vs Pharmacy Taxable Split

**Workstream B · Verdict: 🟡 Partial (fields support it; rules are playbook-carried; no clinic tenant)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Engine shared with:** [UC-07](uc-07-school-exempt-taxable-split.md) — same two-stage classifier, different rule table

---

## 1. Question

> *"Which parts of what we do are taxable, and are we charging GST on the right
> ones?"*

(Verbatim from `spec.md` UC-14.)

---

## 2. Statutory basis

- **Notification 12/2017-Central Tax (Rate), entry 74** — health care services by a
  clinical establishment, an authorised medical practitioner or para-medics are
  **exempt**.
- **Room rent** — ⚠️ from **18 July 2022** (Notification 4/2022-CT(Rate)), room rent
  **above ₹5,000 per day per patient** (non-ICU/CCU/ICCU/NICU) charged by a clinical
  establishment is **taxable at 5% without ITC**. ICU rooms remain exempt at any rate.
- **Outpatient pharmacy** — medicines sold over the counter to walk-in or OP patients
  are a supply of **goods at their HSN rate**. Medicines administered to **in-patients**
  as part of treatment form part of the exempt composite healthcare supply.
- **Cosmetic / plastic surgery** — taxable unless undertaken to restore or reconstruct
  anatomy or function lost to congenital defect, developmental abnormality, injury or
  trauma.
- **Consequence if wrong:** GST not charged on taxable streams (OP pharmacy, high-rent
  rooms, cosmetic procedures) is recovered from the clinic with interest and penalty.
  Charging GST on exempt consultation is collection without authority (s.76).

---

## 3. Trigger

As UC-07. **Monthly** before the return, **on item-master change**, and additionally
**on in-patient discharge** (the room-rent test is per patient per day, so it is
evaluated per stay).

---

## 4. Input contract

As UC-07 (`Item.list`, `Invoice.list {"direction":"receivable"}`,
`TaxExemption.list`), plus:

| Need | Field | Live status |
|---|---|---|
| IP vs OP pharmacy sale | none | ❌ **no patient-type field** on `Invoice` or `Invoice.items[]` |
| Room rent per day | line `qty` (days) × `rate` | ✅ derivable, **if** room rent is a separate item |
| ICU vs ward | none | ❌ needs a separate `Item` per room class |
| Cosmetic vs reconstructive | none | ❌ clinical judgement, not data |

---

## 5. Algorithm

**Stage 1 (master)** — identical to UC-07 §5 steps 1–2, plus clinic stream mapping:

| Stream | Identifier (playbook) | Treatment |
|---|---|---|
| Consultation / procedure | SAC 9993xx | exempt (entry 74) |
| In-patient medicine | HSN 3004 on an IP invoice | exempt (part of composite) |
| OP pharmacy | HSN 3004 on an OP invoice | taxable at HSN rate |
| Room — ICU class | item tagged ICU | exempt |
| Room — ward, ≤ ₹5,000/day | item tagged ward | exempt |
| Room — ward, > ₹5,000/day | item tagged ward | **5%, no ITC** |
| Cosmetic procedure | item tagged cosmetic | taxable (18%) |

**Stage 2 (transaction)** — as UC-07 steps 4–7, plus:

- **Room-rent test:** for each room line, `per_day = rate` (when `qty` is days).
  Taxable if the room class is ward and `per_day > 5,000`. The tax must be exactly 5%
  (`POST /api/accounting/tax/compute {"amount": x, "rate": 5}`), and the clinic must not
  claim ITC attributable to it.
- **Pharmacy IP/OP split:** without a patient-type field, the conservative default is
  **every pharmacy line is OP (taxable)**. Stated in the output.

### Worked example (constructed — no clinic tenant exists)

> Invoice to an in-patient for a 3-day stay: room *Deluxe Ward* 3 × ₹6,500; consultation
> ₹2,000 (SAC 999312); medicines ₹4,800 (HSN 3004).
>
> ```
> room per day 6,500 > 5,000, ward class → taxable 5% on 19,500 = ₹975.00 (no ITC)
> consultation                           → exempt, tax 0
> medicines on an IP invoice             → exempt (composite) — but platform cannot tell IP from OP
>                                          → conservative default: taxable at HSN rate, flagged "ip_op_unknown"
> ```

---

## 6. Known-bad data

Everything in UC-07 §6 applies: classification must come from `Item.tax_preference`,
never zero-tax lines; the item master has live contradictions; and Rule 0 applies.
Additionally:

- **Shelf-life/batch items on this instance are hand tools**, not medicines (UC-16). No
  live record resembles a pharmacy line.

---

## 7. Output contract

Same as UC-07 §7 (`supply_classification` rows + a monthly `turnover_split` aggregate
for UC-15), with two extra rules: `room_rent_threshold` and `ip_op_unknown`.

---

## 8. Limits

- Cannot distinguish IP from OP pharmacy, ICU from ward, or cosmetic from
  reconstructive. The platform has no fields for these, so the spec defaults
  conservatively and says so.
- Never edits items or invoices. Not tax or medical-billing advice.

---

## 9. Validation

1. **Engine regression:** every UC-07 control (INV-2026-00254 → `exempt_but_taxed`)
   must pass unchanged. The engines are the same.
2. **Room-rent boundary fixture:** ₹5,000.00/day → exempt; ₹5,000.01/day → 5%; ICU at
   ₹9,000/day → exempt.
3. **No live validation possible** — see F2 (sandbox) for a seeded clinic tenant.

---

## 10. Open questions

- **Patient-type field:** is this a platform gap worth filing (alongside F18), or
  handled by using separate `Item`s for IP-medicine vs OP-medicine? The latter works
  today, with no platform change. Recommend it in the playbook.
- **One engine or two files?** UC-07 and UC-14 share all code and differ only in the
  rule table. Consider merging into one spec with two rule tables at review.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-14 Clinic exempt-taxable split`.

**Call 1 — `Item.list {"limit":1000}`** → 103 items. No item has a healthcare SAC
(9993xx) or a medicine HSN (3004). Items with `shelf_life_days > 0` (29) are tools such
as *"Pipe Wrench 138mm (Pair)"*, shelf life 28 days.

**Call 2 — `Invoice.get {"id":"289df9d7-d856-499e-b751-91db971fcdd4"}`** (INV-2026-00254)
— the same engine control as UC-07. It must fire `exempt_but_taxed`.

**What the live data changed:** nothing in the verdict. It confirms that no live data
can validate this use case, and that the engine (not the rule table) is what can be
tested today.
