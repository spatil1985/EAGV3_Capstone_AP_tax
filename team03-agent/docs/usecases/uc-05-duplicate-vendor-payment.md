# UC-05 — Duplicate Vendor Payment Detection

**Workstream A · Owner: Sudip · Verdict: 🟡 Rework required (unchanged by live data)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Is any vendor being paid twice?"*

(Verbatim from `spec.md` UC-05 — the Core Challenge Prompt.)

---

## 2. Statutory basis

This is a financial control rather than a statutory obligation, but it has two
statutory edges:

- **Section 16(2), CGST Act** — ITC is available once per tax invoice. A duplicate bill
  booked twice carries its GST twice, so a duplicate *payment* is usually also a
  duplicate *credit claim*, recoverable with interest under **s.50(3)** (18% p.a. on
  ITC wrongly availed *and utilised*) and penalty under **s.73/74**.
- **Companies Act 2013, s.134(5)(e) / s.143(3)(i)** — directors' responsibility and
  auditor reporting on internal financial controls. Duplicate-payment prevention is a
  standard IFC test.

**Consequence if missed:** cash lost to the vendor (recoverable only by negotiation),
plus the doubled ITC reversed with interest on assessment.

---

## 3. Trigger

- **Document event (primary):** on every new `Bill` in `draft`/`open`, before it is
  approved for payment. A duplicate caught before payment costs nothing; after payment
  it costs a recovery conversation.
- **Scheduled sweep (secondary):** daily, over all `open` bills. It catches pairs where
  both documents were created before the event hook existed, and the recurring-scheduler
  runaway (B7/N6) that creates bills without a user action.
- **Period:** current financial year (from `Company.fiscal_year_start`, live value
  `2026-04-01`) plus the last 90 days of the previous FY, because year-end is where
  re-keyed duplicates cluster.

---

## 4. Input contract

| Tool (MCP) | Arguments used | Why |
|---|---|---|
| `Bill.list` | `{"limit": 1000, "offset": n}` — page; no server-side filter needed | All bills, all statuses |
| `PaymentMade.list` | `{"limit": 1000}` | Whether either side of a pair has already been paid |
| `Party.get` | `{"id": vendor_id}` | `name`, `gst_no` for the exact-tier key and the output row |
| `endpoint.accounting.bill_match` | `{"bill_id": id}` | Over-billing against the PO (`billed_to_date_qty > ordered_qty`) is a duplicate signal the amount heuristic cannot see |

**Fields read (all confirmed on live `Bill` records, 2026-09-28):**

