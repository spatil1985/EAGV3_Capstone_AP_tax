# UC-09 — Vendor TDS Verification (194C / 194J / 194I)

**Workstream A · Owner: Sudip · Verdict: 🟢 Buildable as a verification layer**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Are we deducting the right TDS on every vendor payment, under the right section?"*

(Verbatim from `spec.md` UC-09.)

---

## 2. Statutory basis

Cited with Income-tax Act 1961 numbering, as `spec.md` does. **See README: the
Income-tax Act 2025 is understood to apply from 1 April 2026 and renumbers these
sections.** The obligations are unchanged in substance.

| Section | Payment | Rate (long-standing) | Threshold |
|---|---|---|---|
| **194C** | Contractors (incl. transport, job work, catering) | 1% individual/HUF · 2% others | per constants table — confirm current |
| **194J** | Professional fees 10% · technical services 2% | 10% / 2% | per constants table — confirm current |
| **194I** | Rent — land/building 10% · plant/machinery 2% | 10% / 2% | per constants table — confirm current |

- **s.206AA** — no PAN → higher rate (20%, or twice the section rate).
- **Consequence of default:** interest under **s.201(1A)** (1% per month for
  non-deduction, 1.5% for deducted-not-deposited). The expense is disallowed under
  **s.40(a)(ia)** (30% of the payment) until the TDS is paid.
- **Consequence of over-deduction:** the vendor is short-paid, and the excess sits in
  their 26AS as a refund claim. It is a commercial dispute rather than a statutory one,
  but it is real.

---

## 3. Trigger

- **Document event:** on bill approval, before payment — TDS is deducted at credit or
  payment, whichever is earlier.
- **Monthly sweep:** before the 7th-of-next-month TDS deposit deadline, verify the
  month's deductions.
- **Period:** month of deduction. Thresholds are FY-cumulative per vendor per section.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Bill.list` | `{"limit": 1000}` | All bills. Filtering on `tds_amount` would need a range operator, which does not exist |
| `Party.get` | `{"id": vendor_id}` | PAN (for 206AA), vendor type (individual vs company → 194C rate) |
| `Item.get` | `{"id": item_id}` | SAC → which section applies |

**Bill fields** (confirmed live): `tds_name`, `tds_percentage`, `tds_amount`,
`tds_section_code`, `tds_section`, `items[].taxable_amount`, `items[].hsn_or_sac`,
`grand_total`, `balance_due`, `recurring_bill_id`, `vendor_id`.

---

## 5. Algorithm

1. **Base** = Σ `items[].taxable_amount` (TDS is on the value *excluding* GST when GST
   is shown separately — CBDT Circular 23/2017).
2. **Expected section** from the line's SAC, via a playbook table: 9965/9967 →
   194C (transport); 9983/9982 → 194J; 9972 → 194I; HSN goods chapters → **no TDS** (a
   pure goods purchase is 194Q territory, UC-13).
3. **Expected rate** from the section and the vendor type (194C 1% vs 2%); 206AA if no
   PAN.
4. **Expected amount** = `round(base × rate, 2)`, or 0 below the FY-cumulative threshold.
5. **Recompute the stored arithmetic:** `stored_expected = base × tds_percentage / 100`.
6. Emit findings:
   - `tds_arithmetic_wrong`: `|tds_amount − stored_expected| > ₹1`. The stored amount
     doesn't match its own stored rate.
   - `tds_section_missing`: `tds_amount > 0` and `tds_section` empty.
   - `tds_on_goods`: TDS present on a bill whose lines are all goods-chapter HSN.
   - `tds_rate_wrong`: stored rate ≠ expected rate for the section.
   - `tds_not_deducted`: expected > 0 and `tds_amount` = 0.
   - `tds_exceeds_bill`: `tds_amount > base` (**payable goes negative**).

### Worked example (REAL — BILL-2026-00227)

> **BILL-2026-00227** (`6f37ead0-39a3-42ad-8d2f-9c6ae6bab7f2`), dated 2026-09-27,
> vendor Chakan MIDC Utilities, one line: *Battery Tray Weldment (sub-assy)*, HSN
> `73269099` (goods), `taxable_amount = 8.55`.
> Stored: `tds_percentage = 5.0`, `tds_amount = 9178.58`, `tds_section = null`,
> `tds_section_code = "S8306/9691"`.
>
> ```
> stored_expected = 8.55 × 5% = 0.43        stored = 9,178.58   → tds_arithmetic_wrong (21,345× too high)
> tds_amount 9,178.58 > base 8.55                                → tds_exceeds_bill
> tds_section null                                               → tds_section_missing
> line HSN 7326 is goods                                         → tds_on_goods (no 194C/J/I applies)
> grand_total = −₹9,170.00                                       → payable is negative
> ```
>
> Output: *"BILL-2026-00227 (Chakan MIDC Utilities) — ₹9,178.58 TDS on an ₹8.55 goods
> bill with no section; payable has gone negative (−₹9,170.00). Do not pay; correct
> the bill."*

---

## 6. Known-bad data

- **N7 has grown from 9 bills to 101.** Every bill with non-zero `tds_amount` (101/227)
  is wrong. Every one of them is a recurring-template bill (`recurring_bill_id` set on
  101/101), and every one has `tds_section = null`. The scheduler runaway (B7/N6) is
  multiplying the defect daily.
- **`tds_section_code` holds product-code gibberish** (`PS8313/9639`, `FGS1676/9672`,
  `S8306/9691`) — the N127 seed-data class. It is not a section code.
- **`tds_percentage` is 0 on 53 of the 101** while `tds_amount` is non-zero. The stored
  rate is not a usable input either, so steps 2–3 (derive the section from SAC) are
  mandatory, not optional.
- **The other 126 bills carry no TDS at all.** Those are the candidates for
  `tds_not_deducted`, and the live data cannot tell us the vendor type or PAN status yet
  (§10).

---

## 7. Output contract

```json
{
  "finding_type": "tds_verification",
  "rule": "tds_arithmetic_wrong",
  "also": ["tds_exceeds_bill", "tds_section_missing", "tds_on_goods"],
  "entity_type": "Bill",
  "entity_id": "6f37ead0-39a3-42ad-8d2f-9c6ae6bab7f2",
  "entity_ref": "BILL-2026-00227",
  "counterparty_id": "448f90ae-5d19-4892-b667-516cfb4b7879",
  "counterparty_name": "Chakan MIDC Utilities",
  "base_amount": 8.55,
  "stored_tds_percentage": 5.0,
  "stored_tds_amount": 9178.58,
  "expected_tds_amount": 0.00,
  "expected_section": null,
  "difference": 9178.58,
  "currency": "INR",
  "status": "finding",
  "summary": "BILL-2026-00227 — ₹9,178.58 TDS on an ₹8.55 goods bill; payable negative. Do not pay."
}
```

**Sort:** `tds_exceeds_bill` first (blocks payment), then by `difference`.
**Run summary:** *"N bills with TDS; K wrong (₹X phantom TDS); M bills with negative
payable; J bills possibly missing TDS."*

---

## 8. Limits

- Verification only. It never sets `tds_amount`. Auto-deduction by threshold is GST-18,
  and not ours to build.
- Does not deposit TDS or file 26Q/27Q.
- Threshold tracking is FY-cumulative per vendor per section. It needs the full FY of
  bills, and this instance's ledger only starts 2026-06-07 (§10).

---

## 9. Validation

1. **Self-consistency check needs no oracle:** `tds_amount` vs `base × tds_percentage`
   is arithmetic. 101/101 fail live.
2. **Section-mapping control:** Chakan Transport Lines' GTA bills (SAC 996511, UC-03)
   must map to **194C**. They currently carry **no TDS** → `tds_not_deducted`
   candidate once thresholds are applied.
3. **Payable-sign control:** `grand_total < 0` ⇔ `tds_amount > base + tax` on all
   101. Confirmed live: the negative `grand_total` sum −₹52,53,352 tracks the stored
   TDS sum ₹52,57,489.59.

---

## 10. Open questions

- **Vendor type and PAN are not in the fields read so far.** `Party` must be checked for
  a PAN / entity-type field before `tds_rate_wrong` and 206AA can be implemented. If
  absent, that is a data gap to escalate.
- **Income-tax Act 2025 renumbering** — confirm the section references and thresholds
  (README caveat).
- **Should UC-09 re-report N7?** It is a filed bug. The spec emits per-bill findings,
  because each one blocks a payment, and adds a one-line reference to N7 in the run
  summary rather than claiming a new defect.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-09 Vendor TDS verification`.

