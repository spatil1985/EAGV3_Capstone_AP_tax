"""LLM-generated, not graded. A spent platform token budget (HTTP 429 budget_exhausted) is final."""

import json

import pytest
import requests

from aptax.agentswitch import transport as T
from aptax.agentswitch.transport import BudgetExhausted, LiveTransport


def http_error(status, body):
    resp = requests.Response()
    resp.status_code = status
    resp._content = json.dumps(body).encode()
    return requests.HTTPError(f"{status} error", response=resp)


class Client:
    """mcp_rpc / rest_get raise `error` until `succeed_after` attempts, then return `result`."""

    def __init__(self, error, succeed_after=None, result=None):
        self.error, self.succeed_after, self.result = error, succeed_after, result or {"result": {}}
        self.calls = 0

    def mcp_initialize(self, client_name=""):
        return {}

    def mcp_notify_initialized(self):
        pass

    def _maybe_fail(self):
        self.calls += 1
        if self.succeed_after is None or self.calls <= self.succeed_after:
            raise self.error
        return self.result

    def mcp_rpc(self, method, params=None):
        return self._maybe_fail()

    def rest_get(self, path, params=None):
        return self._maybe_fail()


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr(T.time, "sleep", slept.append)
    return slept


def test_budget_exhausted_is_not_retried(no_sleep):
    client = Client(http_error(429, {"error": "budget_exhausted", "detail": "token budget spent"}))
    live = LiveTransport(client)
    with pytest.raises(BudgetExhausted):
        live.call_tool("Bill.list", {})
    assert client.calls == 1 and no_sleep == []
    assert live.budget_exhausted


def test_after_budget_exhausted_every_call_fails_without_the_network():
    client = Client(http_error(429, {"detail": "budget_exhausted"}))
    live = LiveTransport(client)
    with pytest.raises(BudgetExhausted):
        live.call_tool("Bill.list", {})
    with pytest.raises(BudgetExhausted):
        live.rest("GET", "/api/accounting/locale")
    with pytest.raises(BudgetExhausted):
        live.call_tool("Invoice.list", {})
    assert client.calls == 1


def test_ordinary_429_is_still_retried(no_sleep):
    client = Client(http_error(429, {"detail": "rate limited, slow down"}), succeed_after=2,
                    result={"result": {"content": [{"type": "text", "text": "{\"data\": []}"}]}})
    live = LiveTransport(client)
    assert live.call_tool("Bill.list", {}).ok
    assert client.calls == 3 and len(no_sleep) == 2
    assert live.budget_exhausted is None


def test_401_is_not_mistaken_for_a_spent_budget():
    client = Client(http_error(401, {"detail": "budget_exhausted"}))
    live = LiveTransport(client)
    result = live.call_tool("Bill.list", {})
    assert not result.ok and live.budget_exhausted is None
