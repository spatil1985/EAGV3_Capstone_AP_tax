"""Thin HTTP / JSON-RPC client for the AgentSwitch REST API and MCP endpoint.

Centralizes login (POST /api/auth/login -> Bearer token) and the MCP
JSON-RPC 2.0 handshake so `run_agent.py` and the live connectivity tests in
`tests/integration/` share one implementation instead of duplicating request
plumbing.
"""

import itertools
import os

import requests

DEFAULT_BASE_URL = "https://agentswitch.theschoolofai.in"
MCP_PROTOCOL_VERSION = "2025-11-25"


class AgentSwitchAuthError(RuntimeError):
    """Raised when login fails or the login response is malformed."""


class AgentSwitchClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"
        self._ids = itertools.count(1)

    @classmethod
    def login(cls, base_url: str, email: str, password: str) -> "AgentSwitchClient":
        response = requests.post(
            f"{base_url.rstrip('/')}/api/auth/login",
            json={"email": email, "password": password},
            timeout=30,
        )
        if response.status_code != 200:
            raise AgentSwitchAuthError(
                f"Login failed: HTTP {response.status_code} {response.text}"
            )
        token = response.json().get("token")
        if not token:
            raise AgentSwitchAuthError("Login response did not include a 'token' field")
        return cls(base_url, token)

    @classmethod
    def from_env(cls, prefix: str = "AGENTSWITCH") -> "AgentSwitchClient":
        """Log in using AGENTSWITCH_BASE_URL / _EMAIL / _PASSWORD env vars.

        AGENTSWITCH_BASE_URL defaults to Suryodaya (India); point it at
        https://class.agentswitch.theschoolofai.in for Keystone (US).
        """
        base_url = os.environ.get(f"{prefix}_BASE_URL", DEFAULT_BASE_URL)
        email = os.environ[f"{prefix}_EMAIL"]
        password = os.environ[f"{prefix}_PASSWORD"]
        return cls.login(base_url, email, password)

    # -- REST -----------------------------------------------------------

    def whoami(self) -> dict:
        response = self._session.get(f"{self.base_url}/api/auth/me", timeout=30)
        response.raise_for_status()
        return response.json()

    def get_locale(self) -> dict:
        response = self._session.get(f"{self.base_url}/api/accounting/locale", timeout=30)
        response.raise_for_status()
        return response.json()

    # -- MCP (JSON-RPC 2.0 over POST /api/mcp) ---------------------------

    def mcp_rpc(self, method: str, params: dict | None = None) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._ids),
            "method": method,
            "params": params or {},
        }
        response = self._session.post(f"{self.base_url}/api/mcp", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def mcp_get_raw(self) -> requests.Response:
        """Raw GET /api/mcp -- spec says this must 405 (there is no SSE stream)."""
        return self._session.get(f"{self.base_url}/api/mcp", timeout=30)

    def mcp_initialize(self, client_name: str = "team03-agent", client_version: str = "0.1") -> dict:
        return self.mcp_rpc(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": client_name, "version": client_version},
            },
        )

    def mcp_notify_initialized(self) -> None:
        """Fire-and-forget JSON-RPC notification (no id, no response)."""
        payload = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        self._session.post(f"{self.base_url}/api/mcp", json=payload, timeout=30)

    def mcp_tools_list(self) -> list:
        result = self.mcp_rpc("tools/list")
        return result.get("result", {}).get("tools", [])

    def mcp_tools_call(self, name: str, arguments: dict) -> dict:
        result = self.mcp_rpc("tools/call", {"name": name, "arguments": arguments})
        return result.get("result", {})
