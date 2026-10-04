# UC-32 — Refund of Accumulated Input Credit: Zero-Rated Supplies (Rule 89(4)) and Inverted Duty (Rule 89(5))

**Domains: agency (exports of services), manufacturing (SEZ/exports, inverted rates), retail (inverted rates) · Category: input tax · Verdict: 🟡 Partial — the refund computation runs live; filing a refund is out of scope**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

This is "unclaimed" money of a different kind: credit that can't be used against output tax, but can be
refunded in cash.

---

## 1. Question

> *"We have credit piling up because we export or because our inputs are taxed higher than our sales. How much can we get refunded, and by when?"*

---

## 2. Statutory basis

- **s.54(3) CGST Act:** unused input credit can be refunded in two cases:
  - **(i)** zero-rated supplies made **without paying tax** (under LUT: exports, SEZ);
  - **(ii)** an **inverted duty structure**, where tax on inputs is higher than tax on output.
    Notified goods and services are excluded.
- **Rule 89(4)** (zero-rated): `refund = (zero-rated turnover × net credit) ÷ adjusted total turnover`.
  Net credit is credit on **inputs and input services**; capital goods are excluded.
- **Rule 89(5)** (inverted duty), as amended by Notification 14/2022-CT:
  `refund = (inverted turnover × net credit ÷ adjusted total turnover) − (tax on inverted turnover × net
  credit ÷ credit on inputs and input services)`. Net credit here is **inputs only**; input services are
  excluded. The Supreme Court upheld this in *VKC Footsteps* (2021).
- **s.54(1):** the claim must be made within **2 years** of the relevant date. That is the export or
  invoice date for zero-rated supplies, and the return due date for the period for inverted duty.
- **Consequence:** a missed window means the credit stays trapped for good, as a cost.

---

## 3. Trigger

- **Scheduled monthly** after GSTR-3B. Claims can be per tax period or bunched across periods within an
  FY.
- **Scheduled warning** when a period's 2-year window is within 90 days.
- **On request.**

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Invoice.list` | Receivable: `gst_treatment` (`sez\|overseas\|deemed_export`), `taxable_value`, `taxes[]`, `date`, `currency`, `exchange_rate` |
| `TaxExemption.list` | LUT evidence: rows "Export under LUT" and "SEZ supply – Letter of Undertaking, no IGST" ([UC-20](uc-20-export-lut-tracking.md)) |
| `Bill.list` | `itc_eligibility` (`input` / `input_services` / `capital_goods`), `ims_status`, `items[].tax_percentage`, tax by head |
| `Item.list` | `inter_state_tax_rate` / `intra_state_tax_rate`, for the inverted-rate test |

---

## 5. Algorithm

1. **Period:** the claim period (month or FY).
2. **Zero-rated turnover:** taxable value of live SEZ, export and deemed-export invoices **with zero
   tax**, i.e. under LUT. Invoices that paid IGST are a different refund route.
3. **Adjusted total turnover:** all live outward taxable value in the period, excluding supplies under
   the inverted-duty claim if both are made.
4. **Net credit (89(4)):** credit on bills with `itc_eligibility ∈ {input, input_services}`, not
   IMS-rejected, net of reversals (UC-01/UC-25).
5. **`refund_eligible_zero_rated`** = `zero_rated × net_credit ÷ ATT`, capped at the credit balance.
6. **Inverted test (89(5)):** compare each output line's rate with the weighted rate of its inputs. If
   input rate > output rate, compute the formula with net credit = inputs only →
   `refund_eligible_inverted`.
7. **`refund_window_closing`:** for each period with an indicative refund, `2 years − (today − relevant
   date) ≤ 90 days`.

### Worked example (REAL: FY 2026-27 to date, indicative)

> - **Zero-rated turnover:** 7 SEZ invoices in FY 2026-27 with zero tax → **₹13,05,145.88**.
> - **Adjusted total turnover:** ₹6,44,70,617.02.
> - **Net credit:** inputs ₹18,58,462.59 + input services ₹6,724.43 = ₹18,65,187.02. Capital goods
>   (₹15,913.60) are excluded.
>
> ```
> refund (89(4)) = 13,05,145.88 × 18,65,187.02 ÷ 6,44,70,617.02 = ₹37,758.92   (2.02% of net credit)
> ```
>
> **Inverted test:** outward tax is 18% throughout ("CGST @ 9%"/"SGST @ 9%"/"IGST @ 18%"). Input lines
> carry 5%, 12% and 18%, so no input is taxed above output → **no inverted-duty refund**.
>
> Output: *"About ₹37,759 of FY 2026-27 credit is refundable on SEZ supplies under LUT, once the LUT is
> confirmed valid. No inverted-duty position exists."*

---

## 6. Known-bad data

- **LUT validity can't be proved.** The `TaxExemption` LUT row has no dates and no party link (UC-20). The
  refund depends on it, and validity comes from `config/overrides/` (G7).
- `items[].tax_percentage` is null on all outward lines, so the output rate is read from the `taxes[]` head
  names.
- FY 2025-26 credit is absent from the ledger (bills start 2026-06-07), so FY 2025-26 refunds can't be
  computed.

---

## 7. Output contract

`finding_type: "itc_refund"`, `rule ∈ {refund_eligible_zero_rated, refund_eligible_inverted,
refund_window_closing, lut_unverified}`. Fields: `period`, `zero_rated_turnover`,
`adjusted_total_turnover`, `net_itc`, `refund_amount`, `relevant_date`, `window_closes`.

---

## 8. Limits

- Never files RFD-01; there is no refund module. It reports the eligible amount and the deadline.
- *Indicative only:* the statutory formula uses the credit actually availed in the period's returns,
  which the platform doesn't record per document (UC-24 §10).

---

## 9. Validation

1. **Live:** recompute the three inputs and the formula above.
2. **Fixture (89(4)):** zero-rated 40, ATT 100, net credit 50 → refund 20.
3. **Fixture (89(5)):** inverted turnover 100, ATT 100, net credit on inputs 20, credit on inputs and
   input services 25, tax on inverted turnover 5 → 20 − 5 × 20 ÷ 25 = 16.

---

## 10. Open questions

- Are the FY 2026-27 SEZ invoices paid in foreign exchange or INR? That doesn't matter for SEZ, but it does
  for exports of services (UC-20's two tests).
- Should IGST-paid exports (the refund under Rule 96, through the shipping bill) be a separate use case?
  No IGST-paid export exists in the data today.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Invoice.list {"limit":1000}` → 15 live SEZ invoices overall (taxable ₹39,89,830.03, tax ₹0), of which 7
  are in FY 2026-27 (₹13,05,145.88). No `overseas` or `deemed_export` receivable invoices.
- `Bill.list {"limit":1000}` → FY 2026-27 open bills, IMS-rejected excluded:
  - inputs ₹18,58,462.59;
  - input services ₹6,724.43;
  - capital goods ₹15,913.60.
  Input-line rates: 5% ×6, 12% ×5, 18% ×5, 9% ×7 (half-rate rows), 0% ×14.
- `TaxExemption.list` → 8 rows, including "Export under LUT" and "SEZ supply — Letter of Undertaking, no
  IGST" (`associated_with: contact`), with no dates.
