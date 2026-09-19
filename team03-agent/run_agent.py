"""Custom Agent Loop driving MCP (JSON-RPC 2.0) for Seat 03 (Payables & Tax).

No third-party agent frameworks (LangChain, CrewAI, AutoGen) are permitted per
the capstone rules. This is a minimal hand-rolled loop:

  1. Log in (POST /api/auth/login) to get a Bearer token.
  2. Load SKILL.md as the system prompt.
  3. Discover tools via MCP `tools/list`.
  4. Loop: call the LLM, execute any requested tool via MCP `tools/call`,
     feed results back, repeat until the LLM returns a final answer.

Auth and MCP transport live in `scripts/agentswitch_client.py`, shared with
the live connectivity tests in `tests/integration/`.

Credentials come from the environment -- never hardcode them here:
  AGENTSWITCH_BASE_URL  (default: Suryodaya; set to the Keystone URL for US)
  AGENTSWITCH_EMAIL
  AGENTSWITCH_PASSWORD
"""

import json

from scripts.agentswitch_client import AgentSwitchClient


def call_llm(messages: list, tools: list):
    """Placeholder for the LLM call -- wire up your chosen provider's SDK here."""
    raise NotImplementedError("Wire up an LLM client (e.g. Anthropic SDK) here.")


def run_agent_loop(user_query: str, client: AgentSwitchClient | None = None):
    client = client or AgentSwitchClient.from_env()
    client.mcp_initialize()
    client.mcp_notify_initialized()
    tools = client.mcp_tools_list()

    messages = [
        {"role": "system", "content": open("SKILL.md").read()},
        {"role": "user", "content": user_query},
    ]

    while True:
        response = call_llm(messages, tools=tools)

        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                result = client.mcp_tools_call(tool_call["name"], tool_call["arguments"])

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