| Field | Use |
|---|---|
| `id`, `number` | identity (`number` is the platform's `BILL-2026-nnnnn`) |
| `bill_number` | **supplier's** document number — the exact-tier key. **Populated on only 18 of 227 bills** |
| `vendor_id` | pair scope |
| `date` | FY assignment and ±3-day window |
| `grand_total` | amount key. **Can be negative** (N7) — see §6 |
| `recurring_bill_id` | the suppression gate — 126 of 227 bills carry one |
| `purchase_order_id` | two bills on different POs are weaker duplicates than two on the same PO |
| `status` | `draft`/`open` — only unpaid pairs are actionable |
| `items[]._item_id_display`, `items[].qty`, `items[].rate` | line-content comparison for the `suspicious` tier |
| `created_at` | two bills created seconds apart by the seeder or a double-submit |

---

## 5. Algorithm

Three tiers, evaluated in order. A pair is reported at the highest tier it reaches.

**Tier 1 — `exact` (document identity; Clear's key)**
1. For every bill with a non-empty `bill_number`, compute
   `key = (vendor.gst_no or vendor_id, normalise(bill_number), fy(date))`,
   where `normalise` upper-cases and strips spaces, `-`, `/` and leading zeros.
2. Any key with ≥2 bills is an `exact` duplicate, regardless of amount or date.

**Tier 2 — `over_billed` (quantity identity; new, from live data)**
3. For each bill with `purchase_order_id`, call `endpoint.accounting.bill_match`. If any
   `live.lines[]` has `billed_to_date_qty > ordered_qty`, the PO has been billed beyond
   what was ordered. Report the bill as `over_billed`, even if no second bill shares its
   amount.

**Tier 3 — `suspicious` (amount proximity; the old heuristic, now gated)**
4. Group bills by `vendor_id`. Within a group, pair bills with identical `grand_total`
   (≠ 0) and `|date_a − date_b| ≤ 3` days.
5. **Recurring gate:** drop the pair if both bills share a non-null `recurring_bill_id`.
   Same template, different period is *expected* repetition, not duplication. (The
   runaway scheduler is B7/N6, a platform defect reported separately. UC-05 must not
   double-report it.)
6. **Strengthen or weaken** the surviving pairs:
   - same line items (`_item_id_display`, `qty`, `rate`) → `suspicious_strong`
   - different line items, same total → `suspicious_weak`
   - `created_at` within 5 seconds of each other → note `possible double-submit`
7. **Paid check:** join `PaymentMade.bills[]`. If both sides are paid, the finding is a
   **recovery** case; if one or neither is paid, it is a **prevention** case (hold the
   unpaid one).

### Worked example (real data, 2026-09-28)

> **BILL-2026-00059** (`5b375f12-ca42-457b-9f9a-6aa245fb1aa9`) and **BILL-2026-00029**
> (`c729be05-d286-4147-86ab-88073d8fa3ca`). Vendor: Sandvik Tooling India. Both dated
> 2026-09-12, both `grand_total` ₹3,53,554.00, both `status: open`.
>
> - Tier 1: `bill_number` is empty on both → exact tier **cannot run**.
> - Tier 3: same vendor, same amount, 0 days apart. `recurring_bill_id` is null on both
>   → **gate does not suppress**.
> - Step 6: identical line items, "EN19 Round Bar 40mm; EN8 Round Bar 25mm" on both →
>   `suspicious_strong`. Different POs (`68e1c19b…` vs `59dd7e11…`), and `created_at`
>   1.37 s apart (17:19:39.470 / 17:19:40.840).
> - Step 7: neither is paid → **prevention**: hold BILL-2026-00029 pending vendor
>   confirmation.
>
> Output: *"BILL-2026-00059 / BILL-2026-00029 (Sandvik Tooling India) — ₹3,53,554.00
> each, same items, same day, different POs. Hold one pending vendor confirmation."*

---

## 6. Known-bad data

- **`grand_total` is negative on 101 bills** (N7/UC-09 — phantom TDS). Tier 3 matches
  on `grand_total`, so two corrupt recurring bills "match" on −₹2,03,955.00. The
  recurring gate suppresses them, but **exclude `grand_total ≤ 0` from Tier 3
  outright**. A negative-total bill is a `data_quality` finding for UC-09, not a
  duplicate candidate.
- **`bill_number` is empty on 209/227 bills.** Tier 1 is the right design but currently
  covers 8% of the ledger. Report its coverage in every run's summary, so a clean Tier 1
  is never mistaken for "no duplicates".
- **Seed-data clustering.** 213 of 227 bills are dated 2026-09, and dozens were created
  within ~4 s on 2026-09-12 17:19. On this instance, "same day" is weak evidence.
  Line-item identity (step 6) carries the weight.

---

## 7. Output contract

```json
{
  "finding_type": "duplicate_payment",
  "tier": "suspicious_strong",
  "rule": "same_vendor_same_amount_3d",
  "entity_type": "Bill",
  "entity_id": "c729be05-d286-4147-86ab-88073d8fa3ca",
  "entity_ref": "BILL-2026-00029",
  "pair_entity_id": "5b375f12-ca42-457b-9f9a-6aa245fb1aa9",
  "pair_entity_ref": "BILL-2026-00059",
  "counterparty_id": "97717ad7-4e5c-44c1-b8be-780dd5d371d7",
  "counterparty_name": "Sandvik Tooling India",
  "amount": 353554.00,
  "days_apart": 0,
  "same_line_items": true,
  "paid_state": "neither_paid",
  "action": "hold_one",
  "currency": "INR",
  "status": "finding",
  "summary": "BILL-2026-00059 / BILL-2026-00029 (Sandvik Tooling India) — ₹3,53,554.00 each, same items, same day, different POs. Hold one pending vendor confirmation."
}
```

- **Sort:** tier (`exact` > `over_billed` > `suspicious_strong` > `suspicious_weak`),
  then `amount` descending.
- **Run summary leads with coverage:** *"N candidate duplicates (x exact, y over-billed,
  z suspicious). Exact-tier coverage: 18/227 bills carry a supplier document number.
  208 recurring pairs suppressed."*

---

## 8. Limits

- Never cancels, voids or edits a bill. The strongest action is a hold via
  `playbooks/duplicate_audit.md`, and only after human confirmation. Writes to this
  shared ledger affect Teams 01 and 02.
- Does not decide which of a pair is the "real" one. It flags both and recommends
  holding the later-created one.
- Does not detect duplicates split across vendors (same supplier under two `Party`
  records). That needs Party de-duplication, which is out of scope.

---

## 9. Validation

1. **Control group already exists in the data:** 208 pairs sharing a
   `recurring_bill_id` must be suppressed. If any appears in output, the gate is
   broken.
2. **Positive control:** the Sandvik pair above must appear as `suspicious_strong`.
3. **Over-billing control:** BILL-2026-00101 (`08837e85…`) must appear as
   `over_billed`. Live `bill_match`: `ordered_qty 2.0`, `billed_to_date_qty 4.0`, flag
   `qty_over_ordered`.
4. **Regression against the three Keystone false positives** that motivated the rework
   (`scripts/invoice_matcher.py`, amount-only). All three were recurring-template pairs
   and must be suppressed.

---

## 10. Open questions

- **Tier 1 is starved.** With 92% of bills lacking `bill_number`, should the agent
  escalate "supplier invoice number missing" as a `data_quality` finding at bill entry?
  That is the only way the strong key ever becomes usable.
- **Different POs, same items, same amount** (the Sandvik pair): legitimate repeat
  order, or duplicate? The data cannot tell. This is exactly the case for a human.
- **Should UC-05 own the B7/N6 recurring runaway?** Currently no: it is a platform
  defect already reported, and flagging 208 pairs would bury the 10 real candidates.
  Revisit if B7 is closed as "won't fix".

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-05 Duplicate vendor payment`.

**Call 1 — all bills**
```http
POST {{base_url}}/api/mcp
{"jsonrpc":"2.0","id":1,"method":"tools/call",
 "params":{"name":"Bill.list","arguments":{"limit":1000}}}
```
→ 227 bills. Tier results computed client-side:

| Measure | Value |
|---|---|
| Bills with supplier `bill_number` | **18 / 227** |
| Tier 1 `exact` groups | **0** |
| Tier 3 raw pairs (same vendor, same `grand_total`, ≤3 days) | **218** |
| …suppressed by `recurring_bill_id` gate | **208** |
| …surviving `suspicious` pairs | **10** |
| Distinct `recurring_bill_id`s / bills carrying one | 36 / 126 |

Surviving pairs (first six; all `open`, all dated 2026-09-12, none recurring):

| Pair | Vendor | `grand_total` | Items identical? |
|---|---|---|---|
| BILL-2026-00059 / 00029 | Sandvik Tooling India | ₹3,53,554.00 | **yes** |
| BILL-2026-00098 / 00067 | Nashik Heat Treaters | ₹95,580.00 | no line detail |
| BILL-2026-00033 / 00051 | Godrej Material Handling | ₹48,380.00 | no line detail |
| BILL-2026-00096 / 00092 | Nashik Heat Treaters | ₹47,790.00 | no line detail |
| BILL-2026-00087 / 00037 | Suvarna Electricals | ₹40,120.00 | no line detail |
| BILL-2026-00084 / 00035 | Suvarna Electricals | ₹36,108.00 | no line detail |

**Call 2 — over-billing signal**
```http
POST {{base_url}}/api/mcp
{"jsonrpc":"2.0","id":2,"method":"tools/call",
 "params":{"name":"endpoint.accounting.bill_match",
           "arguments":{"bill_id":"08837e85-481c-4ae3-9127-28abcd80797e"}}}
```
Trimmed real response (inside `result.content[0].text`):
```json
{"result":{"bill_id":"08837e85-481c-4ae3-9127-28abcd80797e","live":{
  "basis":"receipts_against_purchase_order","status":"exceeds_tolerance",
  "lines":[{"ordered_qty":2.0,"received_qty":2.0,"billed_qty":2.0,
            "billed_to_date_qty":4.0,"flags":["qty_over_ordered"],
            "po_rate":1284.272,"bill_rate":1284.272}]},
  "recorded_status":null}}
```
**What it proves:** BILL-2026-00101's PO has been billed twice for the same 2 units. An
amount-only matcher would never see this, because the other bill need not share the
amount.

**What the live data changed:** Tier 2 (`over_billed`) is new. It was not in `spec.md`
and exists because `bill_match` turned out to compute billed-to-date quantities.
