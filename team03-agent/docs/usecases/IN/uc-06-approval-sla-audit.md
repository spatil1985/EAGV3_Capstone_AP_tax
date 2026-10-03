# UC-06 — Approval SLA and Segregation-of-Duties Audit

**Workstream A · Verdict: 🟢 Buildable (newly unblocked — confirmed live)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Who approved what, was it within policy, and did anyone approve their own bill?"*

(Verbatim from `spec.md` UC-06.)

---

## 2. Statutory basis

Not a tax obligation, but an internal-control one:

- **Companies Act 2013, s.134(5)(e)** — directors of listed companies state that
  internal financial controls are adequate and operating effectively.
  **s.143(3)(i)** — the auditor reports on them.
- **Segregation of duties** is the textbook IFC test for payables: the person who
  raises a bill must not be the person who approves it. `ApprovalPolicy.allow_self_approval`
  is the platform's own expression of that control.

**Consequence if missed:** an IFC deficiency in the audit report. More practically, an
approved-by-self bill is the standard route for internal payment fraud.

---

## 3. Trigger

- **On request** — "show me approval compliance for Q2".
- **Scheduled weekly** — SLA breaches on *open* requests move every hour, but a weekly
  compliance report is the consumable. Live breach alerts are the platform's own job
  (`endpoint.approvals.check_sla`), not ours.
- **Period:** requests with `submitted_at` inside the reporting window. Open requests
  are evaluated against *now*; resolved ones against `resolved_at`.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `ApprovalRequest.list` | `{"limit": 1000}` | **Now in `tools/list`** (F6 fully delivered) |
| `ApprovalLog.list` | `{"limit": 1000}` | 331 rows live |
| `endpoint.approvals.check_sla` | `{"dry_run": true}` | **Oracle for open requests.** ⚠️ Tagged `risk: WRITE`, permission `ApprovalRequest.write`. **`dry_run: true` is mandatory**: without it the call stamps breaches, sends reminders and escalates on a ledger shared with two other teams |
| `ApprovalPolicy.list` | — | ❌ **REST returns 403; no MCP tool.** `allow_self_approval` is therefore unreadable (§10) |

**`ApprovalRequest` fields read** (confirmed on live records): `id`, `number`,
`document_type`, `document_id`, `document_name`, `document_amount`, `status`,
`requested_by`, `requested_by_name`, `current_level`, `total_levels`, `submitted_at`,
`resolved_at`, `sla_deadline`, `is_overdue`, `final_decision`, `steps`, `history`,
`policy_id`.

**`ApprovalLog` fields read:** `request_id`, `action`, `actor_id`, `actor_name`,
`level`, `previous_status`, `new_status`, `timestamp`, `ip_address`.
`action` values seen live: `submitted`, `policy_matched`, `reassigned`, `recalled`,
`sla_breached`, `notification_sent`, `escalated`, `approved`, `rejected`,
`routed_to_default`.

---

## 5. Algorithm

**Part A — SLA, resolved requests (recompute; never trust the stored flag)**
1. Take requests with `status ∈ {approved, rejected, recalled, cancelled}` and both
   `sla_deadline` and `resolved_at` present.
2. Parse both as ISO-8601 (they are: `2026-09-14T18:00:00`, with or without
   microseconds; one value is date-only, `2026-11-05`).
3. `late = resolved_at > sla_deadline`. This is the truth. Compare it with
   `is_overdue` and emit a `data_quality` row for each disagreement.
4. **Sanity gate:** if `resolved_at > now`, the timestamp is impossible. Emit
   `data_quality` and exclude it from the compliance rate.

**Part B — SLA, open requests (use the platform oracle)**
5. Call `check_sla {"dry_run": true}`. Its `breached[].request_id` set is the truth for
   open requests (validated on Keystone for N1: 27/27 exact).
6. Compare with stored `is_overdue=1` among open requests
   (`status ∈ {pending, escalated, in_review}`). Disagreements are `data_quality` rows.

