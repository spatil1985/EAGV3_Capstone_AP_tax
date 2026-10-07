"""Control-plane authentication (agent_design.md §4.14, S17 auth.py): fail closed.

- `APTAX_CONTROL_TOKEN` unset → 503: the control plane is off, not open.
- Missing or wrong bearer token → 401. Compared with `hmac.compare_digest`.
- The kill switch additionally requires a loopback client (glc routes/control.py).
"""

import hmac
import ipaddress
import os

from aptax.config import CONTROL_TOKEN_ENV


def check_control(authorization: str | None) -> tuple[int, str] | None:
    """None when the bearer token is valid, else (HTTP status, reason)."""
    expected = os.environ.get(CONTROL_TOKEN_ENV, "")
    if not expected:
        return 503, f"control plane disabled: {CONTROL_TOKEN_ENV} is not set"
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return 401, "missing bearer token"
    if not hmac.compare_digest(token.strip().encode(), expected.encode()):
        return 401, "invalid control token"
    return None


def is_loopback(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        return host == "localhost"
    mapped = getattr(ip, "ipv4_mapped", None)
    return ip.is_loopback or bool(mapped and mapped.is_loopback)
