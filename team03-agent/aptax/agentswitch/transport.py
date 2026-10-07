"""Transports: how aptax reaches AgentSwitch (MCP and REST).

Ported from harness/access/transport.py (agent_design.md §2a) and extended:
- **Retry with backoff** on timeouts, connection errors and HTTP 5xx/429: up to 4
  attempts, 0.5·2ⁿ s capped at 4 s (the S17 `gateway.py` schedule).
- **A concurrency semaphore** (default 4), because the agent loop runs up to four
  tool calls at once and the platform is shared with other teams.
- `tools_list()`, so the registry can hide capabilities whose tools don't exist.
- `rest(method, …)`, so the gateway can reach the REST allowlist (G2).

Same Adapter / Decorator shape as the harness: `LiveTransport` adapts the raw client,
`RecordingTransport` saves every response, `ReplayTransport` serves them offline.
"""

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import requests

RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass
class ToolResult:
    ok: bool
    data: Any = None
    error: str | None = None
    meta: dict = field(default_factory=dict)


class Transport(Protocol):
    def call_tool(self, name: str, arguments: dict) -> ToolResult: ...
    def rest(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> Any: ...
    def tools_list(self) -> list[dict]: ...


def _with_retry(operation, attempts: int = 4):
    """Run `operation()`; retry transient failures with exponential backoff."""
    for attempt in range(attempts):
        try:
            return operation()
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in RETRY_STATUS or attempt == attempts - 1:
                raise
        except (requests.Timeout, requests.ConnectionError):
            if attempt == attempts - 1:
                raise
        time.sleep(min(0.5 * (2 ** attempt), 4.0))
    raise RuntimeError("unreachable")


class LiveTransport:
    def __init__(self, client, *, max_concurrency: int = 4):
        self._client = client
        self._initialized = False
        self._init_lock = threading.Lock()
        self._slots = threading.Semaphore(max_concurrency)
        self._tools: list[dict] | None = None

    def _ensure_session(self) -> None:
        with self._init_lock:
            if not self._initialized:
                _with_retry(lambda: self._client.mcp_initialize(client_name="team03-aptax"))
                self._client.mcp_notify_initialized()
                self._initialized = True

    def call_tool(self, name: str, arguments: dict) -> ToolResult:
        self._ensure_session()
        with self._slots:
            try:
                rpc = _with_retry(lambda: self._client.mcp_rpc(
                    "tools/call", {"name": name, "arguments": arguments}))
            except requests.RequestException as exc:
                return ToolResult(False, error=f"transport: {type(exc).__name__}: {exc}")
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

    def rest(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> Any:
        with self._slots:
            if method == "GET":
                return _with_retry(lambda: self._client.rest_get(path, params))
            if method == "POST":
                return _with_retry(lambda: self._client.rest_post(path, body))
        raise ValueError(f"unsupported method {method}")

    def tools_list(self) -> list[dict]:
        if self._tools is None:
            self._ensure_session()
            self._tools = _with_retry(self._client.mcp_tools_list)
        return self._tools


def _key(kind: str, name: str, payload) -> str:
    digest = hashlib.sha1(json.dumps([kind, name, payload or {}], sort_keys=True,
                                     default=str).encode()).hexdigest()
    safe = name.strip("/").replace("/", "_").replace(".", "_").replace(" ", "_")
    return f"{safe}-{digest[:12]}"


class RecordingTransport:
    """Decorator: delegates to `inner` and saves each response under `directory`.

    Recordings contain live business data: they belong under runs/ (gitignored).
    """

    def __init__(self, inner: Transport, directory: Path):
        self._inner = inner
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _save(self, key: str, body) -> None:
        (self._dir / f"{key}.json").write_text(json.dumps(body, indent=1, default=str), encoding="utf-8")

    def call_tool(self, name: str, arguments: dict) -> ToolResult:
        result = self._inner.call_tool(name, arguments)
        self._save(_key("tool", name, arguments), {"ok": result.ok, "data": result.data, "error": result.error})
        return result

    def rest(self, method, path, params=None, body=None):
        response = self._inner.rest(method, path, params, body)
        self._save(_key(f"rest-{method}", path, {"params": params, "body": body}), {"rest": response})
        return response

    def tools_list(self) -> list[dict]:
        tools = self._inner.tools_list()
        self._save("tools_list", {"tools": tools})
        return tools


class ReplayMiss(LookupError):
    """A replayed run asked for a call that was never recorded."""


class ReplayTransport:
    def __init__(self, directory: Path):
        self._dir = Path(directory)

    def _load(self, key: str) -> dict:
        path = self._dir / f"{key}.json"
        if not path.exists():
            raise ReplayMiss(f"no recording {path.name}; re-record with --record")
        return json.loads(path.read_text(encoding="utf-8"))

    def call_tool(self, name: str, arguments: dict) -> ToolResult:
        try:
            body = self._load(_key("tool", name, arguments))
        except ReplayMiss as exc:
            return ToolResult(False, error=str(exc))
        return ToolResult(body["ok"], data=body.get("data"), error=body.get("error"))

    def rest(self, method, path, params=None, body=None):
        return self._load(_key(f"rest-{method}", path, {"params": params, "body": body}))["rest"]

    def tools_list(self) -> list[dict]:
        try:
            return self._load("tools_list")["tools"]
        except ReplayMiss:
            return []