**Part C — segregation of duties**
7. For each `ApprovalLog` row with `action = approved`, look up its request. If
   `log.actor_id == request.requested_by`, emit a **self-approval** finding.
8. For approved `Bill`/`Invoice` requests, check that some `approved` log exists at
   every level from 1 to `total_levels`. A request `approved` with fewer approvals than
   levels skipped a level.

**Part D — report**
9. Compliance rate = on-time resolved / (resolved − excluded), by `document_type`. AP
   documents (`Bill`, `Invoice`, `PurchaseOrder`) are reported first.

### Worked example (real data, 2026-09-28)

> **APR-2026-00025** (`28c170e0-c8d0-4e0b-aa46-18e7df716e5f`), document type `Invoice`,
> status `recalled`.
> `sla_deadline = 2026-10-21T18:00:00`, `resolved_at = 2026-09-12T17:19:15.683726`.
>
> ```
> late       = 2026-09-12 > 2026-10-21 → false  (resolved 39 days early)
> is_overdue = 1                          → stored flag says overdue
> verdict    = false positive — data_quality row; counted ON TIME in the compliance rate
> ```

---

## 6. Known-bad data

- **`is_overdue` is unreliable in both directions** (N1 on Keystone, N8 on India). Never
  read it except to report its own error rate.
- **N8's records have been re-stamped since filing.** On 2026-09-23 APR-2026-00080 had
  `sla_deadline 2025-08-12` (13 months late). On 2026-09-28 the same record reads
  `2026-09-15T18:00:00` (on time). All 14 N8 ids changed the same way. **Store the
  `sla_deadline` you evaluated in every output row**, because the platform may rewrite
  it later.
- **One `resolved_at` is in the future:** APR-2026-00050, `2026-11-05`, evaluated on
  2026-09-28.
- **N5 — `steps[]`/`history[]` hold tool names** (`approver_role: "Angle Plate 945"`).
  Do not derive approvers from `steps[]`; use `ApprovalLog.actor_id` only.
- **Test traffic from other teams** (`requested_by_name: "Team 24"`, request names like
  `TEST-REQ-TEAM24-…`). Exclude requests whose `document_type` is not a real business
  document (`Lead`, `AgentJob`) from the AP compliance figure.

---

## 7. Output contract

```json
{
  "finding_type": "approval_control",
  "rule": "sla_breach | self_approval | level_skipped",
  "entity_type": "ApprovalRequest",
  "entity_id": "28c170e0-c8d0-4e0b-aa46-18e7df716e5f",
  "entity_ref": "APR-2026-00025",
  "document_type": "Invoice",
  "sla_deadline_evaluated": "2026-10-21T18:00:00",
  "resolved_at_evaluated": "2026-09-12T17:19:15.683726",
  "late": false,
  "stored_is_overdue": 1,
  "status": "finding",
  "summary": "APR-2026-00025 (Invoice) resolved 39 days before SLA; platform flags it overdue — counted on time."
}
```

- **Run summary:** *"Resolved: X of Y on time (Z%). Open: N breached per check_sla.
  Self-approvals: S. Platform `is_overdue` disagrees on K requests."*
- **Sort:** self-approvals first (fraud risk), then breaches by hours late, then
  `data_quality` rows.

---

## 8. Limits

- **Never calls `check_sla` without `dry_run: true`.** Never calls
  `endpoint.approvals.process_decision`.
- Cannot evaluate policy compliance (right approver? right amount band?) because
  `ApprovalPolicy` is 403. Reports what *happened*, not whether it matched *policy*.
- Business-hours SLA calendars: `check_sla` reports `deferred_out_of_business_hours`
  (1 live). Part A uses wall-clock time. It may disagree with the platform on requests
  that resolved out of hours.

---

## 9. Validation

