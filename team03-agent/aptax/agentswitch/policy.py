"""Declarative policy engine over config/policy.yaml (agent_design.md §4.10).

Semantics follow glc_v5 `policy/engine.py`:
- rules are tried in order; the **first match wins**;
- no rule matches → **deny**;
- an unreadable or malformed file → a **deny-everything** policy, so the agent boots
  in a known-safe state instead of an open one.

A rule matches on `tool` (fnmatch glob, also used for "GET /api/..." REST calls),
`tier` (T0–T3), `require_args` (exact argument values) and `when` (named conditions
the gateway knows at call time). Policy is data: changing what the agent may do is a
reviewed edit to the YAML file, not a code change.
"""

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from aptax.agentswitch.risk import Tier

CONDITIONS = {"allowlisted", "subscription_allows", "approval_granted"}
ACTIONS = {"allow", "deny"}


@dataclass(frozen=True)
class CallFacts:
    """What the gateway knows about one call when it asks the policy."""
    tool: str
    tier: Tier
    args: dict
    allowlisted: bool = False
    subscription_allows: bool = False
    approval_granted: bool = False


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    reason: str
    rule_index: int | None = None


@dataclass(frozen=True)
class Rule:
    action: str
    reason: str = ""
    tool: str | None = None
    tier: Tier | None = None
    require_args: dict = field(default_factory=dict)
    when: tuple[str, ...] = ()

    def matches(self, facts: CallFacts) -> bool:
        if self.tool and not fnmatch.fnmatchcase(facts.tool, self.tool):
            return False
        if self.tier is not None and facts.tier is not self.tier:
            return False
        for key, expected in self.require_args.items():
            if facts.args.get(key) != expected:
                return False
        return all(getattr(facts, cond) for cond in self.when)


DENY_EVERYTHING = (Rule(action="deny", reason="policy file unreadable — deny everything", tool="*"),)


def _parse_rule(raw: dict) -> Rule:
    action = raw.get("action")
    if action not in ACTIONS:
        raise ValueError(f"rule action must be one of {sorted(ACTIONS)}: {raw}")
    tier = raw.get("tier")
    if tier is not None:
        tier = Tier(int(str(tier).lstrip("Tt")))
    when = tuple(raw.get("when") or ())
    unknown = set(when) - CONDITIONS
    if unknown:
        raise ValueError(f"unknown condition(s) {sorted(unknown)} in {raw}")
    return Rule(action=action, reason=raw.get("reason", ""), tool=raw.get("tool"), tier=tier,
                require_args=dict(raw.get("require_args") or {}), when=when)


class PolicyEngine:
    def __init__(self, rules: tuple[Rule, ...], source: str = "<inline>", error: str | None = None):
        self.rules = rules
        self.source = source
        self.error = error            # why we fell back to deny-everything, if we did

    @classmethod
    def load(cls, path: Path) -> "PolicyEngine":
        try:
            raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
            rules = tuple(_parse_rule(r) for r in raw.get("rules") or ())
            if not rules:
                raise ValueError("no rules")
            return cls(rules, str(path))
        except Exception as exc:  # noqa: BLE001 — any problem means fail closed
            return cls(DENY_EVERYTHING, str(path), error=f"{type(exc).__name__}: {exc}")

    def evaluate(self, facts: CallFacts) -> Verdict:
        for index, rule in enumerate(self.rules):
            if rule.matches(facts):
                reason = rule.reason or f"policy rule {index} ({rule.action})"
                return Verdict(rule.action == "allow", reason, index)
        return Verdict(False, "no policy rule matched — default deny")
