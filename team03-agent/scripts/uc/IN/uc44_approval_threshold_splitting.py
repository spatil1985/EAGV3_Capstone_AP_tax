"""UC-44 — Approval-threshold splitting (India).

Spec: docs/usecases/IN/uc-44-approval-threshold-splitting.md.
Question: "Is anyone splitting purchases into smaller bills so each one stays under the approval limit?"

Engine: scripts/uc/common/threshold_split.py. The threshold is assumed (₹1,00,000) in
config/overrides/approval_thresholds.yaml because ApprovalPolicy is 403 for our role (N426 T2.1).
Rules: split_candidate (bills and purchase orders), policy_unreadable (context row).
"""

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import CONTEXT, Finding
from scripts.uc.common.threshold_split import split_findings, thresholds


class ThresholdSplitting(Rule):
    id = "approval_control"
    severity = 55

    def evaluate(self, data: Dataset, ctx):
        limits = thresholds(ctx.tenant)
        yield from split_findings(data.get("bills", []), "Bill", limits.get("Bill"), ctx)
        yield from split_findings(data.get("purchase_orders", []), "PurchaseOrder", limits.get("PurchaseOrder"), ctx)
        yield Finding(finding_type="approval_control", rule="policy_unreadable", severity=10, status=CONTEXT,
                      entity_type="ApprovalPolicy", entity_id="policy", entity_ref="approval policy",
                      currency=ctx.currency,
                      summary="ApprovalPolicy returns 403 for our role, so approval limits are taken from "
                              "config/overrides/approval_thresholds.yaml (" +
                              ", ".join(f"{k} {v.get('threshold')} {v.get('source')}" for k, v in limits.items()) + ").",
                      details={"thresholds": limits})


class ApprovalThresholdSplitting(Playbook):

    @property
    def rules(self):
        return [ThresholdSplitting()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), purchase_orders=fetcher.list("PurchaseOrder"))

    def summary(self, outcome, ctx):
        splits = [f for f in outcome.findings if f.rule == "split_candidate"]
        if not splits:
            return "No vendor's bills or POs look split to stay under the approval limit (limit assumed — policy unreadable)."
        names = ", ".join(f.entity_ref for f in splits[:3])
        return (f"{len(splits)} group(s) look split to stay under the approval limit ({names}); every document is under "
                f"the limit, together they exceed it, and none was approved. The limit is assumed: the approval policy "
                f"can't be read.")
