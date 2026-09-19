"""Live smoke test: does the MCP JSON-RPC endpoint answer the documented handshake?

Per the brief: one endpoint, JSON-RPC 2.0 at POST $AS/api/mcp, protocol
version 2025-11-25, no SSE stream (GET answers 405 with Allow: POST), no
batching.

Skipped unless AGENTSWITCH_EMAIL / AGENTSWITCH_PASSWORD are set -- see
tests/integration/conftest.py.
"""

from scripts.agentswitch_client import MCP_PROTOCOL_VERSION


def test_get_mcp_has_no_stream(client):
    response = client.mcp_get_raw()
    assert response.status_code == 405
    assert "POST" in response.headers.get("Allow", "")


def test_initialize_handshake_succeeds(client):
    response = client.mcp_initialize()
    assert response.get("jsonrpc") == "2.0"
    assert "error" not in response
    assert response["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION


def test_tools_list_exposes_seat_03_scope(client):
    client.mcp_initialize()
    client.mcp_notify_initialized()

    tools = client.mcp_tools_list()

    assert isinstance(tools, list)
    assert len(tools) > 0

    tool_names = {tool["name"] for tool in tools}
    allowed_prefixes = ("Invoice.", "Payment.", "TaxLine.", "Vendor.", "JournalEntry.")
    assert any(name.startswith(allowed_prefixes) for name in tool_names), (
        f"Expected at least one tool from {allowed_prefixes}, got {sorted(tool_names)}"
    )

    prohibited_prefixes = ("SalarySlip.", "Contract.", "EsignDocument.")
    leaked = [name for name in tool_names if name.startswith(prohibited_prefixes)]
    assert not leaked, f"Seat 03 should not see prohibited entities, but found: {leaked}"
