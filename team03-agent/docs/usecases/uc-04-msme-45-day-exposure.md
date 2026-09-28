# UC-04 — MSME 45-Day Exposure

**Workstream A · Owner: Sudip · Verdict: 🟢 Buildable now**
**Status: draft**

---

## 1. Question

> "Which small suppliers are we about to pay late, and what will it cost us?"

(Verbatim from `spec.md` UC-04, not rephrased.)

---

## 2. Statutory basis

*Constants used here are tracked centrally in
[`statutory_constants.md`](../../playbooks/statutory_constants.md#rule-msme-45d)
(RULE-MSME-45D) and
[...#rate-msme-penal](../../playbooks/statutory_constants.md#rate-msme-penal)
(RATE-MSME-PENAL) — edit rates/thresholds there, not here.*

Two independent statutes bite on the same fact pattern — a late payment to an MSME
supplier — and both must be reported, since neither substitutes for the other:

- **MSMED Act 2006, s.15/16** — a buyer must pay a registered micro or small
  enterprise within the agreed period, capped at **45 days** from acceptance of
  goods/services (s.15). Failing that, **s.16** imposes **compound penal interest
  at three times the RBI-notified bank rate**, compounding monthly, running from the
  day after the 45-day window lapses until actual payment.
- **Income Tax Act 1961, s.43B(h)** (inserted by Finance Act 2023, effective FY
  2023-24 onward) — any sum payable to a micro or small enterprise under MSMED s.15
  is deductible **only in the year it is actually paid**, if payment falls outside
  the agreed/45-day period; otherwise the expense is **disallowed** in the year it
  was otherwise deductible on accrual and pushed to the year of actual payment.
- **Consequence if missed:** (a) penal interest at 3× RBI bank rate, compounding
  monthly, accruing daily from day 46 until payment — not a one-time penalty, it
  grows every day the bill stays open; **and** (b) the entire bill amount is
  disallowed as a deduction for that year, i.e. added back to taxable income,
  increasing the tax bill for that year regardless of whether the vendor is ever
  paid. `agentswitch_submissions.md` F8 gives the illustrative shape: a ₹10,00,000
  bill unpaid past 45 days costs penal interest **and** loses deductibility for that
  return.
- **s.43B(h) applies only to micro and small enterprises** (`Party.msme_type` ∈
  `micro`/`small`), **not medium** — medium enterprises are covered by MSMED s.15/16
  penal interest but not the s.43B(h) tax disallowance. This distinction must be
  carried in the algorithm (§5), not collapsed into a single "is_msme" check.

---

## 3. Trigger

- **Primary mode: scheduled.** Run daily. Like UC-01, the 45-day boundary is a
  moving date with no document event to hang the check on — a bill can cross from
  compliant to breached purely because a day passed.
- **Secondary mode: on-request.** Ad-hoc "what's our MSME exposure right now."
- **Period computed over:** no calendar period — a point-in-time age check against
  **today's date** for every open (`balance_due > 0`) `Bill` from an MSME vendor.
  The **RBI bank rate** used in the interest calculation is a rate that changes
  periodically (see §5, §10) — it is *not* itself period-bound in the sense of a
  monthly/annual report, but it must be refreshed from a current source, not
  hardcoded indefinitely.

---

## 4. Input contract

Fields confirmed via `CURRENT_STATUS.md` §3, `spec.md` §4.1 UC-04's data line, and
`agentswitch_submissions.md` F8 (which independently verifies the same fields while
arguing the gap case).

**Tools:**
- `Party.list(filters={"is_msme": true})` — `finance_user` has `read`
  (`mcp_tool_inventory_india.md` §Party; confirmed field presence in
  `agentswitch_submissions.md` F8 point 1 and `screen_api_mapping.md` line 404).
- `Bill.list(filters={"vendor_id": [...msme vendor ids...]})` — `finance_user` has
  `read`.

**Fields read per `Party` record:**
| Field | Type | Purpose | Confirmed |
|---|---|---|---|
| `id` | uuid | join key to `Bill.vendor_id` | `CURRENT_STATUS.md` §3 |
| `name` | string | vendor name for output | `CURRENT_STATUS.md` §3 |
| `is_msme` | boolean | scope filter — only MSME vendors are in scope | F8 point 1 |
| `msme_type` | enum `micro`/`small`/`medium` | drives whether s.43B(h) applies (micro/small only) | F8 point 1 |
| `msme_no` | string | Udyam registration number, included in output for audit trail | F8 point 1 |

**Fields read per `Bill` record:**
| Field | Type | Purpose | Confirmed |
|---|---|---|---|
| `id`, `bill_number` | uuid, string | row identity | `CURRENT_STATUS.md` §3 |
| `vendor_id` | uuid | join to `Party` | `CURRENT_STATUS.md` §3 |
| `date` | date | acceptance-date proxy — see §5 step 1 caveat | `spec.md` §4.1 UC-04 |
| `due_date` | date | agreed payment date, if earlier than the 45-day statutory cap | `spec.md` §4.1 UC-04; confirmed as a real, usable field in `screen_api_mapping.md` line 32 |
| `balance_due` | decimal | if `0`, bill is fully paid — excluded | `spec.md` §4.1 UC-04 |
| `grand_total` | decimal | base for the s.43B(h) disallowance amount and, cautiously, the interest base (see §6 on N7) | `CURRENT_STATUS.md` §3 |

**Pagination:** page through both `Party.list` and `Bill.list` at max page size.

---

## 5. Algorithm

1. **Fetch** all `Party` records where `is_msme == true` (page through). Build a set
   of MSME `vendor_id`s, tagged with `msme_type`.
2. **Fetch** all `Bill` records where `vendor_id` is in that set (page through).
3. **Exclude** any bill where `balance_due == 0` (fully paid — no live exposure).
4. **Determine the payment-window start date.** The MSMED Act's 45-day clock runs
   from **acceptance of goods/services**, which this spec approximates as
   `Bill.date` (the bill/invoice date) in the absence of a distinct
   goods-acceptance-date field on `Bill` — flagged as an approximation, not a
   confirmed statutory equivalence, in §10.
5. **Determine the applicable deadline:** `deadline = min(Bill.date + 45 days,
   Bill.due_date)` if `Bill.due_date` is populated and earlier than the 45-day cap
   (the agreed period cannot exceed 45 days under s.15); otherwise
   `deadline = Bill.date + 45 days`.
6. **Compute age and breach:**
   ```
   age_days = today - Bill.date
   breach?  = today > deadline
   ```
7. **For breaching bills, compute penal interest** under MSMED s.16 — compound
   interest at **3× the RBI-notified bank rate**, compounding monthly, from the day
   after `deadline` to today:
   ```
   overdue_days   = today - deadline
   monthly_periods = overdue_days / 30  (whole months elapsed, per compounding convention — see §10 for the exact day-count convention question)
   penal_rate_annual = 3 * rbi_bank_rate   # rbi_bank_rate is a playbook constant, refreshed periodically — see §10
   penal_interest = balance_due * ((1 + penal_rate_annual/12) ** monthly_periods - 1)
   ```
8. **For breaching bills where `msme_type` is `micro` or `small`** (not `medium`),
   flag the **s.43B(h) disallowance**: the full `grand_total` of the bill is
   disallowed as a deduction in the year it would otherwise have accrued, unless
   paid within the year. This spec reports the disallowance amount; it does not
   determine which tax year's return is affected (that requires the company's own
   filing calendar, out of scope here).
9. **Emit one exposure row per breaching bill** (schema in §7).
10. **Delegate aggregation** (total penal interest, total disallowance exposure) to
    `scripts/tax_math.py` per SKILL.md Hard Rule 3 when row count exceeds 5.

### Worked example (constructed — deliberately distinct from `agentswitch_submissions.md` F8's own illustrative ₹10,00,000/60-day example, to avoid implying that figure was pulled from live data; F8's example is itself stated as illustrative, not observed)

> Bill `BILL-2026-00077`, vendor "Sharma Precision Components" (`is_msme = true`,
> `msme_type = "small"`), dated `2026-06-01`, `due_date = null` (no separate agreed
> date), `balance_due = 300,000.00`, `grand_total = 300,000.00`. Evaluated on
> `2026-09-25` (today). Assume a playbook constant `rbi_bank_rate = 6.50%` p.a.
> (illustrative — must be refreshed from an actual RBI notification before use, see
> §10):
>
> ```
> deadline        = 2026-06-01 + 45 days = 2026-07-16
> age_days        = (2026-09-25) - (2026-06-01) = 116 days
> breach?         = today (Sep 25) > deadline (Jul 16) -> yes
> overdue_days    = (2026-09-25) - (2026-07-16) = 71 days
> monthly_periods = 71 / 30 = 2 (whole months, floor convention)
> penal_rate_annual = 3 * 6.50% = 19.50%
> penal_interest  = 300000 * ((1 + 0.1950/12)^2 - 1) = 300000 * 0.032701... ≈ 9,810.35
> s.43B(h) disallowance (msme_type=small, in scope): grand_total = 300,000.00 disallowed
>   for the year, unless paid before year-end.
> ```
>
> Output row: *"BILL-2026-00077 (Sharma Precision Components) — 71 days past the
> 45-day MSME deadline, ₹9,810.35 penal interest accrued (3× RBI rate, compounding
> monthly), ₹3,00,000.00 at risk of s.43B(h) disallowance if unpaid by year-end."*

---

## 6. Known-bad data

- **N7 — `tds_amount` corrupt on 9 India bills, driving negative `grand_total`.**
  This use case reads `grand_total` (step 8, and as the interest base in step 7 via
  `balance_due`) — if a bill is one of the N7-affected nine, its `grand_total` is
  negative and arithmetically meaningless. This spec does not attempt to repair the
  figure; it flags affected bills separately (`data_quality_flag: "n7_tds_corruption"`
  in the output row, §7) rather than computing a penal-interest or disallowance
  figure against a corrupted base. **Cross-check:** if `grand_total < 0` for an
  MSME-vendor bill, suppress the numeric interest/disallowance fields and emit the
  row as a data-quality escalation instead of a normal finding.
- **§7a — document-level `taxes[]` is not read by this use case.** No item-level tax
  computation is needed here (the exposure is on `grand_total`/`balance_due`, not on
  GST components), so §7a's item-level-only rule does not constrain this
  calculation directly — noted for completeness only.
- **N6 — recurring-bill scheduler duplicates.** If an MSME vendor's bill is one of
  the N6-generated duplicates, this use case would currently report the *same*
  penal-interest exposure multiple times (once per duplicate bill), inflating the
  apparent total. This spec does not itself de-duplicate against N6 — that is
  UC-05's job. Recommend running UC-05 first and excluding any bill flagged there as
  `finding_type: "recurring_scheduler_defect"` before running this use case's
  aggregation step, or clearly labelling the overlap in the combined report.

---

## 7. Output contract

```json
{
  "finding_type": "msme_45_day_exposure",
  "entity_type": "Bill",
  "entity_id": "<Bill.id>",
  "entity_ref": "<Bill.bill_number>",
  "vendor_id": "<Party.id>",
  "vendor_name": "<Party.name>",
  "vendor_msme_no": "<Party.msme_no>",
  "msme_type": "small",
  "trigger_date": "2026-06-01",
  "deadline": "2026-07-16",
  "overdue_days": 71,
  "penal_interest_amount": 9810.35,
  "s43b_h_applicable": true,
  "s43b_h_disallowance_amount": 300000.00,
  "currency": "INR",
  "data_quality_flag": null,
  "computed_at": "2026-09-25T00:00:00Z",
  "status": "finding",
  "summary": "BILL-2026-00077 (Sharma Precision Components) — 71 days past the 45-day MSME deadline, ₹9,810.35 penal interest, ₹3,00,000.00 at risk of s.43B(h) disallowance."
}
```

- **Row schema fields:** `s43b_h_applicable` is `false` when `msme_type == "medium"`
  — the row is still emitted (penal interest still applies under MSMED s.16 for
  medium enterprises too, per s.15's scope), but
  `s43b_h_disallowance_amount` is `null` in that case, not zero, to distinguish
  "not applicable" from "applicable but computed as zero."
- **Sort order:** descending by `penal_interest_amount + coalesce(s43b_h_disallowance_amount, 0)`
  — the combined statutory cost, since that is the single number a human triaging
  the list most needs first.
- **Finding vs. context:** a row is a finding only if `today > deadline` (step 6).
  Bills approaching but not yet past the deadline (e.g. day 40) are **not** emitted
  as findings — an early-warning window (e.g. day 35+) is a candidate future
  addition, not in scope now (contrast UC-01's identical design choice).
- **One-sentence summary:** the `summary` field per row, plus an overall lead line:
  *"N MSME bills have crossed the 45-day deadline; total penal interest ₹X, total
  s.43B(h) disallowance exposure ₹Y."* (X, Y via `scripts/tax_math.py`.)

---

## 8. Limits

- **This use case never writes to the ledger.** `JournalEntry` is read-only for
  `finance_user` — output is a report or an `AgentEscalation.create` call, never a
  posting.
- **This does not determine which tax year's return is affected by an s.43B(h)
  disallowance** — that requires the company's filing calendar and accrual
  treatment, which is out of scope. The spec reports the *amount at risk*, not the
  return line it lands on.
- **This does not verify the vendor's MSME registration is current/valid** — it
  trusts `Party.is_msme`/`msme_no` as stored. Udyam registration validity/expiry is
  not modelled anywhere in the schema found so far (no `MSMEPreferences` field for
  the *vendor's* registration expiry — only the company's own, per
  `agentswitch_submissions.md` F8 point 3).
- **The RBI bank rate is a playbook constant that must be refreshed periodically,
  not hardcoded once and forgotten** — see §10.
- **This is not tax advice.** The 45-day figure, the 3× RBI rate mechanism, and
  s.43B(h)'s scope are current as of this spec's date and must be rechecked against
  the current notification/circular before being relied on for a filing decision.

---

## 9. Validation

1. **Hand-computed control case** — the §5 worked example, independently computed
   by hand using the compound-interest formula and cross-checked against the
   implementation's output.
2. **Boundary control group** — synthetic bills at 44 days (must NOT appear), 45
   days exactly (boundary — this spec treats day 45 itself as still compliant,
   i.e. breach is `> 45`, mirroring UC-01's `> 180` convention; **not independently
   confirmed against a CBIC/MSME circular**, flagged in §10), and 46 days (must
   appear).
3. **`msme_type` branch control** — three synthetic bills identical except
   `msme_type` (`micro`, `small`, `medium`), all past deadline: verify the `medium`
   case correctly emits `s43b_h_applicable: false` and a null disallowance amount
   while still carrying a non-zero `penal_interest_amount` — this is the specific
   "identical except one variable" method that made bug report B7 credible, applied
   here to a statute-branching condition rather than a data bug.
4. **No live breach case confirmed as of spec-writing time.** Unlike UC-01 (where no
   bill had yet crossed 180 days), this spec has **not been checked against live
   `Party.is_msme` + `Bill` data** to see whether any MSME vendor bill on Suryodaya
   is currently past 45 days — that check should be run before/alongside
   implementation, since (unlike the 180-day Rule 37 case) 45 days is a much shorter
   window and a real breach is plausible in the existing 101-bill dataset. This is
   the single most valuable pre-implementation check for this spec.
5. **RBI bank rate sourcing is genuinely untested** — there is no platform field or
   endpoint that supplies the current RBI bank rate; it must come from an external,
   periodically-refreshed playbook constant (§10), and no oracle exists within this
   platform to validate that constant's currency.

---

## 10. Open questions

- **Acceptance date vs. `Bill.date`.** The MSMED Act's 45-day clock runs from
  acceptance of goods/services (or deemed acceptance, 15 days after delivery if the
  buyer raises no objection), not necessarily the invoice date. This spec uses
  `Bill.date` as a proxy since no distinct goods-acceptance-date field exists on
  `Bill`. This is a simplification that could understate or overstate the true
  deadline depending on how far apart delivery and invoicing are in practice —
  needs a decision on whether a separate acceptance-date field should be requested
  as a platform gap, or whether `Bill.date` is an acceptable proxy for this agent's
  purposes.
- **Day-count/compounding convention for the penal interest (step 7) is this
  author's construction** (`floor(overdue_days / 30)` whole months), not a cited
  MSMED s.16 circular. MSMED s.16 says "compound interest with monthly rests"; the
  exact rounding/day-count convention (30-day months vs. actual calendar months,
  floor vs. partial-month proration) needs confirmation against an authoritative
  reading before this figure is relied on.
- **The RBI bank rate itself is not sourced anywhere in this spec or the platform.**
  It must live as a playbook constant per `assignment.md` §7's "statutory constants
  table," refreshed on whatever cadence RBI updates it — this spec does not define
  that refresh mechanism, only assumes the constant exists and is current.
- **45-day boundary inclusivity** (day 45 itself) is asserted as "still compliant"
  by analogy to UC-01's day-180 convention, not independently confirmed against an
  MSMED circular — flagged for review, not asserted confidently.
- **Interaction with N6 duplicate bills** (§6) is named but not resolved — this spec
  assumes UC-05 runs first and its output is available to gate against; the exact
  sequencing/data-sharing mechanism between the two use cases is not specified here.
