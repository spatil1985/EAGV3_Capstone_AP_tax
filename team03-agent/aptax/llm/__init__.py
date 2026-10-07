"""The LLM boundary (agent_design.md §4.11).

The runtime depends only on `contract.py`. The gateway itself — providers, keys,
routing, budget admission, metering — is the team's own module, plugged in by name:

    APTAX_LLM=package.module:factory      # factory() returns an object with complete(...)

`complete` must accept the keyword arguments of `contract.LLMGateway.complete` and
return a `contract.LLMResponse`. Nothing in aptax reads provider keys or calls a
provider directly.
"""

import importlib
import os

from aptax.config import LLM_ENV
from aptax.llm.contract import (  # noqa: F401 — re-exported for gateway authors
    BudgetRefused, LLMError, LLMGateway, LLMResponse, ToolCall, ToolSpec, Usage)


class LLMNotConfigured(LLMError):
    """No gateway is plugged in, or the plug-in is not a gateway."""


def load_llm(spec: str | None = None):
    spec = (spec if spec is not None else os.environ.get(LLM_ENV, "")).strip()
    if not spec:
        raise LLMNotConfigured(f"no LLM gateway configured: set {LLM_ENV}=package.module:factory "
                               "(see aptax/llm/contract.py for the interface)")
    module_name, _, attr = spec.partition(":")
    if not module_name or not attr:
        raise LLMNotConfigured(f"{LLM_ENV} must look like package.module:factory, got {spec!r}")
    try:
        factory = getattr(importlib.import_module(module_name), attr)
    except (ImportError, AttributeError) as exc:
        raise LLMNotConfigured(f"cannot load {spec}: {exc}") from exc
    gateway = factory()
    if not callable(getattr(gateway, "complete", None)):
        raise LLMNotConfigured(f"{spec} returned {type(gateway).__name__}, which has no complete(...)")
    return gateway
