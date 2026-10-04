# US-20 — Approval Threshold Splitting (US instance of UC-44)

**US · Domains: all five · Verdict: 🟢 Buildable — threshold inferable from live approvals; 0 split candidates**
**IN spec (algorithm, output contract):** [`../IN/uc-44-approval-threshold-splitting.md`](../IN/uc-44-approval-threshold-splitting.md) · **live evidence 2026-10-04**

---

Regime-agnostic. Sections 1, 2, 3, 5 and 7 are as UC-44. On Keystone the threshold can be **inferred**
from approval history (UC-44 step 1), which India can't do.

## 4. Input contract (US differences)

`ApprovalRequest` for bills uses **two policies**. Their amount bands give the threshold:

| Policy | Bill approvals | Amounts |
|---|---|---|
| `ba8184c2-9181-480e-9e1f-6813766b694f` | 35 | ≈ $3,075 … **$10,000** |
| `a99c548b-41cd-4340-bd25-34b3da9ff2e1` | 10 | ≈ **$10,626** … $16,739 |

→ inferred edge **$10,000**, `threshold_source: inferred`. Config overrides it once finance confirms.

## 6. Known-bad data (US)

- **Standing orders recur fortnightly in identical groups.** Apex Metals Supply has the same four bills
  ($3,288.20, $3,437.94, $10,626.36, $16,739.38) on 2026-01-10, 01-26, 02-11, 02-27, 03-15, 03-31, 04-16
  and 05-02, each bill on its own PO (4 distinct POs per day). US-07 suppresses them as standing orders,
  and UC-44 step 4 excludes them.
- `ApprovalPolicy` is still unreadable, so the edge is inferred, not read.

## 9. Validation (US)

1. **Live:** 9 same-vendor-same-day groups (36 bills).
   - 8 are Apex Metals fortnightly standing orders. In each, the bills below $10,000 sum to $6,726.14,
     which is below the threshold.
   - The 9th (2026-10-01: four drafts of $53–$210) is recurring-template output (US-07 §6).
   → **0 split candidates**, the correct result.
2. **Fixture:** three bills of $4,000 to one vendor on one day, with no PO and no approval → candidate at
   the inferred $10,000 edge.

## 10. Open questions (US)

- Confirm with the Keystone operators that $10,000 is the policy edge. The inference rests on 45
  approvals; one exception would move it.

## 11. Live evidence — actual calls, 2026-10-04

- `ApprovalRequest.list` → 123 (PurchaseOrder 54, Bill 45, Contract 13, Invoice 8, …).
- `Bill.list` → same-vendor-same-day groups: 9, all Apex Metals Supply LLC.
  - 8 standing-order days, 2026-01-10 … 2026-05-02: 6 paid, 2 open.
  - 1 draft group on 2026-10-01.
  - Bills pending approval: $3,288, $3,438, $6,750, $6,854, $10,000, $16,739.
