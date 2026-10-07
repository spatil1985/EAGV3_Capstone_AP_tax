"""The only LLM interface the runtime sees (agent_design.md §4.11).

Messages use the neutral shape glc_v5 adapters already translate (providers.py docs):

    {"role": "user" | "assistant" | "tool", "content": str,
     "tool_calls": [{"id", "name", "arguments", "provider_meta"?}],   # assistant turns
     "tool_call_id": str, "name": str}                                # tool turns

Capability names the model sees are our own snake_case names (as_query, eway_coverage,
submit_answer), never dotted MCP tool names, so no provider rejects them.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    provider_meta: dict | None = None

    def as_message_part(self) -> dict:
        part = {"id": self.id, "name": self.name, "arguments": self.arguments}
        if self.provider_meta:
            part["provider_meta"] = self.provider_meta
        return part


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_tokens: int = 0
    usd: float = 0.0
    latency_ms: int = 0


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    usage: Usage = field(default_factory=Usage)
    provider: str = ""
    model: str = ""


class LLMError(RuntimeError):
    pass


class BudgetRefused(LLMError):
    """Admission refused before the provider was called (glc economics/budget.py idea)."""

    def __init__(self, reason: str, detail: dict):
        super().__init__(reason)
        self.detail = detail


class LLMGateway(Protocol):
    def complete(self, *, system: str, messages: list[dict], tools: list[ToolSpec], role: str,
                 run_id: str, max_tokens: int = 2048,
                 response_format: dict | None = None) -> LLMResponse: ...
