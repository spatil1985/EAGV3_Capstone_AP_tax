# UC-03 — RCM Self-Invoicing Exposure

**Workstream A · Owner: Sudip · Verdict: 🟢 Buildable**
**Status: draft — pairs with [UC-21](uc-21-import-services-rcm.md); same check, domestic counterparty**

---

## 1. Question

> "Which supplier bills make us liable to pay the tax ourselves, and have we?"

(Verbatim from `spec.md` UC-03, not rephrased.)

---

## 2. Statutory basis

- **Section 9(3), CGST Act 2017** — for specified categories of inward supply, the
  **recipient**, not the supplier, is liable to pay GST under reverse charge. The
  notified categories relevant to a typical manufacturing/services buyer include:
  goods transport agency (GTA) services (Notification 13/2017-CT(R), entry 1),
  legal services from an advocate/firm of advocates (entry 2), services by a
  director to the company (entry 6), sponsorship services (entry 4), and several
  others.
- **Section 9(4), CGST Act 2017** — reverse charge on supply from an **unregistered
  person** to a registered person, for notified classes of supply (historically
  broader, narrowed by later notifications to specific sectors — the agent must
  treat this as a category to check per playbook, not assume blanket applicability).
- **Consequence if missed:** the tax was never charged by the supplier (correctly —
  RCM supplies are typically invoiced without GST by the supplier) and the
  **recipient's liability to self-assess and pay it was simply never discharged**.
  This is not a missing input credit (which is merely lost money); it is an
  **undeclared output-side liability** — the department can demand the tax, plus
  interest under s.50(1) at 18% p.a. from the date it was due, plus potential
  penalty under s.122 for non-payment of self-assessed tax. Because RCM tax paid can
  usually be claimed back as ITC in the same return (subject to eligibility), the
  *net* cash cost of compliance is often small — but the *liability* for not having
  self-invoiced and paid is real and separate from the credit question.