**Call 1 — `Bill.list {"limit":1000}`** → 227 bills.

| Measure | Live value |
|---|---|
| Bills with `tds_amount ≠ 0` | **101** (N7 filed with **9**) |
| …whose `tds_amount` ≠ `base × tds_percentage` (>₹1) | **101 / 101** |
| …with `tds_percentage = 0` but `tds_amount > 0` | 53 |
| …with base (`Σ taxable_amount`) = 0 | 29 |
| …with `tds_section` null | 101 |
| …with `recurring_bill_id` set | 101 |
| Sum of stored `tds_amount` | **₹52,57,489.59** |
| Bills with negative `grand_total` / `balance_due` | **101 / 101** |

Worst offenders (stored TDS ₹2,03,954.62 on a ₹0 base, `grand_total` −₹2,03,955.00):
BILL-2026-00191 `40e120a1…`, 00175, 00155, 00126, 00109, 00106, 00103 — all from
recurring template `20fbba9d-a30f-43e5-8820-f97461ae307c` (the N6 template), one per
day.

**Call 2 — `Bill.get {"id":"40e120a1-c884-4d84-a20c-2433fb41ee1e"}`** (BILL-2026-00191)
```json
{"number":"BILL-2026-00191","recurring_bill_id":"20fbba9d-a30f-43e5-8820-f97461ae307c",
 "tds_percentage":0,"tds_amount":203954.62,"tds_section":null,"tds_section_code":"PS8313/9639",
 "grand_total":-203955.0,"balance_due":-203955.0}
```

**Call 3 — `Bill.get {"id":"6f37ead0-39a3-42ad-8d2f-9c6ae6bab7f2"}`** (BILL-2026-00227)
→ the §5 worked example, verbatim.

**What the live data changed:** N7 was reported as a 9-bill defect on three templates.
It is now 101 bills and growing by one per template per day. Recommend updating N7 on
the board with the new count. That is a status update to an existing report, not a new
filing.
