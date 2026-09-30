"""Playbook registry and router (harness_plan.md §4.5).

Patterns:
- **Registry** — manifests are data (YAML front matter in playbooks/*.md), loaded once.
  Adding a use case means adding a file, not editing this module.
- **Factory** — `instantiate()` builds the playbook class named by the manifest's
  `compute: module:Class`, so the runner never imports use-case code directly.

The router decides, per manifest, whether it runs *for this RunContext*:
    status × tax_regime × vertical × required locale features × trigger
Everything that doesn't run comes back with a reason, which is how `spec` and
`blocked` use cases stay visible without fabricated data.
"""

import importlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from harness.context import ROOT

PLAYBOOK_DIR = ROOT / "playbooks"


@dataclass(frozen=True)
class Manifest:
    id: str
    title: str
    status: str                      # live | spec | blocked
    compute: str | None
    tax_regimes: tuple = ("all",)
    verticals: tuple = ("all",)
    requires_features: tuple = ()
    triggers: tuple = ()
    tools: tuple = ()
    questions: tuple = ()
    owner: str | None = None
    blocked_by: str | None = None
    escalate: str = "never"          # never | new_findings
    spec: str | None = None
    source: str = ""

    @classmethod
    def from_front_matter(cls, meta: dict, source: Path) -> "Manifest":
        return cls(
            id=meta["id"], title=meta["title"], status=meta.get("status", "spec"),
            compute=meta.get("compute"),
            tax_regimes=tuple(meta.get("tax_regimes") or ("all",)),
            verticals=tuple(meta.get("verticals") or ("all",)),
            requires_features=tuple(meta.get("requires_features") or ()),
            triggers=tuple(tuple(sorted(t.items())) for t in meta.get("triggers") or ()),
            tools=tuple(meta.get("tools") or ()),
            questions=tuple(meta.get("questions") or ()),
            owner=meta.get("owner"), blocked_by=meta.get("blocked_by"),
            escalate=meta.get("escalate", "never"), spec=meta.get("spec"),
            source=str(source.relative_to(ROOT)),
        )

    def has_trigger(self, kind: str, cadence: str | None = None) -> bool:
        for trig in map(dict, self.triggers):
            if trig.get("kind") == kind and (cadence is None or trig.get("cadence") == cadence):
                return True
        return False


def read_front_matter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None           # legacy playbooks without a manifest are ignored
    _, meta, _body = text.split("---", 2)
    return yaml.safe_load(meta)


def load_manifests(directory: Path = PLAYBOOK_DIR) -> list[Manifest]:
    manifests = []
    for path in sorted(directory.glob("*.md")):
        meta = read_front_matter(path)
        if meta:
            manifests.append(Manifest.from_front_matter(meta, path))
    return manifests


@dataclass(frozen=True)
class Route:
    manifest: Manifest
    action: str      # run | skip | spec | blocked
    reason: str = ""


@dataclass
class Registry:
    manifests: list[Manifest] = field(default_factory=load_manifests)

    def get(self, playbook_id: str) -> Manifest:
        for m in self.manifests:
            if m.id == playbook_id:
                return m
        raise KeyError(f"no playbook {playbook_id!r} in {PLAYBOOK_DIR}")

    def route(self, ctx, *, trigger: str, cadence: str | None = None,
              ids: list[str] | None = None) -> list[Route]:
        chosen = [self.get(i) for i in ids] if ids else self.manifests
        return [self._route_one(m, ctx, trigger, cadence, explicit=bool(ids)) for m in chosen]

    @staticmethod
    def _route_one(m: Manifest, ctx, trigger, cadence, explicit) -> Route:
        if m.status == "blocked":
            return Route(m, "blocked", f"blocked by {m.blocked_by}")
        if m.status == "spec":
            return Route(m, "spec", f"not executable — no {'/'.join(m.verticals)} tenant exists")
        if "all" not in m.tax_regimes and ctx.tax_regime not in m.tax_regimes:
            return Route(m, "skip", f"tax_regime {ctx.tax_regime} not in {list(m.tax_regimes)}")
        if "all" not in m.verticals and ctx.vertical not in m.verticals:
            return Route(m, "skip", f"vertical {ctx.vertical} not in {list(m.verticals)}")
        missing = [f for f in m.requires_features if not ctx.features.get(f)]
        if missing:
            return Route(m, "skip", f"locale feature(s) off: {', '.join(missing)}")
        if not explicit and not m.has_trigger(trigger, cadence):
            return Route(m, "skip", f"no {trigger}{'/' + cadence if cadence else ''} trigger")
        return Route(m, "run")

    @staticmethod
    def instantiate(m: Manifest):
        module_name, _, class_name = (m.compute or "").partition(":")
        if not class_name:
            raise ValueError(f"{m.id}: compute must be 'module:Class', got {m.compute!r}")
        playbook = getattr(importlib.import_module(module_name), class_name)()
        playbook.manifest = m
        return playbook