- **This spec covers the identification and self-invoicing/payment gap check only.**
  It does not compute the ITC eligibility of the resulting self-paid tax — that is
  a downstream step covered conceptually by UC-02 (Geetha's blocked-credit audit),
  not duplicated here.

---

## 3. Trigger

- **Primary mode: scheduled.** Run on a periodic sweep (e.g. weekly), since RCM
  applicability spans the whole supplier-type lookup table (§5) rather than hanging
  off a single field change — consistent with `assignment.md` §5a's reasoning for
  UC-02, which this use case structurally resembles (a standing audit sweep, not an
  event hook on one field).
- **Secondary mode: on-request.** Ad-hoc "what's our current RCM exposure."
- **Period computed over:** this is a **standing audit**, not calendar-bound by
  itself — it should be run over **all open, unreconciled bills** (a rolling window,
  e.g. the current and prior GST return period, since RCM liability is discharged
  return-period by return-period) rather than the full historical ledger every time,
  to bound cost. The exact rolling window (one period vs. two) is a judgment call
  flagged in §10.

---

## 4. Input contract

Fields confirmed via `CURRENT_STATUS.md` §3, `spec.md` §4.1 UC-03's data line, and
`mcp_tool_inventory_india.md` (`Bill`, `Party` groups).

**Tools:**
- `Bill.list` — `finance_user` has `read`.
- `Party.get`/`Party.list` — `finance_user` has `read`, for the counterparty-type
  join.

**Fields read per `Bill` record:**
| Field | Type | Purpose | Confirmed |
|---|---|---|---|
| `id`, `bill_number` | uuid, string | row identity | `CURRENT_STATUS.md` §3 |
| `vendor_id` | uuid | join to `Party` | `CURRENT_STATUS.md` §3 |
| `date` | date | period attribution | `CURRENT_STATUS.md` §3 |
| `is_reverse_charge` | boolean | **the flag under audit** — whether the bill was recorded as RCM | `spec.md` §4.1 UC-03; also confirmed in `screen_api_mapping.md` line 111 as a real `Bill` field |
| `items[].hsn_or_sac` | string | SAC-code lookup for the supplier-type mapping (§5) | `spec.md` §1 field-existence table |
| `items[].cgst_amount`, `sgst_amount`, `igst_amount`, `cess_amount` | decimal | tax amount that *should* have been self-assessed, computed item-level per §7a | `CURRENT_STATUS.md` §7a |
| `grand_total` | decimal | fallback context if item-level tax is absent on an RCM bill (common — supplier typically bills with no GST at all under RCM, see §5 step 4) | `CURRENT_STATUS.md` §3 |

**Fields read per `Party` record (the counterparty):**
| Field | Type | Purpose | Confirmed |
|---|---|---|---|
| `id`, `name` | uuid, string | join target, output | `CURRENT_STATUS.md` §3 |
| `contact_type` | `"vendor"` filter | scope to vendors | `CURRENT_STATUS.md` §3 |
| `gst_treatment` | enum: `business_gst`/`business_composition`/`consumer`/`overseas`/`unregistered_business`/`sez`/`deemed_export` | **primary supplier-type signal** — `unregistered_business` is the direct trigger for s.9(4); `overseas` is UC-21's trigger, not this one's | `spec.md` §1; enum confirmed verbatim in `screen_api_mapping.md` lines 183-185 |
| `gst_no` | string or null | corroborates `unregistered_business` (null/absent GSTIN alongside that treatment) | `screen_api_mapping.md` line 60 |

---

## 5. Algorithm

### 5a. The supplier-type → RCM-expected lookup table

This is the piece `assignment.md` §4 says the spec "must nail." It is a **playbook
constant**, not a platform field — nothing in the schema tags a bill as "GTA" or
"legal services" directly. The agent must infer supplier type from a combination of
`items[].hsn_or_sac` (SAC codes for services) and, where SAC is absent or
ambiguous, `Party.name`/vendor classification maintained separately. Stated
plainly: **this lookup table is agent-side logic layered on top of platform data,
not a verified platform capability** — the SAC codes below are standard GST SAC
codes as of this spec's writing and must be rechecked against the current
notification (per `spec.md` §8's disclaimer) before being relied on.

| Supplier type | Notification basis | SAC code (indicative) | RCM expected when |
|---|---|---|---|
| Goods Transport Agency (GTA) | Notif. 13/2017-CT(R) entry 1 | `9965`/`9967` | GTA has not opted to pay forward charge (a per-vendor election the agent cannot see directly — flagged §10) |
| Legal services (advocate/firm of advocates) | Notif. 13/2017-CT(R) entry 2 | `9982` | Always, when supplied by an individual advocate/advocate firm to a business entity |
| Director's sitting fees/services to the company | Notif. 13/2017-CT(R) entry 6 | N/A — not SAC-coded; identified via `Party` tagged as a director-type payee, not a standard vendor | Always |
| Sponsorship services | Notif. 13/2017-CT(R) entry 4 | `9983` (indicative, sponsorship is not always cleanly SAC-isolated) | Always, when recipient is a body corporate/partnership |
| Supply from an **unregistered person** (s.9(4), notified classes) | Notif. 07/2019-CT(R) and successors (real estate promoters primarily; general s.9(4) is largely suspended/narrowed post-2019) | N/A | Only for the specific notified classes still in force — **this spec does not assume blanket s.9(4) applicability**, since the general reverse charge on all unregistered-supplier purchases was deferred/narrowed after 2017. Flag `gst_treatment = unregistered_business` as a **review candidate**, not an automatic RCM-expected finding, pending the specific notified class check |
| Import of services | s.9(3) via IGST Act s.5(3) | N/A | **Out of scope for this spec — see [UC-21](uc-21-import-services-rcm.md)**, which covers the `overseas` counterparty case as its own complete spec |

### 5b. Steps

1. **Fetch** all `Bill` records in the trigger window (§3), page through.
2. **Join** each bill's `vendor_id` to `Party` for `gst_treatment`, `gst_no`, `name`.
3. **Classify supplier type** per the §5a table, using `items[].hsn_or_sac` first,
   falling back to a vendor-tagging convention the agent maintains for
   non-SAC-coded categories (director fees) — **this fallback is not schema-backed
   and must be documented as agent-maintained reference data**, not asserted as a
   platform fact (see §10).
4. **Determine RCM-expected:** `true` if the supplier type matches an "always" row
   in §5a, or a conditional row whose condition is separately confirmed (e.g. GTA
   forward-charge election — not visible in this schema, treated conservatively as
   RCM-expected unless a separate record says otherwise).
5. **Cross-check against `Bill.is_reverse_charge`:**
   - `RCM-expected = true` AND `is_reverse_charge = true` → **compliant**, not a
     finding (context row only, if included at all — see §7).
   - `RCM-expected = true` AND `is_reverse_charge = false` → **finding**: an
     undeclared RCM liability. This is the primary output of this use case.
   - `RCM-expected = false` AND `is_reverse_charge = true` → **finding** (secondary,
     lower severity): RCM flagged where it may not apply — worth a review in case
     of over-compliance/misclassification, though this carries no missed-liability
     cost, only a potential over-claimed-then-reversed-credit question (UC-02's
     territory).
6. **For each undeclared-liability finding, compute the tax that should have been
   self-assessed:**
   ```
   rcm_liability = sum(item.cgst_amount + item.sgst_amount
                        + item.igst_amount + item.cess_amount
                        for item in bill.items)
   ```
   If item-level tax fields are all zero (the common case — a GTA/advocate bill is
   typically invoiced with **no GST charged by the supplier at all**, since RCM
   moves the liability to the recipient), the agent **cannot derive the liability
   amount from the bill's own tax fields** and must instead compute it as
   `applicable_rcm_rate × taxable_value` using a playbook-carried rate table (5%
   GTA, 18% legal/director/sponsorship, standard rates) against `Bill.grand_total`
   or item `taxable_value`, whichever is the untaxed base. **This is the harder,
   more common case in practice** and is flagged explicitly in §10 as needing a
   confirmed base-amount field before implementation.
7. **Emit one finding row per bill** (schema in §7).

### Worked example (constructed — no confirmed live case of an undeclared GTA/legal RCM bill was found during spec-writing; SAC codes and rates are standard as of this writing, not independently re-verified against the current notification per §8's disclaimer)

> Bill `BILL-2026-00312`, vendor "Sri Balaji Road Carriers" (`gst_treatment =
> "unregistered_business"`, no `gst_no`), item `hsn_or_sac = "9965"` (GTA), item
> `cgst_amount = 0`, `sgst_amount = 0`, `igst_amount = 0` (supplier invoiced freight
> with no GST, as expected under RCM), `Bill.is_reverse_charge = false`,
> freight taxable value (from item line total) = ₹40,000.00.
>
> ```
> supplier_type   = GTA (SAC 9965 match)
> rcm_expected    = true (GTA, no evidence of forward-charge election on file)
> is_reverse_charge (actual) = false
> -> FINDING: undeclared RCM liability
> item-level tax on bill = 0 (as expected for a GTA RCM bill)
> rcm_liability (derived, playbook rate 5% GTA, no ITC on GTA RCM at 5% per
>   standard notification terms) = 40,000.00 * 5% = 2,000.00
> ```
>
> Output row: *"BILL-2026-00312 (Sri Balaji Road Carriers, GTA) — RCM expected but
> `is_reverse_charge` is false; estimated undeclared liability ₹2,000.00 (5% on
> ₹40,000.00 freight value, derived from playbook rate — not present on the bill's
> own tax fields)."*

---

## 6. Known-bad data

- **§7a — document-level `taxes[]`, `Tax`/`TaxJurisdiction` master, `group_taxes[]`
  are not trustworthy.** This use case computes any *actually recorded* tax
  exclusively from `items[].cgst_amount`/`sgst_amount`/`igst_amount`/`cess_amount`.
  It does not read `Bill.taxes[]` at all.
- **`Bill.is_reverse_charge` itself is the field under audit, not a known-bad
  field** — but its *absence of corroborating evidence* (no separate RCM-payment
  record, no distinct `JournalEntry` visibility since that's read-only) means this
  spec can only check whether the flag was **set**, not whether the liability was
  actually **paid/self-invoiced and reported** in a `GSTReturn`. See §8 and §10.
- **N7 (`tds_amount` corruption)** is not directly relevant here — this use case
  does not read `tds_amount`. Noted only because the same 9 corrupted bills, if any
  happen to also be RCM-relevant, would carry an untrustworthy `grand_total`, which
  step 6's fallback base-amount calculation depends on when item-level tax is zero.
  Cross-check any RCM finding's `grand_total` against negative-value corruption
  before trusting the derived liability figure.

---

## 7. Output contract

```json
{
  "finding_type": "rcm_undeclared_liability",
  "entity_type": "Bill",
  "entity_id": "<Bill.id>",
  "entity_ref": "<Bill.bill_number>",
  "vendor_id": "<Party.id>",
  "vendor_name": "<Party.name>",
  "vendor_gst_treatment": "unregistered_business",
  "supplier_type_inferred": "gta",
  "supplier_type_basis": "hsn_or_sac=9965",
  "rcm_expected": true,
  "is_reverse_charge_actual": false,
  "recorded_tax_amount": 0.00,
  "derived_liability_amount": 2000.00,
  "derivation_method": "playbook_rate_5pct_on_taxable_value",
  "currency": "INR",
  "computed_at": "2026-09-25T00:00:00Z",
  "status": "finding",
  "summary": "BILL-2026-00312 (Sri Balaji Road Carriers, GTA) — RCM expected but not flagged; ~₹2,000.00 undeclared liability (derived, not recorded on the bill)."
}
```

- **Row schema fields:** `derivation_method` is always present and distinguishes
  `"item_level_tax"` (liability read directly off the bill's own tax fields — high
  confidence) from `"playbook_rate_on_taxable_value"` (estimated — lower
  confidence, must be labelled as such per §5 step 6). This use case's finding is
  conceptually a "liability owed" finding like UC-01's reversal, but is **not**
  wired to the shared reversal row schema ([UC-01 §7](uc-01-rule-37-itc-reversal.md#7-output-contract-the-shared-reversal-row-schema)):
  that schema is for "credit that must be given back" (ITC reversal); this is
  "liability that was never assessed in the first place" — a different finding
  shape (no `interest_amount` concept the same way, since RCM interest only starts
  accruing once the return period's due date passes, which is a separate,
  period-specific computation not attempted here). Keeping the two schemas
  distinct avoids implying RCM exposure is a credit reversal.
- **Sort order:** descending by `derived_liability_amount` (or `recorded_tax_amount`
  when derivation is `item_level_tax`).
- **Finding vs. context:** only rows where `rcm_expected != is_reverse_charge_actual`
  are findings. Compliant bills (flag matches expectation) are not emitted unless a
  "show all checked, including compliant" verbose mode is explicitly requested —
  the default output is findings-only.
- **One-sentence summary:** per-row `summary`, plus overall lead line: *"N bills
  show a supplier-type/RCM-flag mismatch; estimated undeclared liability ₹X (Y
  derived, Z from recorded tax)."*

---

## 8. Limits

- **This use case never writes to the ledger.** `JournalEntry` is read-only for
  `finance_user` — this ends in a report or an escalation, never a posting, never a
  `Bill.update` to set `is_reverse_charge` automatically.
- **This does not verify that the RCM liability, once flagged, was actually paid or
  self-invoiced.** It checks the `is_reverse_charge` flag's consistency with
  supplier type — it cannot see whether cash was remitted or a self-invoice
  document was raised, since neither is a field this spec reads (no self-invoice
  entity was found in the schema during research; flagged in §10).
- **The supplier-type lookup table (§5a) is agent-maintained playbook logic, not a
  verified platform capability**, and depends on SAC-code presence and a non-SAC
  vendor-tagging convention (director fees) that is not schema-backed. A vendor
  missing a SAC code or untagged as a director-fee payee will silently fall through
  this check — a false negative this spec cannot detect on its own.
- **This is not tax advice.** Notification numbers, SAC codes and rates cited in
  §5a are current as of this spec's writing and must be reconfirmed against the
  live notification before being relied on for a filing decision, per `spec.md` §8.
- **This does not compute or claim the ITC eligibility of RCM tax once paid** — that
  is UC-02's domain (Geetha, blocked-credit audit), referenced but not duplicated
  here.

---

## 9. Validation

**No confirmed live case of an undeclared GTA/legal/director/sponsorship RCM bill
was found during spec-writing** — the worked example in §5 is explicitly constructed
for this reason.

1. **Hand-computed control case** — the §5 worked example, independently verified
   against the 5% GTA rate and the standard SAC code, same method as UC-01 §9.
2. **Control group by supplier type** — construct four synthetic bills, identical
   in every field except `items[].hsn_or_sac` (one each: GTA `9965`, legal `9982`,
   sponsorship `9983`, and a plain taxable-goods HSN code as the negative control).
   Verify only the first three are flagged `rcm_expected: true` and the fourth is
   not — this isolates the lookup table's per-code branching, the same
   "identical-except-one-variable" method that made bug report B7 credible.
3. **Live cross-check against `Bill.is_reverse_charge = true` bills that already
   exist** — sample any currently-flagged RCM bills on Suryodaya (if any exist) and
   confirm their `hsn_or_sac`/vendor pattern matches an expected RCM category, as a
   sanity check that the lookup table's direction is right (a bill correctly
   flagged `is_reverse_charge=true` should match one of the §5a rows) — this is a
   plausibility check, not a substitute for point 2's controlled test.
4. **Genuinely untested:** whether `Bill.is_reverse_charge` is ever set `true` on
   Suryodaya at all (i.e. whether any RCM bill currently exists to check against)
   was not confirmed during spec-writing — this should be checked before
   implementation, since a zero-RCM-bill dataset would mean this check has never
   been exercised against real data.

---

## 10. Open questions

- **No self-invoice or RCM-payment-tracking entity was found in the schema search**
  behind this spec. Section 31(3)(f) requires the recipient to raise a self-invoice
  for RCM supplies from unregistered persons — whether the platform models this
  anywhere (perhaps as a specially-flagged `Invoice` with `direction=payable`?) is
  unconfirmed and should be checked before claiming this use case can verify
  "and have we [discharged the liability]," which is literally half of the
  question this UC is meant to answer (§1). As specified, this use case can only
  answer the *identification* half with confidence.
- **GTA forward-charge election is not visible in this schema.** A GTA can elect to
  pay tax under forward charge instead of RCM (Notification 13/2017-CT(R) proviso);
  this spec conservatively treats all GTA bills as RCM-expected unless
  `is_reverse_charge` is already `true`, which will produce false positives for any
  GTA vendor who has validly elected forward charge. No field was found to record
  that election — needs either a platform gap flag or an agent-maintained
  vendor-level override list.
- **The non-SAC-coded categories (director fees) rely on a vendor-tagging
  convention this spec assumes exists but does not itself define** — how would the
  agent actually distinguish "Party is a director receiving sitting fees" from any
  other individual payee, given no `Party.role` value for "director" was confirmed
  during this spec's research? This needs a concrete answer before implementation,
  not just a table row.
- **Step 6's fallback liability derivation (playbook rate × taxable value) assumes
  a usable taxable-value base is readable from item lines even when tax fields are
  zero** — this needs confirming against a live bill sample (does `items[]` still
  carry a `rate`/`quantity`/line total when `cgst_amount` etc. are zero, or does the
  whole tax block go empty together?) before the derivation in §5 step 6 can be
  implemented as written.