1. **Oracle agreement (Part B):** stored-vs-oracle comparison on open requests. Live:
   0 false negatives, 3 false positives. Re-running must reproduce 44 breached for the
   same snapshot.
2. **Hand-check Part A** on the 5 disagreeing resolved requests (§11). Each is a
   two-timestamp comparison a human can verify in seconds.
3. **Self-approval positive control:** none exists live (0 found). Construct one on
   Keystone via `Bill.approval.submit` as the same user who approves. This needs a
   write, so agree it with the team first.

---

## 10. Open questions

- **`allow_self_approval` is unreadable.** Part C treats every self-approval as a
  finding, which is correct if the policy forbids it and noise if it allows it. Ask for
  `ApprovalPolicy` read access. This is the one remaining piece of F6.
- **Does `cancelled`/`recalled` count as "resolved" for SLA purposes?** A recall is the
  requester withdrawing, not an approver deciding. Current spec includes them, matching
  N1/N8. Arguably they should be excluded from the compliance rate.
- **Re-stamped deadlines:** should the agent keep its own history of `sla_deadline`
  values to detect after-the-fact edits? That is a stateful store we do not have.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-06 Approval SLA audit`.

**Call 1 — `ApprovalRequest.list {"limit":1000}`** → 172 requests.
Status: draft 94 · pending 38 · escalated 13 · recalled 11 · approved 6 · in_review 4 ·
cancelled 4 · rejected 2.

Part A result: **19 resolved with both timestamps → 5 disagree with `is_overdue`**
(4 false positive, 1 false negative).

| Request | Type | `sla_deadline` | `resolved_at` | stored | truth |
|---|---|---|---|---|---|
| APR-2026-00058 `e83fa013…` | LeaveApplication | 2026-09-16T18:00 | 2026-09-12T17:19 | 1 | on time |
| APR-2026-00025 `28c170e0…` | **Invoice** | 2026-10-21T18:00 | 2026-09-12T17:19 | 1 | on time |
| APR-2026-00021 `e3631ab8…` | Quotation | 2026-09-14T18:00 | 2026-09-12T17:19 | 1 | on time |
| APR-2026-00018 `ed68ccc0…` | Contract | 2026-09-14T18:00 | 2026-09-12T17:19 | 1 | on time |
| APR-2026-00050 `f0132f05…` | SalesOrder | 2026-10-07T10:15 | **2026-11-05** (future) | 0 | late / impossible |

**Call 2 — `endpoint.approvals.check_sla {"dry_run":true}`**
```json
{"result":{"checked":55,"breached":[{"number":"APR-2026-00033","request_id":"431bc806-fa65-492b-8dc0-80abdfb0f6b7",
  "document_name":"BILL-2026-00004","approver":"Rohan (admin)","hours_overdue":321.7}, "... 43 more ..."],
  "escalated":[],"reminders_sent":[],"deferred_out_of_business_hours":[…1…],"dry_run":true}}
```
Part B: 55 open · stored `is_overdue=1` on **47** · oracle breached **44** → **0 false
negatives, 3 false positives**: APR-2026-00053 (PurchaseOrder, SLA 2026-10-08),
APR-2026-00036 (**Bill**, SLA 2026-11-11), APR-2026-00024 (**Bill**, SLA 2026-11-01).
All three have future deadlines and are flagged overdue anyway.

**Call 3 — `ApprovalLog.list {"limit":1000}`** → 331 rows; 6 `approved`, 0 where
`actor_id == requested_by` → **0 self-approvals**.

**Call 4 — `GET /api/ApprovalPolicy?limit=1`** → **HTTP 403**. Not in `tools/list`.

**What the live data changed:** the N8 pattern (14 false negatives from one bulk
resolve) is gone, because the deadlines were rewritten. The flag is still wrong on 26%
of resolved requests, now mostly in the false-positive direction. The spec's rule
("recompute, never trust") is unchanged. The reason it matters has shifted from
"undercounts breaches" to "overcounts them".
