"""Adapter from the LLM contract to a running glc_v5 gateway (agent_design.md §4.11).

Plug it in with:

    APTAX_LLM=aptax.llm.glc:factory
    GLC_BASE_URL=http://127.0.0.1:8111     # optional, this is the default
    GLC_PROVIDER=gemini                    # optional logical provider; glc picks the key slot
    GLC_TIMEOUT=120                        # optional, seconds per call

glc owns provider keys, retries, fallback and budget admission, so this module only
translates. A 402 from glc becomes `BudgetRefused` so the loop stops cleanly; anything
else that fails becomes `LLMError`. The semantic cache is always off: a fuzzy hit must
never serve a tax number.
"""

import os
from dataclasses import asdict

import requests

from aptax.llm.contract import BudgetRefused, LLMError, LLMResponse, ToolCall, ToolSpec, Usage

BASE_URL_ENV = "GLC_BASE_URL"
PROVIDER_ENV = "GLC_PROVIDER"
TIMEOUT_ENV = "GLC_TIMEOUT"
DEFAULT_BASE_URL = "http://127.0.0.1:8111"
PROJECT = "ap-tax"

# JSON-Schema keywords Gemini rejects in function parameters. glc_v5 strips these from
# response_format schemas but not from tool parameters (providers.py), so we do it here.
UNSUPPORTED_SCHEMA_KEYS = {"additionalProperties", "$schema", "title", "examples", "default"}


def _clean_schema(node):
    if isinstance(node, list):
        return [_clean_schema(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for key, value in node.items():
        if key == "properties" and isinstance(value, dict):
            # Keys here are property names, which may legitimately be "title" or "default".
            out[key] = {name: _clean_schema(prop) for name, prop in value.items()}
        elif key not in UNSUPPORTED_SCHEMA_KEYS:
            out[key] = _clean_schema(value)
    return out


class GlcGateway:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, provider: str | None = None,
                 timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.provider = provider or None
        self.timeout = timeout

    def complete(self, *, system: str, messages: list[dict], tools: list[ToolSpec], role: str,
                 run_id: str, max_tokens: int = 2048,
                 response_format: dict | None = None) -> LLMResponse:
        body = {
            "system": system,
            "messages": messages,
            "tools": [{**asdict(t), "input_schema": _clean_schema(t.input_schema)} for t in tools] or None,
            "max_tokens": max_tokens,
            "temperature": 0,
            "project": PROJECT,
            "agent": role,
            "session": run_id,
            "semantic_cache": False,
        }
        if self.provider:
            body["provider"] = self.provider
        if response_format is not None:
            body["response_format"] = response_format
        try:
            resp = requests.post(f"{self.base_url}/v1/chat", json=body, timeout=self.timeout)
        except requests.RequestException as exc:
            raise LLMError(f"glc gateway unreachable at {self.base_url}: {exc}") from exc

        if resp.status_code == 402:
            detail = _json(resp).get("detail")
            detail = detail if isinstance(detail, dict) else {"detail": detail}
            raise BudgetRefused(detail.get("message") or "budget exceeded", detail)
        if resp.status_code != 200:
            raise LLMError(f"glc /v1/chat returned HTTP {resp.status_code}: {resp.text[:500]}")

        data = _json(resp)
        if data.get("stop_reason") == "error":
            raise LLMError(f"glc reported a provider error; attempted: {data.get('attempted')}")
        return LLMResponse(
            content=data.get("text") or None,
            tool_calls=[ToolCall(id=tc["id"], name=tc["name"], arguments=tc.get("arguments") or {},
                                 provider_meta=tc.get("provider_meta"))
                        for tc in data.get("tool_calls") or []],
            stop_reason=data.get("stop_reason") or "end_turn",
            usage=Usage(
                input_tokens=int(data.get("input_tokens") or 0),
                output_tokens=int(data.get("output_tokens") or 0),
                cache_tokens=int(data.get("cache_read_input_tokens") or 0),
                usd=float((data.get("cost") or {}).get("total_usd") or 0.0),
                latency_ms=int(data.get("latency_ms") or 0)),
            provider=data.get("provider") or "",
            model=data.get("model") or "")


def _json(resp) -> dict:
    try:
        data = resp.json()
    except ValueError as exc:
        raise LLMError(f"glc returned non-JSON (HTTP {resp.status_code}): {resp.text[:500]}") from exc
    return data if isinstance(data, dict) else {}


def factory() -> GlcGateway:
    return GlcGateway(base_url=os.environ.get(BASE_URL_ENV, DEFAULT_BASE_URL),
                      provider=os.environ.get(PROVIDER_ENV, "gemini"),
                      timeout=float(os.environ.get(TIMEOUT_ENV, "120")))
