"""Custom Agent Loop driving MCP (JSON-RPC 2.0) for Seat 03 (Payables & Tax).

No third-party agent frameworks (LangChain, CrewAI, AutoGen) are permitted per
the capstone rules. This is a minimal hand-rolled loop:

  1. Load SKILL.md as the system prompt.
  2. Discover tools via MCP `tools/list`.
  3. Loop: call the LLM, execute any requested tool via MCP `tools/call`,
     feed results back, repeat until the LLM returns a final answer.

MCP endpoint: POST {AGENTSWITCH_BASE_URL}/api/mcp
"""

import json
import os

import requests

MCP_PROTOCOL_VERSION = "2025-11-25"
AGENTSWITCH_BASE_URL = os.environ.get("AGENTSWITCH_BASE_URL", "https://agentswitch.theschoolofai.in")
MCP_URL = f"{AGENTSWITCH_BASE_URL}/api/mcp"


def _rpc(session: requests.Session, method: str, params: dict | None = None, request_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
    response = session.post(MCP_URL, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def mcp_initialize(session: requests.Session) -> dict:
    return _rpc(session, "initialize", {"protocolVersion": MCP_PROTOCOL_VERSION})


def get_mcp_tools(session: requests.Session) -> list:
    result = _rpc(session, "tools/list")
    return result.get("result", {}).get("tools", [])


def execute_mcp_call(session: requests.Session, tool_name: str, tool_args: dict) -> dict:
    result = _rpc(session, "tools/call", {"name": tool_name, "arguments": tool_args})
    return result.get("result", {})


def call_llm(messages: list, tools: list):
    """Placeholder for the LLM call -- wire up your chosen provider's SDK here."""
    raise NotImplementedError("Wire up an LLM client (e.g. Anthropic SDK) here.")


def run_agent_loop(user_query: str, session: requests.Session | None = None):
    session = session or requests.Session()
    mcp_initialize(session)
    tools = get_mcp_tools(session)

    messages = [
        {"role": "system", "content": open("SKILL.md").read()},
        {"role": "user", "content": user_query},
    ]

    while True:
        response = call_llm(messages, tools=tools)

        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                tool_name = tool_call["name"]
                tool_args = tool_call["arguments"]

                result = execute_mcp_call(session, tool_name, tool_args)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result),
                    }
                )
        else:
            return response.get("content")


if __name__ == "__main__":
    print(run_agent_loop("What is our tax liability this period, what is unclaimed, and is any vendor being paid twice?"))
