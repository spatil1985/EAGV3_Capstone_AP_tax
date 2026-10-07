"""Shared contracts, re-exported from their current home.

`Finding` (UC-01 §7 row) and the money helpers live in scripts/ because the
UC-12 playbook uses them today. aptax imports them through here, so moving them into
aptax/domain/ later (agent_design.md §7) is a one-file change.
"""

from scripts.findings import CONTEXT, DATA_QUALITY, FINDING, Finding  # noqa: F401
from scripts.money import fmt, money  # noqa: F401
