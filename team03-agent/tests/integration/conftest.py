"""Fixtures for live connectivity tests against the real AgentSwitch instance.

These hit the network and need real credentials, so every test here is
SKIPPED (not failed) when AGENTSWITCH_EMAIL / AGENTSWITCH_PASSWORD are not
set. Never hardcode seat credentials in this repo -- per the instructor's
note, every write is attributed to whoever is signed in, and passwords are
"yours alone."

Usage (Suryodaya / India, the default):
    export AGENTSWITCH_EMAIL=teamNN@theschoolofai.in
    export AGENTSWITCH_PASSWORD=...
    pytest tests/integration -v

Keystone (US):
    export AGENTSWITCH_BASE_URL=https://class.agentswitch.theschoolofai.in
"""

import os

import pytest

from scripts.agentswitch_client import AgentSwitchClient, DEFAULT_BASE_URL

REQUIRED_ENV = ("AGENTSWITCH_EMAIL", "AGENTSWITCH_PASSWORD")


def _missing_env() -> list:
    return [name for name in REQUIRED_ENV if not os.environ.get(name)]


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("AGENTSWITCH_BASE_URL", DEFAULT_BASE_URL)


@pytest.fixture(scope="session")
def credentials() -> tuple:
    missing = _missing_env()
    if missing:
        pytest.skip(f"Set {', '.join(missing)} to run live AgentSwitch integration tests")
    return os.environ["AGENTSWITCH_EMAIL"], os.environ["AGENTSWITCH_PASSWORD"]


@pytest.fixture(scope="session")
def client(base_url, credentials) -> AgentSwitchClient:
    email, password = credentials
    return AgentSwitchClient.login(base_url, email, password)
