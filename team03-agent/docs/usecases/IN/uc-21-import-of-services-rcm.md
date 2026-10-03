# UC-21 — Import of Services: Reverse Charge

**Workstream A · Verdict: 🟢 Buildable (spec.md) → 🟡 Partial (live data: the classification it relies on is unreliable)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Pairs with:** [UC-03](uc-03-rcm-self-invoicing.md) — same check, different trigger; ship as one playbook · **Uses:** UC-20's place-of-supply contract

---

## 1. Question

> *"Which foreign supplier bills create a GST liability we have to pay ourselves?"*

(Verbatim from `spec.md` UC-21.)

---

## 2. Statutory basis

- **Section 5(3), IGST Act + Notification 10/2017-Integrated Tax (Rate), entry 1** —
  on **import of services** by any person in the taxable territory from a supplier
  outside India, IGST is payable by the **recipient** under reverse charge.
- **Section 2(11), IGST Act — import of services:** supplier outside India, recipient in
  India, place of supply in India.
- **OIDAR** (online information and database access — SaaS, cloud) supplied to a
  *registered* business falls under the same RCM rule. To unregistered persons, the
  foreign supplier pays.
- **ITC** on the RCM tax paid is available (s.16) once paid, if the service is used for
  business. So a missed RCM is **cash-neutral when found early**, and an **interest and
  penalty cost** when found on audit.
- **Consequence if missed:** undeclared IGST, with s.50 interest from the date the
  liability arose (time of supply for RCM services, s.13(3): earlier of payment date or
  60 days from invoice). The matching ITC is claimable only after the tax is paid.

---

## 3. Trigger

As UC-03. **On every bill** before approval, plus a **monthly sweep** before GSTR-3B
(Table 3.1(d), inward supplies liable to reverse charge).

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Bill.list` | `{"gst_treatment":"overseas","limit":1000}` | 12 live |
| `Bill.list` | `{"is_reverse_charge": true, "limit":1000}` | **boolean** (README Rule 6); 8 live |
| `Party.get` | `{"id": vendor_id}` | Country / `gst_treatment` of the vendor — the second opinion |

**Fields:** `Bill.gst_treatment`, `Bill.is_reverse_charge`, `Bill.currency_code`,
`Bill.items[].hsn_or_sac`, `Bill.items[].taxable_amount`, `Party.gst_treatment`,
`Party.name`, `Party.gst_no`.

---

## 5. Algorithm

1. **Is the vendor genuinely overseas?** Require **two** agreeing signals out of:
   - `Bill.gst_treatment = overseas`;
   - `Party.gst_treatment = overseas`;
   - `Bill.currency_code ≠ INR`;
   - vendor has no Indian GSTIN (`Party.gst_no` empty).
   One signal only → `classification_conflict`, not an RCM finding.
2. **Is it a service?** Any line with SAC (`99…`) or `Item.product_type = services`.
   Goods imports are customs IGST at the border, not RCM. Exclude them.
3. **For genuine overseas services:**
   - `is_reverse_charge = 0` → **`rcm_import_undeclared`**: liability = IGST at the
     service's rate × `taxable_amount` (via `POST /api/accounting/tax/compute`).
   - `is_reverse_charge = 1` but the bill carries supplier-charged tax → `rcm_double_tax`
     (the foreign supplier cannot charge Indian GST).
4. Emit `rcm_undeclared_liability` rows (the UC-03 shape).

### Worked example (REAL — why step 1 exists)

> **BILL-2026-00090** (`05ede91a-52b9-40c9-8d80-fde2f5499bc7`): `gst_treatment:
> overseas`, `is_reverse_charge: 1`, `currency_code: INR`, vendor **Bosch Rexroth
> India**, whose `Party.gst_treatment` is **`business_gst`**; line HSN `82055900`
> (goods), `grand_total ₹79,091.00`.
>
> ```
> signals for "overseas": Bill.gst_treatment only (1 of 4)
>   Party says business_gst · currency INR · vendor name ends "India"
> → classification_conflict, NOT rcm_import_undeclared
> line is goods (HSN 8205), not a service → out of scope for import-of-services RCM anyway
> ```
>
> Output: *"BILL-2026-00090 is tagged overseas with reverse charge, but the vendor is an
> Indian GST-registered company billing goods in INR. The tag is wrong; no import-of-
> services liability arises."*

A naive UC-21 (`gst_treatment = overseas and is_reverse_charge = 0`) would report **8
false RCM liabilities** on this data (§11).

---

## 6. Known-bad data

- **All 12 `overseas` bills are from Indian vendors, in INR.** The vendors are Bosch
  Rexroth India, Shreeji Powder Coating, Bharat EV Motors, Kirloskar Pumps and Tata
  Ficosa, all `Party.gst_treatment = business_gst`. The bill-level tag is unreliable,
  which is why step 1 requires two signals.
- **No Party anywhere is `overseas`** (0 of 195). There is no genuine import of services
  in the data.
- **`is_reverse_charge` is set on bills tagged `business_composition` and
  `deemed_export`** (UC-17), where it cannot apply. RCM-flag hygiene is poor throughout.

---

## 7. Output contract

`rcm_undeclared_liability` (UC-03 §7 shape) with `rule: "rcm_import_of_services"`, plus
`classification_conflict` `data_quality` rows for single-signal cases. The run summary
states how many `overseas`-tagged bills were rejected by step 1, so a quiet result is
not mistaken for "no foreign vendors".

---

## 8. Limits

- Cannot determine a vendor's country directly: `Party` has no country field in the
  fields read. It relies on the signal vote.
- Does not pay or self-invoice the RCM (s.31(3)(f) self-invoice). It reports the
  liability.
- Goods imports (Bill of Entry, customs IGST) are out of scope.

---

## 9. Validation

1. **Live negative control:** 12 `overseas` bills → **0 RCM findings, 12
   `classification_conflict`**. Any RCM finding on live data is a false positive.
2. **Fixture:** a Party with `gst_treatment: overseas`, no GSTIN, bill in USD, SAC
   998314 (IT services), `is_reverse_charge 0` → `rcm_import_undeclared`, IGST 18%.
3. **Pairs with UC-03's validation:** Chakan Transport's GTA bills must be caught by
   UC-03, not UC-21.

---

## 10. Open questions

- **Does `Party` hold a country or address field?** If yes, it replaces the signal vote
  as the primary test. Check `Party.get` on a full record.
- **OIDAR from unregistered-recipient scenarios** — not relevant to a registered
  company, and ignored.
- **Merge with UC-03** as one playbook (assignment.md §4 says to ship them together).
  The only difference is step 1's overseas test.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-21 Import of services RCM`.

