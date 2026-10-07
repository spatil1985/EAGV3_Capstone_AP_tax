"""Paths, tenants and environment — the only module that knows where things live.

Credentials are read from the process environment. `load_dotenv()` fills missing
variables from team03-agent/.env (gitignored) so a developer doesn't have to export
them by hand. Values are never printed or journaled.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # team03-agent/
CONFIG_DIR = ROOT / "config"
PLAYBOOK_DIR = ROOT / "playbooks"
RULEBOOK_DIR = ROOT / "rulebook"
RUNS_DIR = ROOT / "runs"                             # gitignored: live business data
DB_PATH = RUNS_DIR / "aptax.sqlite"

# Tenant → environment-variable prefix (agent_design.md §4.2). The same email logs in
# to both instances with a different password, so each tenant has its own prefix.
TENANTS = {"in": "AGENTSWITCH", "us": "US_AGENTSWITCH"}
TENANT_TIMEZONES = {"in": "Asia/Kolkata", "us": "America/New_York"}

# Identities this agent acts as. Events caused by them are refused (self-trigger).
SELF_ACTORS_ENV = "APTAX_SELF_ACTORS"
CONTROL_TOKEN_ENV = "APTAX_CONTROL_TOKEN"
LLM_ENV = "APTAX_LLM"
KILL_FILE = CONFIG_DIR / "kill"


def load_dotenv(path: Path = ROOT / ".env") -> int:
    """Set variables from a KEY=VALUE file without overwriting the environment.

    Returns how many variables were set. Comments and blank lines are skipped;
    surrounding quotes are removed. Nothing is logged.
    """
    if not path.exists():
        return 0
    loaded = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


def self_actors() -> set[str]:
    """Our own identities: configured list plus each tenant's login email."""
    actors = {a.strip() for a in os.environ.get(SELF_ACTORS_ENV, "").split(",") if a.strip()}
    for prefix in TENANTS.values():
        email = os.environ.get(f"{prefix}_EMAIL")
        if email:
            actors.add(email)
    return actors or {"aptax"}


def kill_switch_on() -> bool:
    """Out-of-band stop (glc routes/control.py idea): a file, so it works with the API down."""
    return KILL_FILE.exists() or os.environ.get("APTAX_KILL") == "1"
