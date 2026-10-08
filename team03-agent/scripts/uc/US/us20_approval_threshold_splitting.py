"""US-20 — Approval-threshold splitting (US instance of UC-44).

Spec: docs/usecases/US/us-20-approval-threshold-splitting.md.
Question: "Is anyone splitting purchases to stay under the approval limit?"

Same test as UC-44 (scripts/uc/common/threshold_split.py). On Keystone the limit can be inferred from
approval history: bill approvals fall in two policy bands (≈ $3,075 … $10,000 and $10,626 … $16,739), so
the edge is $10,000. config/overrides/approval_thresholds.yaml carries it (source: inferred) and the run
context re-infers it each time, so a changed policy shows up. Fortnightly Apex Metals standing orders
contain bills above the limit, so they are not split candidates.
"""

from scripts.uc.IN.uc44_approval_threshold_splitting import ApprovalThresholdSplitting
from scripts.uc.common.threshold_split import infer_threshold, thresholds


class ApprovalThresholdSplittingUS(ApprovalThresholdSplitting):

    def fetch(self, ctx, fetcher):
        data = super().fetch(ctx, fetcher)
        data["requests"] = fetcher.list("ApprovalRequest")
        return data

    def context(self, data, findings, ctx):
        edge, bands = infer_threshold(data.get("requests", []), "Bill")
        configured = (thresholds(ctx.tenant).get("Bill") or {}).get("threshold")
        return {"inferred Bill approval edge": str(edge) if edge is not None else "not inferable",
                "configured Bill threshold": configured, "Bill approval bands": bands}
