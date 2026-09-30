"""Transports: how the harness reaches AgentSwitch.

Patterns:
- **Adapter** — `LiveTransport` adapts `scripts.agentswitch_client.AgentSwitchClient`
  (raw JSON-RPC dicts) to the small `Transport` interface the harness depends on, and
  normalises MCP's three result shapes (JSON-RPC error, `isError`, `content[0].text`)
  into one `ToolResult`.
- **Decorator** — `RecordingTransport` wraps any transport and saves every response to
  disk; `ReplayTransport` serves them back. Same interface, so a recorded live run can
  be replayed offline (harness_plan.md §8 "record mode") and hand-written tests can run
  without credentials.
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None
    meta: dict = field(default_factory=dict)


class Transport(Protocol):
    def call_tool(self, name: str, arguments: dict) -> ToolResult: ...
    def rest_get(self, path: str, params: dict | None = None) -> dict: ...


class LiveTransport:
    def __init__(self, client):
        self._client = client
        self._initialized = False

    def _ensure_session(self) -> None:
        if not self._initialized:
            self._client.mcp_initialize(client_name="team03-harness")
            self._client.mcp_notify_initialized()
            self._initialized = True

    def call_tool(self, name: str, arguments: dict) -> ToolResult:
        self._ensure_session()
        rpc = self._client.mcp_rpc("tools/call", {"name": name, "arguments": arguments})
        if "error" in rpc:
            err = rpc["error"]
            detail = json.dumps(err.get("data")) if err.get("data") else ""
            return ToolResult(False, error=f"{err.get('code')}: {err.get('message')} {detail}".strip())
        result = rpc.get("result", {})
        text = "".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        if result.get("isError"):
            return ToolResult(False, error=text or "tool reported isError")
        try:
            return ToolResult(True, data=json.loads(text) if text else None)
        except json.JSONDecodeError:
            return ToolResult(True, data=text)

    def rest_get(self, path: str, params: dict | None = None) -> dict:
        return self._client.rest_get(path, params)


def _key(kind: str, name: str, payload: dict | None) -> str:
    digest = hashlib.sha1(json.dumps([kind, name, payload or {}], sort_keys=True).encode()).hexdigest()
    safe = name.strip("/").replace("/", "_").replace(".", "_")
    return f"{safe}-{digest[:12]}"


class RecordingTransport:
    """Decorator: delegates to `inner` and writes each response under `directory`.

    Recordings contain live business data. Keep them under runs/ (gitignored) unless a
    human has reviewed and trimmed them for tests/recorded/.
    """

    def __init__(self, inner: Transport, directory: Path):
        self._inner = inner
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _save(self, key: str, body: dict) -> None:
        (self._dir / f"{key}.json").write_text(json.dumps(body, indent=1, default=str), encoding="utf-8")

    def call_tool(self, name: str, arguments: dict) -> ToolResult:
        result = self._inner.call_tool(name, arguments)
        self._save(_key("tool", name, arguments),
                   {"ok": result.ok, "data": result.data, "error": result.error})
        return result

    def rest_get(self, path: str, params: dict | None = None) -> dict:
        body = self._inner.rest_get(path, params)
        self._save(_key("rest", path, params), {"rest": body})
        return body


class ReplayMiss(LookupError):
    """A replayed run asked for a call that was never recorded."""


class ReplayTransport:
    def __init__(self, directory: Path):
        self._dir = Path(directory)

    def _load(self, key: str) -> dict:
        path = self._dir / f"{key}.json"
        if not path.exists():
            raise ReplayMiss(f"no recording {path.name} — re-record with --record")
        return json.loads(path.read_text(encoding="utf-8"))

    def call_tool(self, name: str, arguments: dict) -> ToolResult:
        body = self._load(_key("tool", name, arguments))
        return ToolResult(body["ok"], data=body.get("data"), error=body.get("error"))

    def rest_get(self, path: str, params: dict | None = None) -> dict:
        return self._load(_key("rest", path, params))["rest"]
