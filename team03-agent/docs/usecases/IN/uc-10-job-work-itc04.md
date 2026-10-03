# UC-10 — Job Work Movement and ITC-04

**Workstream C · Verdict: 🔴 Blocked (spec.md) → 🟡 Partial (live data)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Backs:** F19 / GAP-2 — **the live data contradicts F19's filed premise; see §11**

---

## 1. Question

> *"What have we sent out for job work that hasn't come back, and when does it become
> a taxable supply?"*

(Verbatim from `spec.md` UC-10.)

---

## 2. Statutory basis

- **Section 143, CGST Act** — a principal may send inputs or capital goods to a job
  worker without payment of tax, provided they are brought back:
  - **inputs within 1 year**, **capital goods within 3 years** of being sent
    (extendable by the Commissioner by 1 year / 2 years);
  - moulds, dies, jigs and fixtures are exempt from the time limit.
- **s.143(3)/(4)** — goods not returned in time are **deemed supplied by the principal
  on the day they were sent out**. Tax is payable with interest from that original date.
- **Rule 45, CGST Rules** — goods move under a delivery challan. Reporting is in **Form
  ITC-04**: half-yearly for aggregate turnover above ₹5 crore, annually otherwise.
- **Consequence if missed:** tax on the full value of unreturned goods, back-dated to
  despatch, with s.50 interest, even though no sale ever happened.

---

## 3. Trigger

- **Scheduled monthly:** age every open job-work challan. The clock is time-driven,
  like UC-01.
- **Pre-ITC-04:** before each ITC-04 period closes (30 Sep / 31 Mar for half-yearly).
- **Period:** point-in-time age against today, per challan.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `DeliveryChallan.list` | `{"challan_type": "job_work", "limit": 1000}` | ✅ **`job_work` is a live enum value** — 19 challans |
| `DeliveryChallan.get` | `{"id": …}` | line detail |
| `Item.get` | `{"id": item_id}` | goods vs capital goods (1-year vs 3-year clock) — **no field distinguishes them** (§10) |
| `TaxExemption.list` | — | Row *"Job-work movement — not a supply"* (`6c8fbb73-d817-430f-9cb1-f999db6cad4f`, `associated_with: item`) |

**DeliveryChallan fields** (all of them, from a live record): `id`, `number`,
`customer_id`, `sales_order_id`, `challan_number`, `reference_number`, `date`,
`challan_type` (`job_work | supply_on_approval | supply_of_liquid_gas | others`),
`place_of_supply`, `gst_no`, `items`, `taxes`, `notes`, `status`
(`draft | delivered`), `net_total`, `total_tax`, `grand_total`.

**What is not there:** no `returned_qty`, no `return_date`, no link from a return
document back to the outbound challan, no `job_worker_id` distinct from `customer_id`,
no inputs-vs-capital-goods marker.

---

## 5. Algorithm

1. Fetch `challan_type = job_work` challans with `status = delivered`. A `draft` challan
   has not moved goods and the clock has not started.
2. For each, `age_days = today − date`.
3. **Clock:** 365 days (inputs) by default. 1,095 days if every line's item is
   flagged capital goods (no such flag exists — §10).
4. **Returned?** No return linkage exists. Best-effort proxy: an inbound `Bill` or
   `DeliveryChallan` from the same party, after the outbound date, with the same
   `item_id`. It is recorded as `return_inferred`, never `return_confirmed`.
5. Emit `job_work_deemed_supply` when `age_days > limit` and not returned, and
   `job_work_due_soon` in the last 60 days.
6. **Deemed-supply tax** (for the report only): `line taxable value × item rate`, via
   `POST /api/accounting/tax/compute`, plus s.50 interest from `date` to today (UC-01
   formula).

### Worked example (real challan, projected date)

> **DC-2026-00084** (`1d2fa370-aa94-4fe6-a1be-0834ab59234e`), `challan_type: job_work`,
> dated **2026-08-04**, `grand_total ₹1,853.21`, `status: draft`.
>
> ```
> status = draft → goods not despatched → clock NOT started → no finding today
> if it were delivered on 2026-08-04:
>   inputs deadline          = 2027-08-04
>   age today (2026-09-28)   = 55 days → compliant, 310 days remaining
> ```
>
> Output (today): nothing for this challan. Run summary: *"19 job-work challans, all
> draft — no goods currently out with job workers."*