**Call 1 — `Bill.list {"gst_treatment":"overseas","limit":1000}`** → 12 bills, all INR:

| Bill | Vendor | `Party.gst_treatment` | RCM | HSN | `grand_total` |
|---|---|---|---|---|---|
| BILL-2026-00101 `08837e85…` | Bosch Rexroth India | business_gst | 1 | 82055900 | ₹4,444.00 |
| BILL-2026-00090 `05ede91a…` | Bosch Rexroth India | business_gst | 1 | 82055900 | ₹79,091.00 |
| BILL-2026-00074 `e7affec3…` | Bharat EV Motors Ltd | business_gst | 1 | — | ₹79,656.17 |
| BILL-2026-00049 `408bf780…` | Shreeji Powder Coating | business_gst | 1 | 82055900 | ₹23,704.00 |
| BILL-2026-00075 `c06bc7df…` | Shreeji Powder Coating | business_gst | 0 | — | ₹77,607.44 |
| BILL-2026-00069 `2cfdecb3…` | Bosch Rexroth India | business_gst | 0 | 84669390 | ₹47,591.00 |
| BILL-2026-00068 `73d0685c…` | Kirloskar Pumps Ltd | business_gst | 0 | 82041100 | ₹50,627.44 |
| BILL-2026-00053 `019164d9…` | Shreeji Powder Coating | business_gst | 0 | — | ₹68,150.94 |
| BILL-2026-00044 `5c9ad0c9…` | Bharat EV Motors Ltd | business_gst | 0 | 73269099 | ₹1,39,617.92 |
| BILL-2026-00039 `79558dca…` | Bosch Rexroth India | business_gst | 0 | 82055900 | ₹11,176.00 |
| BILL-2026-00030 `44bc7ad7…` | Tata Ficosa Automotive Systems | business_gst | 0 | — | ₹14,831.73 |
| BILL-2026-00028 `6fedf88c…` | Bosch Rexroth India | business_gst | 0 | — | ₹32,338.49 |

**The 8 with RCM = 0 are what a naive check would report as undeclared import RCM.**

**Call 2 — `Bill.list {"is_reverse_charge":true,"limit":1000}`** → 8 bills:
BILL-2026-00101, 00095, 00090, 00074, 00072, 00049, 00038, 00022. Sending
`"is_reverse_charge": 1` returns `-32602 "/is_reverse_charge must be boolean"`.

**Call 3 — `Party.list {"limit":1000}`** → `gst_treatment = overseas` on **0** of 195.

**What the live data changed:** 🟢 → 🟡. The spec's one-line check
(`overseas` + RCM false) is only safe if `gst_treatment` is trustworthy, and on this
instance it is not.
