# UC-44 — Approval Threshold Splitting (Bills Broken Up to Avoid Sign-Off)

**Domains: all five · Category: AP control · Verdict: 🟡 Partial — candidates found live; the approval threshold can't be read (`ApprovalPolicy` returns 403), so it comes from config**
**Status: draft · live evidence 2026-10-04 · US counterpart: [US-20](../US/us-20-approval-threshold-splitting.md) · companion to [UC-06](uc-06-approval-sla-audit.md)**

---

## 1. Question

> *"Is anyone splitting purchases into smaller bills so each one stays under the approval limit?"*

---

## 2. Basis

- **Control, not tax statute.** Splitting a purchase to stay below an approval threshold defeats the
  segregation-of-duties control that [UC-06](uc-06-approval-sla-audit.md) audits. It is a standard
  procurement-fraud indicator.
- **India:** the statutory auditor reports on the adequacy and operating effectiveness of **internal
  financial controls** over financial reporting (Companies Act 2013, s.143(3)(i)). Approval controls are
  part of that.
- **Tax tie-in:** split bills also hide cumulative thresholds, such as TDS 194C's single-bill
  vs aggregate limit ([UC-09](uc-09-vendor-tds-verification.md)) and 194Q's ₹50 lakh ([UC-13](uc-13-194q-206c-thresholds.md)).
  The splitting pattern is worth checking against those too.

---

## 3. Trigger

- **On event:** `bill.created` when the same vendor already has a bill dated within the window.
- **Scheduled weekly** sweep.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `Bill.list` | `vendor_id`, `date`, `grand_total`, `approval_status` (`not_required\|pending_approval\|approved\|rejected`), `purchase_order_id`, `created_by`, `created_at` |
| `PurchaseOrder.list` | `vendor_id`, `date`, `grand_total`, `approval_status`: splitting can happen at PO level too |
| `ApprovalRequest.list` | `document_type`, `document_amount`, `policy_id`, `final_decision`: used to **infer** policy bands |
| `ApprovalPolicy.list` | **403 for `finance_user`.** Thresholds unreadable |
| `config/overrides/approval_thresholds.yaml` | The threshold(s) per document type, maintained by finance |

---

## 5. Algorithm

1. **Threshold:** from overrides. If none is set, **infer** one: group `ApprovalRequest` by `policy_id`, and
   take the edge between the highest amount under one policy and the lowest under the next. Report
   `threshold_source: inferred`.
2. **Window groups:** bills (and POs) of the same vendor with dates within *W* days (rulebook, default 3),
   not void.
3. **`split_candidate`:** every document in the group is below the threshold, their sum is at or above
   it, and none went through approval. Strength rises when:
   - amounts are similar or identical;
   - the same `created_by` entered them;
   - they were entered within minutes of each other (`created_at`);
   - there's no PO or a single PO.
4. **Exclusions:**
   - recurring standing orders (`recurring_bill_id` set, or a known schedule as in US-07);
   - documents already flagged as duplicates by UC-05, which are reported there instead.
5. **`policy_unreadable`:** a context row stating that `ApprovalPolicy` returned 403, so the threshold is
   assumed.

### Worked example (REAL, 2026-10-04; threshold assumed ₹1,00,000 from config)

> 15 same-vendor-same-day groups (82 bills, mostly the seed day 2026-09-12). Two groups meet the test:
>
> | Vendor | Date | Bills | Sum | Note |
> |---|---|---|---|---|
> | Suvarna Electricals | 2026-09-12 | ₹40,120 · ₹36,108 · ₹40,120 · ₹36,108 | ₹1,52,456 | Two identical pairs, also a UC-05 duplicate pattern |
> | Chakan Transport Lines | 2026-09-12 | ₹36,344 · ₹29,736 · ₹33,040 · ₹59,472 | ₹1,58,592 | GTA bills already in UC-03 |
>
> 13 bill approval requests on India each use a **different** policy id, so no band can be inferred, and
> the threshold must come from config. Bills awaiting approval: 21, from ₹13,169 to ₹9,26,276.
>
> Output: *"Two vendors received four bills each on 12 September, every bill under ₹1 lakh but together
> over it, and none was approved. Check whether these were one purchase. (Threshold assumed: the
> approval policy can't be read.)"*

---

## 6. Known-bad data

- `ApprovalPolicy` is **403** for our role (UC-06), so the real limits are unknown.
- The seed day (2026-09-12) concentrates bills artificially. Same-day grouping overstates splitting on
  this tenant, and a strength score (step 3) prevents a flood.

---

## 7. Output contract

`finding_type: "approval_control"`, `rule ∈ {split_candidate, policy_unreadable}`. Fields: `vendor_id`,
`window`, `documents[]`, `sum`, `threshold`, `threshold_source` (`config\|inferred`), `strength`
(`low/medium/high`, with the reasons).

---

## 8. Limits

- Never rejects, recalls or re-routes an approval (`endpoint.approvals.process_decision` is never
  allowlisted).
- A candidate is not a finding of fraud. The output says "check whether these were one purchase."

---

## 9. Validation

1. **Live:** the two groups above, with threshold ₹1,00,000.
2. **Fixtures:**
   - three bills of ₹40,000 on the same day with threshold ₹1,00,000 → candidate;
   - the same three with `recurring_bill_id` set → excluded.
3. **Inference fixture:** policy A approves ≤ 10,000, policy B ≥ 10,626 → inferred edge 10,000.

---

## 10. Open questions

- Ask for read access to `ApprovalPolicy` (UC-06 already needs it; F6 was delivered except this entity).
- Should PO-level splitting share this playbook? Recommend yes: same logic, document type as a parameter.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Bill.list` → same-vendor-same-day groups: 15 (82 bills).
  - Shreeji Powder Coating 12 bills, Bharat EV Motors 12 bills, Bosch Rexroth 11 bills: all on
    2026-09-12, several individually above ₹1 lakh, so not split candidates.
- `ApprovalRequest.list` → 177 (Bill 13, PurchaseOrder 13, …). Bill requests each have a distinct
  `policy_id`, with amounts ₹0 to ₹5,23,436.
- `ApprovalPolicy.list` → 403 (UC-06 §11).
