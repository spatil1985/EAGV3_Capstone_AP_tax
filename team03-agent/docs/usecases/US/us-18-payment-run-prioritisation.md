# US-18 — Payment Run Prioritisation (US instance of UC-42)

**US · Domains: all five · Verdict: 🟢 Buildable — live data**
**IN spec (algorithm, output contract):** [`../IN/uc-42-payment-run-prioritisation.md`](../IN/uc-42-payment-run-prioritisation.md) · **live evidence 2026-10-04**

---

The algorithm is UC-42's: holds → net off → score by cost of delay → rank. Only the cost-of-delay sources
differ. Sections 1, 3, 5 and 7 are as UC-42.

## 2. Basis (US): cost of delay and hold reasons

| Source | Effect | Spec |
|---|---|---|
| Contractual due date | Late fees or interest per vendor terms (`payment_terms`) | — |
| Early-payment discount | Lost discount (e.g. 2/10 net 30) | — |
| **Backup withholding** | A vendor with no W-9 or TIN: **withhold 24%** before paying (IRC §3406), so the payment line must be reduced | [US-06](us-06-form-1099-readiness.md), [US-16](us-16-vendor-master-audit.md) |
| Duplicate candidate / standing-order check | Hold | [US-07](us-07-duplicate-vendor-payment.md) |
| Pending or rejected approval | Hold | [US-08](us-08-approval-sla-audit.md) |
| Unapplied credits | Net off | [US-17](us-17-unapplied-vendor-credits.md) |

There is no US private-sector prompt-payment statute (US README mapping, UC-04 row) and no input credit at
stake (no Rule 37 analogue). The US plan is therefore driven by **terms, discounts and withholding**,
not by statutory penalties.

## 4. Input contract (US)

As UC-42, plus `Party.w9_on_file`, `tin`, `backup_withholding`, `is_1099_vendor`.

## 6. Known-bad data (US)

- `payment_terms = 30` on all 81 non-void bills. No discount terms exist anywhere, so the discount
  driver is dormant on this tenant.

## 9. Validation (US)

1. **Live:**
   - open bills **14, $115,392.56**;
   - **overdue 13, $108,642.56**;
   - due in the next 7 days: 1, $6,750.00.
   - The oldest are **BILL-2026-00052** (`08248af6-493f-470e-a484-fab173beb80a`) and BILL-2026-00044
     (`adce2b45-f649-4684-883a-694bb4b7e594`). Both were dated 2026-04-16 and due 2026-05-16, for
     $3,288.20 and $6,854.40, and are **141 days overdue**.
2. **Withholding fixture:** a $7,800 payment to a vendor with `w9_on_file = 0` → pay $5,928 and withhold
   $1,872 (24%) (Canton Industrial Consulting, US-06's live case).

## 10. Open questions (US)

- 13 of 14 open bills are overdue, several by more than four months. Disputed, or simply unpaid? There's no
  dispute flag on `Bill`. Ask the operators before ranking them as urgent.

## 11. Live evidence — actual calls, 2026-10-04

- `Bill.list {"limit":1000}` → 101.
  - Status: paid 67, void 15, open 14, draft 5.
  - Approvals: approved 37, pending 6, rejected 2.
  - `payment_terms: 30` on all non-void bills.
- `Party.list` → vendor W-9 and 1099 fields as tabled in US-16.
