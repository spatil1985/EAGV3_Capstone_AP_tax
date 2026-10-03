"""Shared Finding row — the output contract every playbook emits.

Fixed fields follow UC-01 §7 (docs/usecases/IN/uc-01-rule-37-itc-reversal.md), the
schema `assignment.md` §7 designates as shared. Playbooks may put use-case-specific
values in `details`, but must not rename or drop the fixed fields.

`run_id` and `fingerprint` are stamped by the harness (harness/runner.py), never by a
playbook, so compute code stays free of run state.
"""

from dataclasses import asdict, dataclass, field, replace
from decimal import Decimal

FINDING = "finding"
CONTEXT = "context"
DATA_QUALITY = "data_quality"


@dataclass(frozen=True)
class Finding:
    finding_type: str
    rule: str
    entity_type: str
    entity_id: str
    entity_ref: str | None
    summary: str
    total_exposure: Decimal = Decimal("0")
    reversal_base_amount: Decimal = Decimal("0")
    interest_amount: Decimal = Decimal("0")
    currency: str = "INR"
    counterparty_id: str | None = None
    counterparty_name: str | None = None
    status: str = FINDING
    severity: int = 50
    details: dict = field(default_factory=dict)
    run_id: str | None = None
    fingerprint: str | None = None

    def stamped(self, run_id: str, fingerprint: str) -> "Finding":
        return replace(self, run_id=run_id, fingerprint=fingerprint)

    def to_dict(self) -> dict:
        row = asdict(self)
        # Decimal -> str keeps paise exact in JSON; floats would not.
        for key in ("total_exposure", "reversal_base_amount", "interest_amount"):
            row[key] = str(row[key])
        return row
