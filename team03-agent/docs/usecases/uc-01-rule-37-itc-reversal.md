# UC-01 — Rule 37: 180-Day Non-Payment ITC Reversal

**Workstream A · Owner: Sudip · Verdict: 🟢 Buildable now**
**Status: draft — first spec written, defines the shared reversal row schema (§7)**

---

## 1. Question

> "Which unpaid bills are about to cost me my input credit, and how much?"

(Verbatim from `spec.md` UC-01, not rephrased.)

---

## 2. Statutory basis

- **Section 16(2), second proviso, CGST Act 2017** — if a recipient fails to pay the
  supplier the invoice value (including tax) **within 180 days** from the date of the
  invoice, an amount equal to the input tax credit already availed on that invoice
  must be added back to output tax liability.
- **Rule 37, CGST Rules 2017** — mechanics of the reversal: reversed in the return for
  the period in which the 180-day window lapses, **along with interest under Section
  50(1) at 18% per annum**, computed from the date ITC was availed to the date of
  reversal.
- **Consequence if missed:** the credit is disallowed, interest accrues at 18% p.a.
  for the full period it went unnoticed, and on assessment the department can levy
  this with penalty — the cost compounds the longer the bill stays unpaid past day
  180.
- **Reinstatement:** once the supplier is subsequently paid, the credit **may be
  re-availed** with no time limit under this rule specifically (unlike the general
  s.16(4) return-filing deadline). This spec covers only the reversal trigger, not
  re-availment tracking — see §10.

---

## 3. Trigger

- **Primary mode: scheduled.** Run daily. The 180-day boundary is a moving date —
  a bill that was compliant yesterday can breach today purely because a day passed,
  with no document event to hang the check on. A scheduled sweep is the only way to
  catch the exact day a bill crosses the line.
- **Secondary mode: on-request.** Any ad-hoc "what's our exposure right now" query
  must run the same computation, not a cached result.
- **Period computed over:** no period window — this is a point-in-time age check
  against **today's date** for every open/unpaid Bill, not a monthly or FY-bounded
  report. (Contrast with UC-08/UC-15, which are period-bounded.)

---

## 4. Input contract

All fields below are confirmed present via `CURRENT_STATUS.md` §3 (real entity model,
verified against live `/api/schemas`) and `spec.md` §4.1 UC-01's data list.

**Tool:** `Bill.list` — paginated, `finance_user` has `read` permission
(`docs/mcp_tool_inventory_india.md` §Bill).

**Filter to apply server-side where the tool supports it, else client-side:**
```
Bill.list(filters={
  "itc_eligibility": ["input", "input_services", "capital_goods"]  # exclude "ineligible" — no credit was taken, nothing to reverse
})
```

**Fields read per Bill record:**
| Field | Type | Purpose |
|---|---|---|
| `id` | string (uuid) | row identity, entity id in output |
| `bill_number` | string | human-readable reference |
| `vendor_id` | string (uuid) | join to `Party` for vendor name |
| `date` | date | invoice date — day 0 of the 180-day clock |
| `balance_due` | decimal | if `0`, bill is fully paid — exclude (§5 step 2) |
| `amount_paid` | decimal | used only to detect partial payment (§10 open question) |
| `itc_eligibility` | enum | must be `input`/`input_services`/`capital_goods` to be in scope |
| `items[]` | array | line items — source of the tax amount, per Hard Rule 1 below |
| `items[].cgst_amount` | decimal | item-level GST component |
| `items[].sgst_amount` | decimal | item-level GST component |
| `items[].igst_amount` | decimal | item-level GST component |
| `items[].cess_amount` | decimal | item-level GST component |

