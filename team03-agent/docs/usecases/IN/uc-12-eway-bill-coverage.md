# UC-12 — E-Way Bill Coverage and Expiry Audit

**Workstream C · Verdict: 🟢 Buildable as a coverage and expiry audit**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

> Start here in WS-C: it is the 🟢 use case with the most live data behind it.

---

## 1. Question

> *"Is anything moving on the road right now without valid documentation?"*

(Verbatim from `spec.md` UC-12.)

---

## 2. Statutory basis

- **Section 68, CGST Act + Rule 138, CGST Rules** — an e-way bill must be generated
  before moving goods whose consignment value exceeds **₹50,000**, whether for supply,
  job work, or other reasons.
- **Rule 138(10) — validity:** for normal cargo, **1 day per 200 km** or part (for
  over-dimensional cargo, 1 day per 20 km). A day ends at midnight after 24 hours from
  generation.
- **Section 129 — detention and penalty.** `spec.md` says "tax + 100%". **Our
  understanding is that since 1 January 2022 the penalty is 200% of the tax payable**
  (Finance Act 2021 amendment). Confirm before quoting (README caveat).
- **Consequence:** goods detained in transit, and the penalty is payable to release
  them. For a manufacturer this is a line stoppage at the customer.

---

## 3. Trigger

- **Document event:** on an outward `Invoice` / `DeliveryChallan` moving to a
  despatched state. Check that an EWB exists before the truck leaves.
- **Scheduled, several times daily:** re-check validity of in-transit EWBs. Validity is
  measured in days and expiry happens mid-journey.
- **Period:** point-in-time.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `EWayBill.list` | `{"limit": 1000}` | 100 live |
| `Invoice.list` | `{"direction": "receivable", "limit": 1000}` | Outward documents |
| `DeliveryChallan.list` | `{"limit": 1000}` | Outward non-supply movement |
| `Bill.list` | `{"limit": 1000}` | Inward movement where we arrange transport (`transaction_type: bill`) |

**EWayBill fields** (every field, from a live record): `id`, `number`,
`transaction_id`, `transaction_type` (`invoice | delivery_challan | bill`),
`eway_bill_number`, `customer_gstin`, `generation_date`, `expiry_date`, `total`,
`vehicle_number`, `distance_km`, `is_over_dimensional`, `transporter_id`, `status`
(`active | generated | not_generated`).

**Join key:** `EWayBill.transaction_id` = the source document's `id`, qualified by
`transaction_type`.

---

## 5. Algorithm

**Part A — validity of existing EWBs**
1. For each EWB with `status ∈ {active, generated}`:
   - **No number:** `eway_bill_number` empty → `ewb_not_real`. An EWB without a number
     was never issued by the NIC portal, so it is not valid in transit.
   - **Expired:** `expiry_date < today` and the movement is not confirmed complete →
     `ewb_expired_in_transit`.
   - **Validity arithmetic:** expected days =
     `ceil(distance_km / (20 if is_over_dimensional else 200))`. If
     `expiry_date − generation_date` ≠ expected days → `ewb_validity_wrong`.
   - **No vehicle:** `vehicle_number` empty on an `active` EWB → `ewb_part_b_missing`
     (Part-B not updated; not valid for movement).

**Part B — coverage of outward documents**
2. For each outward document (receivable invoice / challan) with goods lines (any
   `hsn_or_sac` not starting `99`) and `grand_total > 50,000`:
   - no EWB with `transaction_id = document.id` → `ewb_missing`.
3. **Suppress** documents that have not moved: `Invoice.status = draft`,
   `DeliveryChallan.status = draft`. Report them in context only, as "will need an EWB
   before despatch".

### Worked example (REAL — EWayBill `ce6ab7df-cb47-42fb-95a9-e65063f1e534`)

> `transaction_type: invoice`, `transaction_id: abf1b643-e64b-4682-bb68-11466aa4d71d`,
> `total ₹1,24,267.28`, `distance_km 217.81`, `generation_date 2026-07-26`,
> `expiry_date 2026-07-28`, `status: active`, `eway_bill_number: null`,
> `vehicle_number: null`.
>
> ```
> expected validity = ceil(217.81 / 200) = 2 days → 07-26 + 2 = 07-28 ✓ (arithmetic correct)
> eway_bill_number null                 → ewb_not_real
> vehicle_number null                   → ewb_part_b_missing
> expiry 2026-07-28 < today 2026-09-28  → ewb_expired_in_transit (62 days)
> ```
>
> Output: *"EWB for invoice abf1b643… (₹1,24,267.28, 218 km) is marked active but has no
> EWB number and no vehicle, and expired on 28 Jul. It is not valid documentation."*

