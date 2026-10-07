"""RunContext — the facts a run is about, fetched once per run, never cached across runs.

Ported from harness/core/context.py (Factory Method `build`) and kept attribute-compatible
with it, so playbooks written for the harness (UC-12) run here unchanged. Additions:
- the vertical comes from **`OrgProfile.industry`** (agent_design.md §1), not a default;
- constants come from the effective-dated **rulebook** (`ctx.rule(name, on=…)`);
- the locale's own `not_yet_supported` list is kept, so the agent can say "documented
  platform gap" instead of guessing.

If the locale can't be read the run aborts: there is no fallback jurisdiction.
"""

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from aptax.config import PLAYBOOK_DIR, RULEBOOK_DIR, RUNS_DIR
from aptax.domain.rules import Rulebook

INDUSTRY_TO_VERTICAL = {
    "manufacturing": "manufacturing", "education": "school", "healthcare": "clinic",
    "retail": "retail", "consulting": "agency", "technology": "agency", "media": "agency",
}


class ContextError(RuntimeError):
    """The run cannot start (e.g. locale unavailable)."""


def new_run_id(tenant: str) -> str:
    return f"{datetime.now().strftime('%Y%m%dT%H%M%S')}-{tenant}-{uuid.uuid4().hex[:6]}"


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
    industry: str | None = None
    org: dict = field(default_factory=dict)
    not_yet_supported: tuple = ()
    rulebook: Rulebook = field(default_factory=Rulebook)
    constants: dict = field(default_factory=dict)
    runs_dir: Path = RUNS_DIR

    @property
    def run_dir(self) -> Path:
        return self.runs_dir / self.run_id

    def rule(self, name: str, on: date | None = None):
        return self.rulebook.rule(name, on or self.as_of)

    def constant(self, name: str):
        """Harness-compatible alias: the rule in force on the run's as-of date."""
        return self.rule(name)

    def summary(self) -> dict:
        return {"tenant": self.tenant, "country": self.country, "tax_regime": self.tax_regime,
                "currency": self.currency, "as_of": str(self.as_of), "period": self.period,
                "vertical": self.vertical, "vertical_source": self.vertical_source,
                "industry": self.industry, "company_id": self.company_id,
                "features_on": sorted(k for k, v in self.features.items() if v),
                "not_yet_supported": list(self.not_yet_supported),
                "dry_run": self.dry_run}

    @classmethod
    def build(cls, gateway, *, tenant: str, trigger: str, run_id: str, as_of: date | None = None,
              dry_run: bool = True, vertical: str | None = None) -> "RunContext":
        me = gateway.rest("GET", "/api/auth/me")
        try:
            body = gateway.rest("GET", "/api/accounting/locale")
            locale = body.get("locale", body)
        except Exception as exc:  # noqa: BLE001 — any failure aborts the run
            raise ContextError(f"locale unavailable, refusing to guess a jurisdiction: {exc}") from exc
        if not locale.get("tax_regime"):
            raise ContextError("locale has no tax_regime")

        org = {}
        result = gateway.call_tool("OrgProfile.list", {"limit": 1})
        if result.ok and isinstance(result.data, dict) and result.data.get("data"):
            raw = result.data["data"][0]
            org = {k: raw.get(k) for k in ("industry", "gstin", "pan", "tan", "state", "msme_type",
                                           "enable_tds", "enable_e_invoicing", "report_basis")}
        industry = org.get("industry")
        if vertical:
            chosen, source = vertical, "override"
        elif industry:
            chosen, source = INDUSTRY_TO_VERTICAL.get(industry, "other"), "OrgProfile.industry"
        else:
            chosen, source = "manufacturing", "default (OrgProfile unreadable)"

        as_of = as_of or date.today()
        book = Rulebook.load(PLAYBOOK_DIR / "constants.yaml", RULEBOOK_DIR)
        nys = tuple(item.get("key") for item in locale.get("not_yet_supported") or []
                    if isinstance(item, dict) and item.get("key"))
        return cls(
            run_id=run_id, tenant=tenant, trigger=trigger, as_of=as_of, period=as_of.strftime("%Y-%m"),
            dry_run=dry_run, company_id=me.get("company_id") or locale.get("company_id") or "",
            user_email=me.get("email", ""), roles=tuple(me.get("roles", ())),
            country=locale.get("country", ""), tax_regime=locale["tax_regime"],
            currency=locale.get("base_currency", "INR"), features=dict(locale.get("features", {})),
            vertical=chosen, vertical_source=source, industry=industry, org=org,
            not_yet_supported=nys, rulebook=book, constants=book.flat(as_of))