---

## 6. Known-bad data

- **All 19 job-work challans are `draft`.** On this instance nothing has actually gone
  out, so the use case correctly returns zero findings. Do not treat "draft" as "sent".
- **Challan `notes` are seed text** (*"SG iron casting: order 108 at Solapur. Accepted
  on concession."*), and line `_item_id_display` is blank on some challans.
- **`customer_id` is the only counterparty field.** For job work, the "customer" is the
  job worker. That is semantically wrong but usable.

---

## 7. Output contract

```json
{
  "finding_type": "job_work",
  "rule": "s143_deemed_supply | s143_due_soon",
  "entity_type": "DeliveryChallan",
  "entity_id": "…",
  "entity_ref": "DC-2026-00084",
  "counterparty_id": "…",
  "counterparty_name": "Supriya Rathi",
  "sent_date": "2026-08-04",
  "deadline": "2027-08-04",
  "age_days": 55,
  "goods_class": "inputs_assumed",
  "return_state": "none_found | return_inferred",
  "deemed_supply_value": 1853.21,
  "status": "finding",
  "summary": "…"
}
```

---

## 8. Limits

- Cannot confirm a return. The platform has no return linkage, so "returned" is always
  inferred. This is the real remaining gap.
- Cannot tell inputs from capital goods. It defaults to the 1-year clock, which is
  conservative (it flags earlier).
- Does not file ITC-04. It produces the list ITC-04 would need.

---

## 9. Validation

1. **Live negative control:** 19 draft challans → 0 findings. Any output today is a bug.
2. **Boundary fixture:** a delivered challan dated today − 366 → `deemed_supply`;
   today − 364 → `due_soon`; today − 200 → nothing.
3. **Enum check:** `DeliveryChallan.list {"challan_type":"job_work"}` must return 19
   (verified live). A wrong enum value errors with `-32602`.

---

## 10. Open questions

- **Rewrite F19.** Filed text says *"DeliveryChallan … has no job-work subtype"*. It
  does. The accurate gap is: **no return tracking, no job-worker identity, no
  inputs/capital-goods marker.** Update the filing before triage reads it.
- **Capital-goods marker:** `Bill.itc_eligibility = capital_goods` exists on *purchases*
  (9 bills). Can an item's capital-goods status be inferred from how it was bought? That
  is fragile but possible.
- **Moulds/dies exemption** from the time limit needs an item-level flag that does not
  exist.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-10 Job work ITC-04`.

**Call 1 — `DeliveryChallan.list {"limit":1000}`** → 100 challans.
`challan_type`: others 40 · supply_on_approval 21 · supply_of_liquid_gas 20 ·
**job_work 19**. `status`: draft 88 · delivered 12.

**Call 2 — `DeliveryChallan.list {"challan_type":"job_work","limit":1000}`** → 19
challans, dated 2026-08-04 … 2026-09-10, **all `draft`**. Samples:

| Challan | Date | Notes (seed) |
|---|---|---|
| DC-2026-00084 `1d2fa370…` | 2026-08-04 | — |
| DC-2026-00078 `94739328…` | 2026-09-10 | — |
| DC-2026-00039 `1e7f8f2f…` | 2026-09-08 | "SG iron casting: order 108 at Solapur. Accepted on concession." |
| DC-2026-00074 `468c2002…` | 2026-09-05 | "Pipe Wrench: lot 907 at Satara. Accepted on concession." |

**Call 3 — `TaxExemption.list`** → includes *"Job-work movement — not a supply"*
(`6c8fbb73…`, `associated_with: item`). The platform models the tax *treatment* of job
work. It does not model the *return*.

**What the live data changed:** `spec.md`'s verdict was 🔴 because *"no `job_work`
concept anywhere in the 468 tools or the schema."* A `job_work` enum value exists and is
in use. The use case is 🟡: outbound tracking works today; return tracking is the gap.
