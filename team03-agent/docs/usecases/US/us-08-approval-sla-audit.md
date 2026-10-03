# US-08 — Approval SLA & Segregation-of-Duties Audit (US instance of UC-06)

**US · Proposed owner: Sudip · Verdict: 🟢 Buildable — regime-agnostic; 0 findings on live data**
**IN spec (algorithm, output contract):** [`../IN/uc-06-approval-sla-audit.md`](../IN/uc-06-approval-sla-audit.md) · **live evidence 2026-10-03**

---

Identical check in both jurisdictions (`tax_regimes: [all]`). Sections 1, 3, 4, 5 and
7 are as UC-06. US-specific notes and evidence only.

## 2. Statutory basis (US)

Internal control over financial reporting: SOX §404 for issuers. Segregation of
duties in purchasing and payables is a standard key control. Replaces UC-06's
Companies Act citations.

## 6. Known-bad data (US)

- **N1 (filed against this tenant) appears fixed.** It reported 8 of 93 resolved
  requests with a wrong `is_overdue`. On 2026-10-03: **0 of 93**. The same records now
  carry correct flags: APR-2026-00121, resolved 7 days late, now reads `is_overdue 1`;
  APR-2026-00107, resolved a day early, now reads `is_overdue 0`. The timestamps are
  unchanged from the filing, so this is a fix, not a re-stamp (contrast N8 on India).
- Keep UC-06's "recompute, never trust the stored flag" rule anyway. It is now the
  regression guard.
- `ApprovalPolicy` is still unreadable for `finance_user` (`../../submissions/requested_tools.md`
  T2.1), so self-approvals cannot be judged against policy.

## 9. Validation (US)

1. Resolved: 0/93 mismatches.
2. Open: `endpoint.approvals.check_sla {"dry_run": true}` → 30 checked, 27 breached;
   stored `is_overdue = 1` on exactly the same 27. FN 0, FP 0.
3. 203 `approved` log entries, **0** where the actor is the requester.

## 10. Open questions (US)

- Tell triage N1 looks fixed? Recommend a comment on the N1 card with the two record
  ids above.
- 24 requests are `escalated`: report escalation depth (`escalation_count`) as context?

## 11. Live evidence — actual calls, 2026-10-03

- `ApprovalRequest.list {"limit":1000}` → 123: approved 73, escalated 24, rejected 14,
  recalled 6, pending 5, in_review 1.
- `ApprovalLog.list {"limit":1000}` → 602 entries.
- `endpoint.approvals.check_sla {"dry_run": true}` → `checked: 30`, 27 breached.
