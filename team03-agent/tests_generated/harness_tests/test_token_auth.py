"""LLM-generated, not graded. Seat-token auth: from_token and make_transport's token path."""

import pytest
import requests

from aptax import service
from aptax.agentswitch.transport import LiveTransport
from scripts.agentswitch_client import AgentSwitchAuthError, AgentSwitchClient


@pytest.fixture
def no_network(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("network call attempted")
    monkeypatch.setattr(requests, "post", boom)
    monkeypatch.setattr(requests, "get", boom)


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.setattr(service, "load_dotenv", lambda: 0)   # never read the developer's .env
    for prefix in ("AGENTSWITCH", "US_AGENTSWITCH"):
        for key in ("BASE_URL", "TOKEN", "EMAIL", "PASSWORD"):
            monkeypatch.delenv(f"{prefix}_{key}", raising=False)


def test_from_token_sets_bearer_without_login(no_network):
    client = AgentSwitchClient.from_token(" https://class.example/ ", " tok123\n")
    assert client.base_url == "https://class.example"
    assert client.token == "tok123"
    assert client._session.headers["Authorization"] == "Bearer tok123"


@pytest.mark.parametrize("base_url, token", [("", "tok"), ("https://x", "  ")])
def test_from_token_rejects_empty_values(base_url, token):
    with pytest.raises(AgentSwitchAuthError):
        AgentSwitchClient.from_token(base_url, token)


def test_make_transport_prefers_token(clean_env, no_network, monkeypatch):
    monkeypatch.setenv("US_AGENTSWITCH_BASE_URL", "https://class.example/")
    monkeypatch.setenv("US_AGENTSWITCH_TOKEN", "tok-us")
    monkeypatch.setenv("US_AGENTSWITCH_EMAIL", "x@y")
    monkeypatch.setenv("US_AGENTSWITCH_PASSWORD", "pw")
    transport = service.make_transport("us")
    assert isinstance(transport, LiveTransport)
    assert transport._client.token == "tok-us"
    assert transport._client.base_url == "https://class.example"


def test_token_without_base_url_is_an_error(clean_env, monkeypatch):
    monkeypatch.setenv("AGENTSWITCH_TOKEN", "tok")
    with pytest.raises(service.ServiceError, match="AGENTSWITCH_BASE_URL"):
        service.make_transport("in")


def test_falls_back_to_login_without_token(clean_env, monkeypatch):
    monkeypatch.setenv("AGENTSWITCH_EMAIL", "a@b")
    monkeypatch.setenv("AGENTSWITCH_PASSWORD", "pw")
    calls = []

    def fake_login(cls, base_url, email, password):
        calls.append((base_url, email, password))
        return AgentSwitchClient(base_url, "tok-login")

    monkeypatch.setattr(AgentSwitchClient, "login", classmethod(fake_login))
    transport = service.make_transport("in")
    assert calls == [("https://agentswitch.theschoolofai.in", "a@b", "pw")]
    assert transport._client.token == "tok-login"
