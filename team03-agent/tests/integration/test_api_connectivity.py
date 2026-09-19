"""Live smoke test: is the AgentSwitch REST API reachable and is login valid?

Skipped unless AGENTSWITCH_EMAIL / AGENTSWITCH_PASSWORD are set -- see
tests/integration/conftest.py.
"""

import requests


def test_login_and_whoami_matches_our_account(client, credentials):
    email, _password = credentials
    me = client.whoami()
    assert me.get("email") == email


def test_locale_endpoint_is_reachable(client):
    # SKILL.md's "Dynamic Locale" rule depends on this endpoint responding
    # with something the agent can branch on (IN vs US). We don't assert on
    # the exact schema here, just that it's reachable and returns data.
    locale = client.get_locale()
    assert isinstance(locale, dict)
    assert locale


def test_unauthenticated_request_is_rejected(base_url):
    # Sanity check on the sanity check: prove the API actually enforces auth,
    # rather than every endpoint just happening to return 200.
    response = requests.get(f"{base_url}/api/auth/me", timeout=30)
    assert response.status_code == 401