**Join:** `Party.get(id=vendor_id)` for `Party.name`, `Party.gst_no` (needed for the
row's human-readable output, §7).

**Pagination:** page through `Bill.list` at the platform's default/max page size
(confirm actual max against a live call before implementation — not yet measured for
this endpoint specifically) until exhausted; do not assume all bills fit in one page.

---

## 5. Algorithm

1. **Fetch** all `Bill` records with `itc_eligibility != "ineligible"` (page through).
2. **Exclude** any bill where `balance_due == 0` (fully paid — no exposure regardless
   of how long it took).
3. **Compute age:** `age_days = today - Bill.date`.
4. **Filter to breach:** keep bills where `age_days > 180`.
5. **Compute the reversible ITC** for each surviving bill, from item-level fields only
   (Hard Rule, §6):
   ```
   itc_to_reverse = sum(item.cgst_amount + item.sgst_amount
                         + item.igst_amount + item.cess_amount
                         for item in bill.items)
   ```
6. **Compute interest** under s.50(1), 18% p.a., simple interest, from day 181 (the
   day the credit became reversible) to today:
   ```
   interest_days = age_days - 180
   interest = itc_to_reverse * 0.18 * interest_days / 365
   ```
7. **Emit one reversal row per bill** (schema in §7).
8. **Delegate the summation** across all rows (total exposure) to
   `scripts/tax_math.py` per SKILL.md Hard Rule 3 — do not sum in the LLM context
   when the row count exceeds 5.

### Worked example (constructed — no live bill has yet crossed 180 days at spec-writing time; see §9 for why)

> Bill `BILL-2026-00040`, dated `2026-01-15`, vendor "Bosch Rexroth India",
> `balance_due = 50000.00` (unpaid), `itc_eligibility = "input"`.
> Item-level tax on this bill: `cgst_amount = 4500.00`, `sgst_amount = 4500.00`,
> `igst_amount = 0`, `cess_amount = 0`. Evaluated on `2026-09-25` (today):
>
> ```
> age_days       = (2026-09-25) - (2026-01-15) = 253 days
> breach?        = 253 > 180 → yes
> itc_to_reverse = 4500.00 + 4500.00 + 0 + 0 = 9000.00
> interest_days  = 253 - 180 = 73
> interest       = 9000.00 * 0.18 * 73 / 365 = 324.00
> total_exposure = 9000.00 + 324.00 = 9324.00
> ```
>
> Output row: *"BILL-2026-00040 (Bosch Rexroth India) — 253 days unpaid, ₹9,000.00
> ITC must be reversed, ₹324.00 interest accrued, ₹9,324.00 total."*

---

## 6. Known-bad data — what this must NOT trust

- **Document-level `taxes[]` is not trustworthy on this instance** (`CURRENT_STATUS.md`
  §7a). It carries free-text product names instead of tax heads and is arithmetically
  incoherent with the document's own total. **This spec computes tax exclusively from
  `items[].cgst_amount`/`sgst_amount`/`igst_amount`/`cess_amount`** — never from
  `Bill.taxes[]`.
- **`Tax`/`TaxGroup`/`TaxJurisdiction` master and `group_taxes[]`** are not used at
  all by this computation — there is no need to touch them, and §7a/B6 (nested
  `group_taxes[].tax_type` still holds tool names post-fix) confirms they remain
  unsafe.
- **`tds_amount`** is not read by this use case — TDS is UC-09's concern, not this
  one's. Flagging here only that N7 (corrupt `tds_amount` on 9 India bills) is a known
  issue on the same entity, in case a future merge of UC-01 and UC-09 output is
  considered.

---

## 7. Output contract — the shared reversal row schema

This is the schema `assignment.md` §7 designates as shared: **UC-08, UC-15 (Geetha)
and UC-16 (Geetha) must emit rows of this same shape**, since Rule 37, Rule 42/43 and
s.17(5)(h) are all variations on "credit must be reversed."

```json
{
  "finding_type": "itc_reversal",
  "rule": "rule_37_180_day",
  "entity_type": "Bill",
  "entity_id": "<Bill.id>",
  "entity_ref": "<Bill.bill_number>",
  "counterparty_id": "<Party.id>",
  "counterparty_name": "<Party.name>",
  "trigger_date": "<Bill.date>",
  "age_days": 253,
  "reversal_base_amount": 9000.00,
  "interest_amount": 324.00,
  "total_exposure": 9324.00,
  "currency": "INR",
  "computed_at": "2026-09-25T00:00:00Z",
  "status": "finding",
  "summary": "BILL-2026-00040 (Bosch Rexroth India) — 253 days unpaid, ₹9,000.00 ITC must be reversed, ₹324.00 interest, ₹9,324.00 total."
}
```

- **Row schema fields fixed for reuse:** `finding_type`, `entity_type`, `entity_id`,
  `entity_ref`, `counterparty_id`, `counterparty_name`, `reversal_base_amount`,
  `interest_amount`, `total_exposure`, `currency`, `status`, `summary`. Consumers
  (UC-08/UC-15/UC-16) vary `rule` and may add extra fields, but must not rename or
  drop these.
- **Sort order:** descending by `total_exposure` — largest exposure first, since that
  is what a human triaging the list should see first.
- **Finding vs. context:** a row only appears in output if `age_days > 180` (step 4).
  Bills between, say, 150–180 days are **not** emitted as findings by this use case —
  a near-miss warning window is a possible future addition (§10), not in scope now.
- **One-sentence summary a human reads first:** the `summary` field, as shown above.
  The overall response for a run with N findings leads with:
  *"N unpaid bills have crossed 180 days; total ITC exposure ₹X, total interest ₹Y."*
  (X, Y computed via `scripts/tax_math.py`, not summed inline.)

---

## 8. Limits

- **This use case never writes to the ledger.** `JournalEntry` is read-only for
  `finance_user` (`CURRENT_STATUS.md` §3). Output is a report row or an
  `AgentEscalation.create` call — never a posting, never a `Bill.update`.
- **This does not determine whether the reversal has already been filed** in a GST
  return. It reports exposure as of today against the raw ledger; reconciling against
  `GSTReturn` filings is out of scope for this spec.
- **This does not compute or track re-availment** once a flagged bill is later paid —
  see §10.
- **This is not tax advice.** Rates (18% p.a. under s.50(1)) and the 180-day figure
  are current as of this spec's date and must be rechecked against the current
  notification before being relied on for an actual filing decision (`spec.md` §8).

---

## 9. Validation

**No real 180-day-breach case exists yet to test against directly** — as of
2026-09-25, the oldest unpaid India bill sampled during `CURRENT_STATUS.md`
exploration had not yet crossed the threshold (the worked example in §5 is
constructed for this reason, and is explicitly labelled as such per §3's ten-section
rule).

Validation strategy given that constraint:

1. **Hand-computed control case** — the §5 worked example, computed independently by
   hand (not by the agent) using real interest-and-reversal formulas, checked against
   the agent's output once implemented. Mismatch = bug in the implementation, not the
   spec.
2. **Boundary control group** — once implemented, construct three synthetic ages
   against a test bill: 179 days (must NOT appear), 180 days exactly (boundary —
   decide inclusive/exclusive before implementation; this spec treats `> 180` as the
   breach, i.e. day 180 itself is still compliant), and 181 days (must appear). This
   mirrors the control-group method that made bug report B7 credible.
3. **Oracle for the interest formula** — Section 50(1)'s 18% p.a. simple-interest
   formula is fixed by statute, not by a platform endpoint; there is no
   `POST /api/.../interest/compute` equivalent to the tax-compute oracle used in B4.
   Cross-check the formula itself against a second independent source (e.g. a GST
   practitioner reference) before shipping, since there is no platform oracle to
   validate against here.
4. **Re-run against live data periodically** as the ledger ages — some currently-open
   bills will cross 180 days within the capstone's timeline, giving a real case to
   validate against without waiting for one to be seeded.

---

## 10. Open questions

- **Re-availment tracking is not covered.** Once a flagged bill is paid after the
  180-day mark, Section 16(2) allows the credit to be re-availed. This spec detects
  the reversal trigger but does not track "was this previously-reversed credit later
  re-claimed correctly?" — that would need a stateful record of which bills were
  already flagged/reversed, which does not exist yet. Candidate for a UC-01b
  follow-up, not blocking this spec.
- **Partial payment is not addressed.** If `amount_paid > 0` but `balance_due > 0`
  (a partially paid bill), does the 180-day clock apply to the unpaid balance only,
  pro-rata to the ITC on the whole invoice, or does any partial payment reset the
  clock entirely? The statute's text refers to failure to pay "the amount towards the
  value of supply along with tax" — read literally this suggests partial payment does
  not fully cure the exposure on the unpaid portion, but this needs confirmation
  against a CBIC circular before the algorithm in §5 is extended to handle it. Current
  spec computes reversal on the **full item-level tax amount** regardless of partial
  payment, which is the conservative (more-exposure-flagged) reading — worth
  revisiting.
- **180-day boundary inclusivity** (day 180 itself) is stated as "still compliant" in
  §9 point 2, but this is this author's reading of "within 180 days," not a confirmed
  legal citation. Flagging for review rather than asserting confidently.
- **No live breach case exists to validate against yet** (§9) — this spec is
  implementable today, but its first real-data validation will happen later in the
  capstone timeline, not now.
