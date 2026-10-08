"""US-17 — Unapplied vendor credits (US instance of UC-41).

Spec: docs/usecases/US/us-17-unapplied-vendor-credits.md.
Question: "Are we about to pay vendors in full while they owe us money from credits?"

Same rules as UC-41 (scripts/uc/common/vendor_balance.py): credit_applicable_now, stale_credit,
advance_unadjusted. Keystone has no vendor credits today, so 0 findings is the expected answer.
"""

from scripts.uc.IN.uc41_unapplied_vendor_credits import UnappliedVendorCredits


class UnappliedVendorCreditsUS(UnappliedVendorCredits):
    """UC-41's playbook unchanged; kept as its own class so the US manifest and SOP stand alone."""
