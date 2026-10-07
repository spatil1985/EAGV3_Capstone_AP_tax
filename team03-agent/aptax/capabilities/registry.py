"""Capability registry — the complete surface the model can act through (agent_design.md §4.8).

Adapted from S17Code `capabilities.py`: every capability declares strict argument
contracts, and Python validates every proposed call before it runs. A model can choose
a capability; it cannot invent one or bypass its validation.

`advertised()` is the authority boundary. A capability is offered only if it is live,
applies to the tenant's regime and vertical, its required tools exist in the live
tools/list, and — when it has a side effect — the run's subscription allows that effect.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable

from aptax.llm.contract import ToolSpec


class CapabilityError(ValueError):
    """A proposed call does not satisfy the capability contract."""


@dataclass(frozen=True)
class Arg:
    kind: str                          # string | integer | boolean | object | array | date
    description: str
    required: bool = True
    choices: tuple = ()
    minimum: int | None = None
    maximum: int | None = None
    items: dict | None = None          # JSON schema of array items

    def schema(self) -> dict:
        kind = "string" if self.kind == "date" else self.kind
        out: dict[str, Any] = {"type": kind, "description": self.description}
        if self.kind == "date":
            out["format"] = "date"
        if self.kind == "array" and self.items:
            out["items"] = self.items
        if self.choices:
            out["enum"] = list(self.choices)
        if self.minimum is not None:
            out["minimum"] = self.minimum
        if self.maximum is not None:
            out["maximum"] = self.maximum
        return out

    def check(self, label: str, value):
        if self.kind in ("string", "date"):
            if not isinstance(value, str) or not value.strip():
                raise CapabilityError(f"{label} must be a non-empty string")
            value = value.strip()
            if self.kind == "date":
                try:
                    date.fromisoformat(value)
                except ValueError:
                    raise CapabilityError(f"{label} must be an ISO date (YYYY-MM-DD)") from None
            if self.maximum is not None and len(value) > self.maximum:
                raise CapabilityError(f"{label} exceeds {self.maximum} characters")
        elif self.kind == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise CapabilityError(f"{label} must be an integer")
            if self.minimum is not None and value < self.minimum:
                raise CapabilityError(f"{label} must be >= {self.minimum}")
            if self.maximum is not None and value > self.maximum:
                raise CapabilityError(f"{label} must be <= {self.maximum}")
        elif self.kind == "boolean":
            if not isinstance(value, bool):
                raise CapabilityError(f"{label} must be a boolean")
        elif self.kind == "object":
            if not isinstance(value, dict):
                raise CapabilityError(f"{label} must be an object")
        elif self.kind == "array":
            if not isinstance(value, list):
                raise CapabilityError(f"{label} must be an array")
            if self.maximum is not None and len(value) > self.maximum:
                raise CapabilityError(f"{label} permits at most {self.maximum} items")
        else:
            raise CapabilityError(f"unsupported argument kind {self.kind!r}")
        if self.choices and value not in self.choices:
            raise CapabilityError(f"{label} must be one of {list(self.choices)}")
        return value


@dataclass(frozen=True)
class Capability:
    name: str
    description: str
    kind: str                                   # read | playbook | action | terminal
    worker: Callable[[dict], dict] | None
    args: dict[str, Arg] = field(default_factory=dict)
    side_effect: str | None = None              # the effect name a subscription must allow
    tax_regimes: tuple = ("all",)
    verticals: tuple = ("all",)
    requires_tools: tuple = ()
    result_chars: int = 4_000                   # longest string the model sees in a result (S17 clip)

    def spec(self) -> ToolSpec:
        props = {k: a.schema() for k, a in self.args.items()}
        required = [k for k, a in self.args.items() if a.required]
        schema = {"type": "object", "properties": props, "additionalProperties": False}
        if required:
            schema["required"] = required
        return ToolSpec(self.name, self.description, schema)

    def validate(self, values) -> dict:
        if not isinstance(values, dict):
            raise CapabilityError(f"arguments for {self.name} must be an object")
        unknown = set(values) - set(self.args)
        if unknown:
            raise CapabilityError(f"unsupported arguments for {self.name}: {sorted(unknown)}")
        clean = {}
        for key, arg in self.args.items():
            if key not in values or values[key] is None:
                if arg.required:
                    raise CapabilityError(f"{self.name} requires argument {key!r}")
                continue
            clean[key] = arg.check(f"{self.name}.{key}", values[key])
        return clean


class Registry:
    def __init__(self, capabilities: list[Capability]):
        self._items: dict[str, Capability] = {}
        for c in capabilities:
            if c.name in self._items:
                raise ValueError(f"duplicate capability {c.name!r}")
            self._items[c.name] = c

    def __contains__(self, name: str) -> bool:
        return name in self._items

    def get(self, name: str) -> Capability:
        try:
            return self._items[name]
        except KeyError:
            raise CapabilityError(f"unknown capability {name!r}") from None

    def all(self) -> list[Capability]:
        return list(self._items.values())

    def advertised(self, ctx, *, allowed_effects=frozenset(), available_tools: set[str] = frozenset()):
        """Capabilities this run may offer the model — the authority boundary."""
        out = []
        for c in self._items.values():
            if "all" not in c.tax_regimes and ctx.tax_regime not in c.tax_regimes:
                continue
            if "all" not in c.verticals and ctx.vertical not in c.verticals:
                continue
            if available_tools and any(t not in available_tools for t in c.requires_tools):
                continue
            if c.side_effect and c.side_effect not in allowed_effects:
                continue
            out.append(c)
        return out
