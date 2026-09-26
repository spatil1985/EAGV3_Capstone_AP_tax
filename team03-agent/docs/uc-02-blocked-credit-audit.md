# UC-02 — Blocked Credit (s.17(5)) Audit

**Workstream B · Owner: Geetha · Verdict: 🟢 Buildable now**
**Status: draft — defines the HSN-prefix → blocked-category mapping table that UC-16 reuses**

---

## 1. Question

> "Have we claimed credit on anything the law blocks?"

(Verbatim from `spec.md` UC-02, not rephrased.)

---

## 2. Statutory basis

- **Section 17(5), CGST Act 2017** — input tax credit is **blocked** (not
  available, regardless of otherwise being used in the course of business) on a
  specific enumerated list, including (the categories this spec targets):
  - **17(5)(a)/(aa)** — motor vehicles for transport of persons (seating capacity
    ≤13 including driver) and their general insurance/servicing, **unless** used
    for further supply of such vehicles, transport of passengers, or driving
    training.
  - **17(5)(b)** — food and beverages, outdoor catering, beauty treatment, health
    services, cosmetic/plastic surgery, membership of a club/health/fitness centre,
    **unless** the same category of supply is used to make a further outward
    taxable supply of the same category, or is obligatory for an employer under any
    law.
  - **17(5)(c)/(d)** — works contract services for construction of an immovable
    property (other than plant and machinery), and goods/services received for
    construction of an immovable property on own account, even when used in the
    course of business.
  - **17(5)(h)** — goods **lost, stolen, destroyed, written off, or disposed of by
    way of gift or free samples**. (This paragraph is UC-16's specific concern —
    drug expiry write-offs — and is cross-referenced there; this spec's mapping
    table includes it for completeness of the blocked-category list but UC-16 owns
    the worked mechanics for the expiry case specifically.)
- **Consequence:** credit claimed against a blocked category is not merely
  disallowed prospectively — it was **never available**. On assessment it is
  recovered with interest under s.50(3) and is liable to penalty under s.74 if the
  claim is found to involve suppression or wilful misstatement; even in the
  ordinary case it is recovered with interest as an incorrectly availed credit.
- **This is an engineering specification, not tax advice** (`spec.md` §8) — the
  exceptions within each blocked category (e.g. "unless used for further supply,"
  "unless obligatory under law") are fact-specific and this spec's HSN-prefix
  mapping is a **first-pass flag for human review**, not a final determination of
  blocked status.

---

## 3. Trigger

- **Primary mode: scheduled.** Per `assignment.md` §5a: run as a **periodic sweep
  (e.g. weekly)** — a wrongly-claimed credit sits undetected until someone looks;
  there is no single document event to hang the check on, since the check spans
  the *whole* blocked-category table against the *whole* bill population, not a
  reaction to one field changing on one record. This is different in kind from
  UC-07/UC-14's event-triggered mode: there, one new invoice fully determines one
  new classification; here, a bill written last month is just as findable as one
  written today, so a standing audit sweep is the right shape, not an event
  listener.
- **Secondary mode: on-request** — same baseline as every use case in this
  workstream.
- **Period computed over:** no period window — like UC-01, this is a point-in-time
  sweep over **all currently-open bills with claimed ITC**, not a monthly/FY-bounded
  report. Every sweep re-examines the full population (or an incremental slice
  since the last sweep, an implementation choice — see §10).

---

## 4. Input contract

Fields confirmed via `spec.md` §4.1 UC-02's data list and `spec.md` §1 (platform
capability table), cross-checked against `CURRENT_STATUS.md` §3/§4.

**Tool:** `Bill.list` — paginated, `finance_user` has read access.

**Filter to apply:**
```
Bill.list(filters={
  "itc_eligibility": ["input", "input_services", "capital_goods"]  # exclude "ineligible" — those bills already correctly declare no credit was taken, nothing to flag
})
```

**Fields read per Bill record:**
| Field | Type | Purpose |
|---|---|---|
| `id` | string (uuid) | row identity |
| `bill_number` | string | human-readable reference |
| `vendor_id` | string (uuid) | join to `Party` for vendor name |
| `date` | date | context for the finding |
| `itc_eligibility` | enum `input \| input_services \| capital_goods \| ineligible` | must **not** be `ineligible` to be in scope — a bill already marked ineligible is not a finding here, it is the correct outcome |
| `items[]` | array | line items — source of both the HSN classification and the tax amount |
| `items[].cgst_amount`, `sgst_amount`, `igst_amount`, `cess_amount` | decimal | item-level GST components — the amount at risk if the category is genuinely blocked |