---

## 6. Known-bad data

- **80 of 80 `active`/`generated` EWBs have no `eway_bill_number`.** On this instance,
  `status` does not mean what it says. **Never trust `status` alone**: the number is the
  proof of issuance. (Candidate new bug report.)
- **`transaction_type: bill`** (33 EWBs) — inward movements. Only relevant where the
  recipient arranges transport. Report them separately from outward coverage.
- **Coverage join is sparse:** only 54 of 280 large goods invoices link to any EWB.
  Most are `draft` (step 3 suppresses them), but some are `paid`, e.g. INV-2026-00056,
  ₹46,53,866.

---

## 7. Output contract

```json
{
  "finding_type": "eway_bill",
  "rule": "ewb_not_real | ewb_expired_in_transit | ewb_validity_wrong | ewb_part_b_missing | ewb_missing",
  "entity_type": "EWayBill",
  "entity_id": "ce6ab7df-cb47-42fb-95a9-e65063f1e534",
  "source_document_type": "invoice",
  "source_document_id": "abf1b643-e64b-4682-bb68-11466aa4d71d",
  "consignment_value": 124267.28,
  "distance_km": 217.81,
  "expiry_date": "2026-07-28",
  "days_past_expiry": 62,
  "status": "finding",
  "summary": "…"
}
```

**Sort:** `ewb_missing` on non-draft documents first (goods may be on the road with
nothing), then `ewb_not_real`, then expiry.

---

## 8. Limits

- Does not generate, extend or cancel EWBs. `EWayBill.generate` / `activate` exist as
  tools, but generation against the NIC portal is GST-29 and out of scope.
- Cannot know whether goods are physically still in transit. "Expired and still active"
  is flagged; closure is a human confirmation.
- Consignment value uses `grand_total`. Rule 138 uses value *including* tax, so this
  matches.

---

## 9. Validation

1. **Validity arithmetic has a real positive control:** the worked example's 2-day
   validity for 217.81 km is correct. The formula implementation must agree with the
   platform on every EWB that has both dates.
2. **Counts on the live snapshot must reproduce:** 80 `ewb_not_real`, 67
   active/generated past expiry.
3. **Status-enum check:** `EWayBill.list {"status":"not_generated"}` → 20 (§11).

---

## 10. Open questions

- **Is `status: active` with no number a platform defect or a demo-mode artefact?** If
  EWB generation is stubbed on this instance (no NIC connection), every EWB will lack a
  number forever, and `ewb_not_real` will fire on everything. Ask the platform team
  before filing.
- **Inward EWBs (`transaction_type: bill`):** in scope for Seat 03 (Payables), or
  logistics? Suggest: report them, don't block on them.
- **Multi-vehicle / transhipment:** the schema has one `vehicle_number`. It cannot
  represent Part-B updates.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-12 E-way bill coverage`.

**Call 1 — `EWayBill.list {"limit":1000}`** → 100 EWBs.

| Measure | Live value |
|---|---|
| `status`: active / generated / not_generated | 52 / 28 / 20 |
| `transaction_type`: invoice / delivery_challan / bill | 33 / 34 / 33 |
| active or generated **with no `eway_bill_number`** | **80 / 80** |
| active or generated **with `expiry_date` < today** | **67** |

Oldest expired "active" EWB: `ce6ab7df-cb47-42fb-95a9-e65063f1e534` (worked example).

**Call 2 — `Invoice.list {"direction":"receivable","limit":1000}`** → 320 invoices;
**280** have goods lines and `grand_total > ₹50,000`; **226** have no EWB with
`transaction_id = id`. Largest uncovered:

| Invoice | Date | `grand_total` | Status |
|---|---|---|---|
| INV-2026-00056 `377aad32…` | 2026-03-30 | ₹46,53,866.00 | **paid** |
| INV-2026-00197 `5d0bcefe…` | 2026-09-17 | ₹42,39,205.31 | draft |
| INV-2026-00221 `ae564c5b…` | 2026-09-17 | ₹42,39,205.31 | draft |
| INV-2026-00205 `a15ce06b…` | 2026-09-17 | ₹35,03,966.04 | draft |

**What the live data changed:** Part A's `ewb_not_real` check was not in `spec.md`. It
exists because every "active" EWB on the instance turned out to lack a number.
