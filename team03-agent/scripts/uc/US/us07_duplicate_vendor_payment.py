"""US-07 — Duplicate vendor payment (US instance of UC-05).

Spec: docs/usecases/US/us-07-duplicate-vendor-payment.md (algorithm as UC-05).
Question: "Is any vendor being paid twice?"

Same tiers as UC-05 (scripts/uc/common/duplicates.py). What differs on Keystone:
- `bill_number` is empty on every bill, so tier 1 (exact) can't run — the summary says so;
- standing orders (identical bills every ~14 days, each on its own PO) are not duplicates: the 3-day
  window already excludes them, and a different PO is noted on any pair;
- the recurring runaway (N6) is suppressed by the same recurring-template gate.
A duplicate costs cash (and any use tax self-assessed on it — US-02); there is no input credit.
"""

from scripts.uc.IN.uc05_duplicate_vendor_payment import DuplicateVendorPayment


class DuplicateVendorPaymentUS(DuplicateVendorPayment):
    """UC-05's playbook unchanged; kept as its own class so the US manifest and SOP stand alone."""
