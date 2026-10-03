"""RunContext — the facts a run is about, fetched once, never cached across runs.

Pattern: **Factory Method** (`RunContext.build`). Construction needs two live calls
(whoami, locale) plus config; callers get a finished, immutable object and cannot
build a half-initialised one. Playbooks read regime, currency, dates and constants
from here — never `if company == "Suryodaya"` (harness_plan.md §1 principle 4).
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # harness/core/context.py -> team03-agent/
CONSTANTS_FILE = ROOT / "playbooks" / "constants.yaml"


class ContextError(RuntimeError):
    """The run cannot start — e.g. locale unavailable. There is no fallback jurisdiction."""


def load_constants(path: Path = CONSTANTS_FILE) -> dict:
    """{name: value} from constants.yaml; each entry also carries its statutory source."""
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {name: entry["value"] for name, entry in raw.items()}


@dataclass(frozen=True)
class RunContext:
    run_id: str
    tenant: str
    trigger: str
    as_of: date
    period: str
    dry_run: bool
    company_id: str
    user_email: str
    roles: tuple
    country: str
    tax_regime: str
    currency: str
    features: dict
    vertical: str
    vertical_source: str
    constants: dict = field(default_factory=dict)
    runs_dir: Path = ROOT / "runs"

    @property
    def run_dir(self) -> Path:
        return self.runs_dir / self.run_id

    def constant(self, name: str):
        if name not in self.constants:
            raise KeyError(f"constant {name!r} missing from playbooks/constants.yaml")
        return self.constants[name]

    @classmethod
    def build(cls, transport, *, tenant: str, trigger: str, as_of: date | None = None,
              dry_run: bool = True, vertical: str | None = None,
              runs_dir: Path | None = None) -> "RunContext":
        me = transport.rest_get("/api/auth/me")
        try:
            locale = transport.rest_get("/api/accounting/locale")["locale"]
        except Exception as exc:  # noqa: BLE001 — any failure here aborts the run
            raise ContextError(f"locale unavailable, refusing to guess a jurisdiction: {exc}") from exc
        if not locale.get("tax_regime"):
            raise ContextError("locale has no tax_regime")

        as_of = as_of or date.today()
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        return cls(
            run_id=f"{stamp}-{tenant}-{uuid.uuid4().hex[:6]}",
            tenant=tenant,
            trigger=trigger,
            as_of=as_of,
            period=as_of.strftime("%Y-%m"),
            dry_run=dry_run,
            company_id=me.get("company_id", ""),
            user_email=me.get("email", ""),
            roles=tuple(me.get("roles", ())),
            country=locale.get("country", ""),
            tax_regime=locale["tax_regime"],
            currency=locale.get("base_currency", "INR"),
            features=dict(locale.get("features", {})),
            # scripts/vertical.py (Item-mix detection) is Phase 0 work; until then both
            # live tenants are manufacturing, and the source says so.
            vertical=vertical or "manufacturing",
            vertical_source="cli" if vertical else "default",
            constants=load_constants(),
            runs_dir=runs_dir or ROOT / "runs",
        )
