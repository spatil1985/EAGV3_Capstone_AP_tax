"""Playbook manifests and routing (agent_design.md §4.8, §4.12).

Manifests are YAML front matter in playbooks/*.md — the format the harness already uses
— plus optional fields this agent adds:

    capability: eway_coverage        # the name the LLM sees (default: id with '-' → '_')
    description: "..."               # what the LLM reads when choosing tools
    requires:                        # G1 — what must be true for this playbook to run
      tools: [EWayBill.list]         #   checked against the live tools/list
      features: [eway_bill]          #   locale feature flags
      verticals: [manufacturing]     #   from OrgProfile.industry
    escalate: digest                 # digest | per_finding | never (legacy new_findings = digest)

Legacy `requires_features` and `verticals` keep working. The markdown body after the
front matter is the SOP text the agent loads with `load_playbook`.

Routing answers, per manifest and run: run | skip | spec | blocked, always with a reason.
A playbook whose tools are absent from tools/list is not runnable (S17: "a capability
with no configuration behind it is a lie in the manifest").
"""

import importlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from aptax.config import PLAYBOOK_DIR, ROOT

MAX_SOP_CHARS = 12_000      # S17 skills/manager.py MAX_INJECTED_CHARS


@dataclass(frozen=True)
class Requires:
    tools: tuple = ()
    features: tuple = ()
    verticals: tuple = ("all",)


@dataclass(frozen=True)
class Manifest:
    id: str
    title: str
    status: str
    capability: str
    description: str
    compute: str | None
    questions: tuple
    tax_regimes: tuple
    requires: Requires
    triggers: tuple
    tools: tuple
    escalate: str
    blocked_by: str | None
    spec: str | None
    source: str
    body: str

    def has_trigger(self, kind: str, cadence: str | None = None) -> bool:
        for trig in self.triggers:
            if trig.get("kind") == kind and (cadence is None or trig.get("cadence") == cadence):
                return True
        return False

    def sop(self) -> str:
        text = self.body.strip()
        return text if len(text) <= MAX_SOP_CHARS else text[:MAX_SOP_CHARS] + "\n…(truncated)"


def _split(path: Path) -> tuple[dict | None, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    _, meta, body = text.split("---", 2)
    return yaml.safe_load(meta) or {}, body


def from_front_matter(meta: dict, body: str, source: Path) -> Manifest:
    req = meta.get("requires") or {}
    escalate = meta.get("escalate", "never")
    escalate = "digest" if escalate == "new_findings" else escalate
    title = meta["title"]
    return Manifest(
        id=meta["id"], title=title, status=meta.get("status", "spec"),
        capability=meta.get("capability") or meta["id"].replace("-", "_"),
        description=meta.get("description") or f"{title}. Answers: " + "; ".join(meta.get("questions") or []),
        compute=meta.get("compute"),
        questions=tuple(meta.get("questions") or ()),
        tax_regimes=tuple(meta.get("tax_regimes") or ("all",)),
        requires=Requires(
            tools=tuple(req.get("tools") or meta.get("tools") or ()),
            features=tuple(req.get("features") or meta.get("requires_features") or ()),
            verticals=tuple(req.get("verticals") or meta.get("verticals") or ("all",))),
        triggers=tuple(dict(t) for t in meta.get("triggers") or ()),
        tools=tuple(meta.get("tools") or ()),
        escalate=escalate, blocked_by=meta.get("blocked_by"), spec=meta.get("spec"),
        source=str(source.relative_to(ROOT)), body=body)


def load_manifests(directory: Path = PLAYBOOK_DIR) -> list[Manifest]:
    manifests = []
    for path in sorted(Path(directory).glob("*.md")):
        meta, body = _split(path)
        if meta and meta.get("id"):
            manifests.append(from_front_matter(meta, body, path))
    return manifests


@dataclass(frozen=True)
class Route:
    manifest: Manifest
    action: str        # run | skip | spec | blocked
    reason: str = ""


def route(m: Manifest, ctx, *, available_tools: set[str], trigger: str | None = None,
          cadence: str | None = None) -> Route:
    if m.status == "blocked":
        return Route(m, "blocked", f"blocked by {m.blocked_by or 'a platform gap'}")
    if m.status == "spec":
        return Route(m, "spec", f"spec only — no {'/'.join(m.requires.verticals)} tenant or data yet")
    if "all" not in m.tax_regimes and ctx.tax_regime not in m.tax_regimes:
        return Route(m, "skip", f"tax_regime {ctx.tax_regime} not in {list(m.tax_regimes)}")
    if "all" not in m.requires.verticals and ctx.vertical not in m.requires.verticals:
        return Route(m, "skip", f"vertical {ctx.vertical} not in {list(m.requires.verticals)}")
    off = [f for f in m.requires.features if not ctx.features.get(f)]
    if off:
        return Route(m, "skip", f"locale feature(s) off: {', '.join(off)}")
    if available_tools:
        missing = [t for t in m.requires.tools if t not in available_tools]
        if missing:
            return Route(m, "blocked", f"tool(s) not exposed to our role: {', '.join(missing)}")
    if trigger and not m.has_trigger(trigger, cadence):
        return Route(m, "skip", f"no {trigger}{'/' + cadence if cadence else ''} trigger")
    return Route(m, "run")


def instantiate(m: Manifest):
    module_name, _, class_name = (m.compute or "").partition(":")
    if not class_name:
        raise ValueError(f"{m.id}: compute must be 'module:Class', got {m.compute!r}")
    playbook = getattr(importlib.import_module(module_name), class_name)()
    playbook.manifest = m
    return playbook