**Fields read per line item, joined to `Item`:**
| Field | Type | Purpose |
|---|---|---|
| `Item.hsn_or_sac` | string | primary signal — matched against the blocked-category HSN-prefix table below |
| `Item.category_id` | string/uuid | secondary signal, where populated, for categories HSN alone under-determines (e.g. "club membership" is a service category, not reliably HSN-coded across item masters) |

**The HSN-prefix → blocked-category mapping table** (agent-side logic, per
`spec.md` §4.1 UC-02's verdict — "HSN-prefix → blocked-category mapping is agent-side
logic," not a platform field):

| Blocked category (s.17(5) para) | HSN/SAC prefix pattern (illustrative — to be refined against a real chart of HSN codes before implementation) | Notes |
|---|---|---|
| Motor vehicles ≤13 seats — (a)/(aa) | HSN 8703 (motor cars/other motor vehicles for transport of persons) | Exception: item description/category indicating "for further supply," passenger transport fleet, or driving-school use should suppress the flag — needs a secondary signal beyond HSN alone (§10) |
| Food & beverage, outdoor catering — (b) | HSN Chapter 21 (food prep), SAC 9963 (catering services) | Exception: obligatory-under-law (e.g. statutory canteen for >250 employees under Factories Act) should suppress — same caveat |
| Club/health/fitness membership — (b) | SAC 9996 (recreational/cultural/sporting services), category keyword match ("club," "membership," "gym") | HSN/SAC alone likely insufficient; category/description keyword match needed |
| Works contract / immovable property construction — (c)/(d) | SAC 9954 (construction services), category keyword match ("civil work," "construction," "renovation") | Exception: "plant and machinery" carve-out requires distinguishing structural construction from machinery installation — not reliably HSN-determinable, flagged for human review rather than auto-excluded |
| Goods lost/written off/destroyed/gifted — (h) | Not HSN-determinable at all — this category is identified by the **transaction context** (a write-off/loss event), not the item's HSN code. UC-02's table lists it for completeness; **UC-16 owns the actual detection mechanism** for the written-off-stock case (drug expiry), which does not run off this table's HSN-matching logic | See UC-16 |

**No field used here is invented.** `Bill.itc_eligibility`, `Item.hsn_or_sac`,
`Item.category_id`, `items[]` are all confirmed in `spec.md` §4.1/§1.

---

## 5. Algorithm

1. **Fetch** all `Bill` records with `itc_eligibility != "ineligible"` (page
   through) — same starting filter as UC-01 §5 step 1, for the same reason (a bill
   already marked ineligible is not this use case's concern).
2. **For each bill, for each line item**, resolve `Item.hsn_or_sac` and
   `Item.category_id` via the join in §4.
3. **Match each line against the blocked-category table** (§4). A line matches if
   its HSN/SAC prefix or category keyword falls within one of the table's patterns.
4. **Apply the known exceptions where determinable from available fields** (§4's
   "Notes" column) — e.g. suppress the motor-vehicle flag if `Item.category_id` or
   description indicates fleet-for-hire/driving-school use. Where the exception
   test is not reliably determinable from available fields (works contract vs.
   plant-and-machinery, club membership's "obligatory under law" test), **do not
   auto-suppress** — emit the flag with a note that the exception test requires
   human judgment (§8).
5. **For each surviving matched line**, compute the credit at risk from item-level
   fields only (Hard Rule, §6):
   ```
   itc_at_risk = item.cgst_amount + item.sgst_amount + item.igst_amount + item.cess_amount
   ```
6. **Emit one finding row per matched line** (schema in §7), grouped by bill for
   the summary.
7. **Delegate summation** across all rows to `scripts/tax_math.py` (or its
   equivalent), not summed in LLM context for more than a handful of rows, per
   UC-01 §5 step 8's precedent.

### Worked example (constructed — illustrative pattern; not yet run against a matched live case, see §9)

> Bill `BILL-2026-00087`, vendor "Metro Hospitality Services", dated `2026-08-10`,
> `itc_eligibility = "input"`. Line items:
> - "Business Lunch — Client Meeting", HSN/SAC matches Chapter 21/SAC 9963 (food &
>   beverage/catering), `cgst_amount = 900.00`, `sgst_amount = 900.00`.
> - "Conference Room Hire", SAC 9963 not matched to a blocked category (venue hire
>   is not itself a s.17(5) category absent a catering/club element).
>
> ```
> Line 1 match: food & beverage — (b) — no obligatory-under-law exception applies
>               (this is a client entertainment lunch, not a statutory canteen)
> itc_at_risk = 900.00 + 900.00 + 0 + 0 = 1,800.00
> ```
> Output row: *"BILL-2026-00087 (Metro Hospitality Services) — line 'Business Lunch
> — Client Meeting' claims ₹1,800.00 ITC on food & beverage, blocked under
> s.17(5)(b) unless an exception applies. Flagged for review."*
>
> **This example is constructed for illustration of the mechanism** — it is not
> drawn from a specific bill observed on Suryodaya, though Suryodaya (a real
> manufacturing tenant) is exactly the kind of company where this pattern (client
> entertainment claimed as input credit) plausibly occurs and should be checked
> against real bills once the HSN-prefix table (§4) is finalized. Unlike UC-07/
> UC-14/UC-08/UC-15, this use case's mechanism **can** be validated against live
> Suryodaya data (§9) — the "constructed" label here is about this specific example,
> not about the whole use case being untestable.

---

## 6. Known-bad data

- **Universal rule applies** (`CURRENT_STATUS.md` §7a): tax amounts computed from
  item-level `cgst_amount`/`sgst_amount`/`igst_amount`/`cess_amount` only.
  Document-level `taxes[]`, the `Tax`/`TaxJurisdiction` master and `group_taxes`
  are not trustworthy on this instance and are not read by this spec.
- **No further known-bad-data caveat specific to this use case.** `Bill.
  itc_eligibility`, `Item.hsn_or_sac`, `Item.category_id` are not among the
  defects catalogued in `CURRENT_STATUS.md` §7/§9 (N7 `tds_amount`, N128
  `CreditNote.taxes[]`, N126/N127 `Tax`/`TaxJurisdiction`, N1/N8 `is_overdue`) —
  none touch the fields this spec reads. This is stated as an honest "no caveat
  beyond the universal rule," not omitted.

---

## 7. Output contract

**This is a genuine "credit should not have been claimed" finding — arguably a
reversal candidate — but it is distinct from UC-01/UC-16's reversal row schema in
one respect: UC-02 flags a *suspected* blocked category for human confirmation
(the exception tests in §5 step 4 are often not fully determinable from available
fields), whereas UC-01/UC-16 compute a reversal amount with high confidence given
the statute's mechanical trigger (an age threshold, a written-off quantity).** For
this reason, UC-02 emits its own row shape rather than the UC-01 §7 schema — but the
fields are chosen to be a straightforward upgrade path to that schema (same
`entity_type`/`entity_id`/`counterparty` naming) if a future revision decides
audit-confirmed UC-02 findings should convert into reversal rows.

**Row schema:**
```json
{
  "finding_type": "blocked_credit_suspected",
  "rule": "section_17_5",
  "blocked_category": "food_beverage_catering | motor_vehicle | club_membership | works_contract_immovable_property | goods_written_off",
  "entity_type": "Bill",
  "entity_id": "<Bill.id>",
  "entity_ref": "<Bill.bill_number>",
  "counterparty_id": "<Party.id>",
  "counterparty_name": "<Party.name>",
  "line_item_id": "<Item.id>",
  "line_item_name": "<Item.name>",
  "hsn_or_sac": "<Item.hsn_or_sac>",
  "itc_at_risk": 1800.00,
  "currency": "INR",
  "exception_test_required": true,
  "exception_test_note": "Client entertainment lunch — check whether an obligatory-under-law or further-outward-supply exception applies before confirming reversal.",
  "computed_at": "2026-09-26T00:00:00Z",
  "status": "finding",
  "summary": "BILL-2026-00087 (Metro Hospitality Services) — ₹1,800.00 ITC claimed on food & beverage, blocked under s.17(5)(b) unless an exception applies."
}
```

- **Sort order:** descending by `itc_at_risk` — largest suspected exposure first,
  same reasoning as UC-01 §7.
- **Finding vs. context:** every matched line (§5 step 3-4 survivor) is a finding —
  there is no "context-only" row in this use case's output, since the whole point
  of the sweep is to surface candidates for human confirmation. A line that does
  not match the blocked-category table is simply not emitted at all (not a
  "context" row either) — this keeps output focused on what needs review.
- **One-sentence summary:** *"N bills carry claimed ITC on suspected blocked
  categories; total ITC at risk ₹X across [category breakdown]."*
  (X computed via `scripts/tax_math.py`-equivalent aggregation.)

---

## 8. Limits

- **Never writes to the ledger.** `JournalEntry` is read-only for `finance_user` —
  output is a report row or an `AgentEscalation.create` call, never a `Bill.update`
  or a posting.
- **Does not itself determine whether an exception applies.** Where §5 step 4
  cannot reliably auto-suppress a flag (works-contract vs. plant-and-machinery,
  club membership's "obligatory under law" test, motor-vehicle further-supply
  exception), this use case surfaces the flag with `exception_test_required: true`
  and a human must confirm — it does not assert a final blocked-credit
  determination on its own.
- **The HSN-prefix mapping table (§4) is illustrative and needs refinement**
  against a real, complete HSN code list before production use — HSN prefixes
  given here are representative of the right category, not verified against an
  authoritative HSN master (no such master is confirmed present in the schema;
  `spec.md` §4.5 UC-18 notes the same gap for rate-slab checking).
- **This is not tax advice** (`spec.md` §8) — every blocked-category test and its
  exceptions must be rechecked against the current text of s.17(5) and any CBIC
  clarifying circulars before a flagged line is actually reversed.

---

## 9. Validation

Unlike UC-07/UC-14/UC-08/UC-15, **this use case's mechanism is testable against
live data today** — Suryodaya is a real, populated manufacturing tenant, and s.17(5)
blocked categories (motor vehicles, food & beverage, works contract) are generic
enough to plausibly appear in any company's bills, not specific to an exempt-supply
vertical.

1. **Live-data dry run** — run the §5 algorithm against Suryodaya's real `Bill`
   population once the HSN-prefix table (§4) is finalized, and manually review
   every flagged line for a genuine s.17(5) match vs. a false positive from an
   over-broad HSN prefix. This is the primary validation path and does **not**
   require a school/clinic tenant, unlike every other spec in this workstream.
2. **Hand-computed control case** — the §5 worked example, computed independently
   by hand, checked against the agent's output once implemented (same method as
   UC-01 §9 point 1).
3. **Known-negative control** — confirm bills already marked
   `itc_eligibility = "ineligible"` are correctly excluded (§5 step 1), and confirm
   a bill with no blocked-category line at all produces zero findings, not a false
   positive.
4. **Currently untested, honestly stated:** the exception-suppression logic in §5
   step 4 (fleet/driving-school carve-out, obligatory-under-law carve-out) has not
   been exercised against any real item description, since it depends on
   `Item.category_id`/description conventions this workstream has not yet observed
   in bulk on Suryodaya's real item catalogue.

---

## 10. Open questions

- **The HSN-prefix table (§4) is a first draft**, built from statutory category
  descriptions rather than a verified, complete HSN code list — it needs a pass
  against Suryodaya's actual `Item.hsn_or_sac` population to check coverage and
  false-positive rate before being trusted at the prefix-matching level.
- **How to auto-suppress the works-contract/plant-and-machinery exception** is
  unresolved — this is the one exception in the table with no clear secondary
  field to test against (unlike motor vehicles, where a category/description
  keyword plausibly helps). May simply need to stay a permanent
  `exception_test_required: true` case referred to a human.
- **Incremental vs. full sweep** (§3) — whether each scheduled run re-examines the
  entire open-bill population or only bills changed since the last run is an
  implementation choice not resolved here; a full sweep is simpler and safer
  (catches a late `itc_eligibility` correction on an old bill) but more expensive
  at scale. Given Suryodaya's current volume (101 bills, `CURRENT_STATUS.md` §6),
  a full sweep is almost certainly fine for now; this is flagged for reconsideration
  only if bill volume grows substantially.
- **Whether goods lost/written off — (h) — belongs in this spec's table at all**,
  given that UC-16 owns the actual detection mechanism for it (§4) — this spec
  keeps it in the table only for completeness of the s.17(5) category list;
  whether that is confusing or helpful for a reader implementing both UC-02 and
  UC-16 together is worth a second opinion in review.
