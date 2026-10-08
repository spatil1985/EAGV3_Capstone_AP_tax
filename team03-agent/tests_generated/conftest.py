"""LLM-generated, not graded (see README.md). Shared fixtures for offline playbook checks."""

from dataclasses import dataclass, field
from datetime import date

import pytest

from aptax.config import PLAYBOOK_DIR, RULEBOOK_DIR
from aptax.domain.rules import Rulebook
from aptax.playbooks.base import Dataset


@dataclass
class FakeCtx:
    """The RunContext attributes playbooks read, without a live locale call."""

    tenant: str = "in"
    as_of: date = date(2026, 10, 8)
    tax_regime: str = "gst"
    currency: str = "INR"
    vertical: str = "manufacturing"
    features: dict = field(default_factory=dict)
    org: dict = field(default_factory=dict)
    run_id: str = "test-run"
    trigger: str = "on_request"
    dry_run: bool = True
    company_id: str = "co-1"
    rulebook: Rulebook = field(default_factory=lambda: Rulebook.load(PLAYBOOK_DIR / "constants.yaml",
                                                                     RULEBOOK_DIR))

    @property
    def period(self) -> str:
        return self.as_of.strftime("%Y-%m")

    def rule(self, name, on=None):
        return self.rulebook.rule(name, on or self.as_of)

    def constant(self, name):
        return self.rule(name)


@pytest.fixture
def make_ctx():
    def _make(**overrides):
        if overrides.get("tenant") == "us":
            overrides.setdefault("tax_regime", "sales_use_tax")
            overrides.setdefault("currency", "USD")
        return FakeCtx(**overrides)
    return _make


@pytest.fixture
def ds():
    return lambda **sets: Dataset(**sets)


def rules_of(findings) -> list[str]:
    return sorted(f.rule for f in findings)
