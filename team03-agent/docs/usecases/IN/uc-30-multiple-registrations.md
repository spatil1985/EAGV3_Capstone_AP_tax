# UC-30 — Multiple GST Registrations (Distinct Persons): Branch Transfers and ISD

**Domains: manufacturing, retail (multi-state); any vertical with offices in more than one state · Category: input and output tax · Verdict: 🟡 Partial — registration data checks run live and fail; transfer and ISD checks are blocked (documents don't record the receiving GSTIN)**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"We're registered in several states. Are our branches dealing with each other the way GST requires?"*

---

## 2. Statutory basis

- **s.25(2) and s.25(4)–(5) CGST Act**: a business needs a registration in every state it supplies from.
  Each registration (GSTIN) is a **distinct person**, and all of them share the company's PAN (s.25(6)).
- **Schedule I para 2**: supplies between distinct persons are taxable **even without consideration**. A
  stock transfer from Maharashtra to the Gujarat stock point needs a tax invoice with IGST.
  - Value under **Rule 28**: open-market value, or 90% of the price to unrelated buyers.
  - *Second proviso (caveat):* where the receiving branch can take full credit, the invoice value is deemed
    to be open-market value.
- **Input Service Distributor (ISD)**: *our understanding, Finance Act 2024 amending s.2(61) and s.20,
  caveat:* **mandatory from 1 April 2025** for common input services invoiced to one GSTIN but used by
  others. Credit must be distributed through ISD, not kept by the GSTIN the bill was addressed to.
- **Consequence:**
  - an untaxed branch transfer is unpaid tax for the sender, and lost credit for the receiver;
  - credit kept at head office instead of being distributed can be denied to the branch that used the
    service.

---

## 3. Trigger

- **Scheduled monthly**, before GSTR-1/3B, for transfers and ISD distribution.
- **On event:** `location.created` / `location.updated`, which triggers the registration data checks;
  `delivery_challan.created` between own locations.
- **On request.**

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Location.list` | `name`, `state`, `state_code`, `gstin`, `is_primary`, `address` |
| `OrgProfile.list` | `gstin`, `pan`, `state` |
| `Invoice.list` | `place_of_supply`, `source_of_supply`, `warehouse_id`, `party_id` |
| `DeliveryChallan.list` | `challan_type`, movements between own locations (UC-10 lists the types) |
| `Bill.list` | `destination_of_supply`, `place_of_supply`: the receiving registration, which is **mostly null** |

---

## 5. Algorithm

1. **Registration consistency** (runs today):
   - `registration_pan_mismatch`: characters 3–12 of a location's GSTIN ≠ `OrgProfile.pan`.
   - `registration_state_mismatch`: the GSTIN's first two digits ≠ the location's state code.
   - `primary_gstin_mismatch`: the primary location's GSTIN ≠ `OrgProfile.gstin`.
   - `location_state_code_invalid`: the state code isn't a 2-digit GST state code.
   - `location_without_gstin` in a state with no registration but outward supplies from it.
2. **Branch transfers** (blocked): a challan or invoice whose consignee is another own GSTIN → must carry
   IGST at Rule 28 value. This needs `source_of_supply` / `warehouse_id` → location mapping.
3. **Supplies from the wrong registration** (blocked): goods despatched from the Gujarat stock point to a
   Gujarat buyer are an **intra-state supply by the Gujarat GSTIN**, not an inter-state one from
   Maharashtra. This needs the despatch location on the invoice.
4. **ISD** (blocked): common services (rent, audit, software, advertising) billed to one GSTIN while other
   GSTINs exist → `isd_distribution_required`. This needs the receiving GSTIN on each bill.

### Worked example (REAL, 2026-10-04)

> The company's own registration: `OrgProfile.gstin 27AASCS7781M1ZQ`, PAN **AASCS7781M**.
>
> | Location | State code | GSTIN | PAN in GSTIN | Finding |
> |---|---|---|---|---|
> | Chakan Plant (primary) | 27 | 27AACCS4471P1ZK | AACCS4471P | `primary_gstin_mismatch`, `registration_pan_mismatch` |
> | Bhosari Warehouse | 27 | 27AACCS4471P1ZK | AACCS4471P | `registration_pan_mismatch` |
> | Bengaluru Sales Office | 29 | 29AACCS4471P1ZB | AACCS4471P | `registration_pan_mismatch` |
> | Sanand Forward Stock Point | 24 | 24AACCS4471P1ZG | AACCS4471P | `registration_pan_mismatch` |
> | Branch — Ahmednagad | `FS3772/4032` | 09AWZPQ2663H8ZH | AWZPQ2663H | PAN mismatch; GSTIN state 09 (Uttar Pradesh) for a Maharashtra town; invalid state code |
> | Branch — Solapur | `MS1298/4033` | — | — | `location_state_code_invalid` |
>
> 52 invoices have place of supply Gujarat (24) and 18 Karnataka (29), both states where a branch GSTIN
> exists. Whether any were despatched from those branches can't be told from the data.
>
> Output: *"None of the 5 branch GSTINs belongs to the company's PAN, and the primary location's GSTIN
> differs from the company profile. Branch transfer and ISD checks can't run until documents record which
> registration they belong to."*

---

## 6. Known-bad data

- **Location GSTINs carry other PANs.** Under s.25(6) every registration must share the company's PAN, so
  either the company profile or the locations are wrong. This is a candidate bug report, and the location
  rows look seeded (`state_code` values like `MS1298/4033`).
- `Bill.destination_of_supply` / `place_of_supply` are null on most bills, so the receiving registration is
  unknown.

---

## 7. Output contract

`finding_type: "registration"`, `rule ∈ {registration_pan_mismatch, registration_state_mismatch,
primary_gstin_mismatch, location_state_code_invalid, branch_transfer_untaxed, supplied_from_wrong_gstin,
isd_distribution_required}`. `entity_type: "Location"` for data rules, the document type for transfer and
ISD rules.

---

## 8. Limits

- Never creates registrations, ISD invoices or cross-charges.
- **Consolidation is not supported** (`not_yet_supported.consolidation`), so each GSTIN's returns can't be
  produced separately. Per-GSTIN UC-23/UC-26 output is blocked until it is.

---

## 9. Validation

1. **Live:** recompute the GSTIN-PAN comparison for all 6 locations.
2. **Fixtures:**
   - GSTIN `27AASCS7781M1ZQ` vs PAN `AASCS7781M` → no finding;
   - GSTIN `29AACCS4471P1ZB` → `registration_pan_mismatch`.
3. **State fixture:** GSTIN prefix `09` on a location in Maharashtra (27) → `registration_state_mismatch`.

---

## 10. Open questions

- Is `Invoice.warehouse_id` → `Warehouse` → `Location` a reliable despatch-location path? If so, steps 2–3
  become buildable.
- Does the platform intend one GSTIN per company (single-registration model) with locations as addresses
  only? If so, the location GSTINs shouldn't exist.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Location.list` → 6 rows:
  - Chakan Plant `0c9bd019-9a45-466c-83a6-0589aaf5fdea` (primary);
  - Bhosari Warehouse `b994abf3-1f8f-42b6-95a7-62fc380c0297`;
  - Bengaluru Sales Office `3eb899cf-9855-447f-9c4c-cbe18f9ddd98`;
  - Sanand Forward Stock Point `305d8e44-d182-4f56-8a12-2923cd9c3c59`;
  - Branch — Ahmednagad `179051f0-0290-4ba2-b594-4f3f3f31e88a`;
  - Branch — Solapur `acdc307c-fbfa-490a-8b7d-cf11c41bd59a`.
- `OrgProfile.list` → `gstin 27AASCS7781M1ZQ`, `pan AASCS7781M`, `state Maharashtra`.
- `Invoice.list` → place of supply on live receivable invoices: 27 ×177, 24 ×52, 29 ×18, 23 ×3.
