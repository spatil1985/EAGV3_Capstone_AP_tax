"""Composition root: the only module that picks concrete classes and wires a run.

The CLI and the HTTP API call these functions; nothing below them knows which
transport, store or LLM gateway is in use (harness/__main__.py did this job before).

    ask(...)            on_request: governor → session → agent loop → stored answer
    run_playbooks(...)  a deterministic playbook run, no LLM (CLI `run`; the scheduled
                        pipeline reuses it in Phase 3)
    call(...)           one capability through the same validation path the loop uses
    routes(...)         which playbooks would run for this tenant, and why not
    policy_check(...)   the policy verdict for a tool, with no network call

Every entry point that touches AgentSwitch goes through the governor first, so the
kill switch, rate limit and daily windows apply to operator commands too.
"""

import os
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from aptax.agentswitch.fetch import Fetcher
from aptax.agentswitch.gateway import BASE_READ_ALLOWLIST, Gateway
from aptax.agentswitch.policy import CallFacts, PolicyEngine
from aptax.agentswitch.risk import classify
from aptax.agentswitch.transport import LiveTransport, RecordingTransport, ReplayTransport
from aptax.capabilities.builtins import build_registry, playbook_index
from aptax.capabilities.registry import CapabilityError
from aptax.clock import tenant_today
from aptax.config import CONFIG_DIR, TENANTS, load_dotenv
from aptax.context import RunContext, new_run_id
from aptax.playbooks.manifest import load_manifests
from aptax.runtime.agent_loop import AgentLoop, LoopLimits
from aptax.runtime.render import write_run_reports
from aptax.runtime.runner import PlaybookRun, PlaybookRunner
from aptax.runtime.shaping import clip
from aptax.triggers.envelope import ask_envelope, request_envelope
from aptax.triggers.governor import Governor
from aptax.triggers.subscriptions import ASK, MANUAL

POLICY_PATH = CONFIG_DIR / "policy.yaml"
CHARTER_PATH = CONFIG_DIR / "charter.md"


class ServiceError(RuntimeError):
    """A run could not start or a request is invalid (credentials, context, arguments)."""


class Refused(ServiceError):
    """The governor refused the envelope."""

    def __init__(self, control: str, reason: str):
        super().__init__(f"refused by {control}: {reason}")
        self.control = control
        self.reason = reason


def load_charter() -> str:
    try:
        return CHARTER_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise ServiceError(f"charter missing: {CHARTER_PATH}") from exc


def make_transport(tenant: str, *, record: str | None = None, replay: str | None = None):
    """Live by default; --replay serves a recording offline; --record saves one."""
    if replay:
        return ReplayTransport(Path(replay))
    load_dotenv()
    prefix = TENANTS[tenant]
    missing = [f"{prefix}_{k}" for k in ("EMAIL", "PASSWORD") if not os.environ.get(f"{prefix}_{k}")]
    if missing:
        raise ServiceError(f"credentials missing: set {', '.join(missing)} (see .env.example)")
    from scripts.agentswitch_client import AgentSwitchClient
    try:
        live = LiveTransport(AgentSwitchClient.from_env(prefix))
    except Exception as exc:  # noqa: BLE001 — login failures are reported, never retried blindly
        raise ServiceError(f"could not log in to AgentSwitch ({tenant}): {type(exc).__name__}: {exc}") from exc
    return RecordingTransport(live, Path(record)) if record else live


@dataclass
class Session:
    store: object
    gateway: Gateway
    ctx: RunContext
    fetcher: Fetcher
    runner: PlaybookRunner
    registry: object

    @property
    def run_id(self) -> str:
        return self.ctx.run_id


def open_session(store, transport, *, tenant: str, trigger: str, mode: str, dry_run: bool = True,
                 question: str | None = None, allowed_effects=frozenset(), subscription_id: str | None = None,
                 envelope=None, as_of: date | None = None, vertical: str | None = None) -> Session:
    policy = PolicyEngine.load(POLICY_PATH)
    run_id = new_run_id(tenant)
    store.start_run(run_id, tenant=tenant, trigger=trigger, mode=mode, dry_run=dry_run, question=question,
                    subscription_id=subscription_id, envelope=envelope)
    if policy.error:
        store.journal(run_id, "note", {"policy": "deny-everything", "error": policy.error})
    gateway = Gateway(transport, store, policy, run_id=run_id, tenant=tenant, dry_run=dry_run,
                      allowed_effects=allowed_effects)
    try:
        ctx = RunContext.build(gateway, tenant=tenant, trigger=trigger, run_id=run_id,
                               as_of=as_of or tenant_today(tenant), dry_run=dry_run, vertical=vertical)
    except Exception as exc:  # noqa: BLE001 — no context, no run
        store.journal(run_id, "note", {"aborted": f"{type(exc).__name__}: {exc}"})
        store.finish_run(run_id, "failed")
        raise ServiceError(f"run {run_id} aborted: {exc}") from exc
    store.journal(run_id, "context", ctx.summary())
    fetcher = Fetcher(gateway)
    runner = PlaybookRunner(ctx, gateway, fetcher, store, load_manifests())
    registry = build_registry(ctx=ctx, gateway=gateway, fetcher=fetcher, store=store, runner=runner)
    return Session(store, gateway, ctx, fetcher, runner, registry)


def _admit(store, env, sub):
    decision = Governor(store).admit(env, sub)
    if not decision.admitted:
        raise Refused(decision.control, decision.reason)
    return decision


# -- on_request ---------------------------------------------------------------------------

def ask(store, transport_factory, *, tenant: str, question: str, llm, source: str = "user.cli",
        limits: LoopLimits = LoopLimits()) -> dict:
    """Answer one question with the agent loop. Read-only in Phase 1 (dry-run)."""
    question = (question or "").strip()
    if not question:
        raise ServiceError("the question is empty")
    env = ask_envelope(tenant, question, source=source)
    decision = _admit(store, env, ASK)
    session = open_session(store, transport_factory(tenant), tenant=tenant, trigger="on_request", mode="agent",
                           dry_run=True, question=question, allowed_effects=ASK.allowed_side_effects,
                           subscription_id=ASK.id, envelope=env)
    if decision.run_budget_usd is not None:
        limits = replace(limits, run_budget_usd=min(limits.run_budget_usd, decision.run_budget_usd))
    loop = AgentLoop(ctx=session.ctx, registry=session.registry, llm=llm, store=store,
                     available_tools=session.gateway.available_tools(), charter=load_charter(),
                     playbook_index=playbook_index(session.runner), limits=limits,
                     allowed_effects=ASK.allowed_side_effects)
    try:
        result = loop.run(question)
    except Exception:
        store.finish_run(session.run_id, "failed")
        raise
    store.finish_run(session.run_id, result.status, answer_md=result.answer_md, llm_usd=result.usd)
    Governor(store).record_spend(ASK, tenant, result.usd)
    return {"status": result.status, "run_id": session.run_id, "answer_md": result.answer_md,
            "stop_reason": result.stop_reason, "turns": result.turns, "tool_calls": result.tool_calls,
            "usd": result.usd, "gateway": dict(session.gateway.stats)}


# -- operator commands ----------------------------------------------------------------------

def run_playbooks(store, transport_factory, *, tenant: str, playbooks=None, trigger: str = "on_request",
                  cadence: str | None = None, dry_run: bool = True, as_of: date | None = None,
                  vertical: str | None = None) -> dict:
    """Run playbooks deterministically: route → evaluate → fingerprint → digest escalation.

    Escalations are suppressed in dry-run (the default) and recorded as would-be writes.
    """
    env = request_envelope(tenant, "run", {"playbooks": list(playbooks or []), "cadence": cadence})
    _admit(store, env, MANUAL)
    session = open_session(store, transport_factory(tenant), tenant=tenant, trigger=trigger, mode="pipeline",
                           dry_run=dry_run, allowed_effects=MANUAL.allowed_side_effects,
                           subscription_id=MANUAL.id, envelope=env, as_of=as_of, vertical=vertical)
    runner = session.runner
    try:
        if playbooks:
            selected = [runner.get(p) for p in playbooks]
            runs = [runner.run_one(m, escalate=True) for m in selected]
        else:
            runs = [runner.run_one(r.manifest, escalate=True) if r.action == "run" else PlaybookRun(r)
                    for r in runner.routes(trigger=trigger, cadence=cadence)]
    except KeyError as exc:
        store.finish_run(session.run_id, "failed")
        raise ServiceError(str(exc.args[0])) from exc
    stats = dict(session.gateway.stats)
    paths = write_run_reports(session.ctx, runs, stats)
    status = "failed" if any(r.error for r in runs) else "completed"
    store.finish_run(session.run_id, status)
    return {"status": status, "run_id": session.run_id, "ctx": session.ctx, "runs": runs,
            "stats": stats, "paths": paths}


def call(store, transport_factory, *, tenant: str, capability: str, args: dict) -> dict:
    """Run one read or playbook capability exactly as the agent loop would: only if it is
    advertised for this tenant, only with arguments that pass its contract."""
    env = request_envelope(tenant, "call", {"capability": capability[:64]})
    _admit(store, env, MANUAL)
    session = open_session(store, transport_factory(tenant), tenant=tenant, trigger="on_request", mode="call",
                           dry_run=True, subscription_id=MANUAL.id, envelope=env)
    offered = {c.name: c for c in session.registry.advertised(
        session.ctx, available_tools=session.gateway.available_tools())}
    cap = offered.get(capability)
    try:
        if cap is None or cap.kind == "terminal":
            raise ServiceError(f"capability {capability!r} is not offered for tenant {tenant}; "
                               f"offered: {', '.join(sorted(n for n, c in offered.items() if c.kind != 'terminal'))}")
        try:
            clean = cap.validate(args)
            data = clip(cap.worker(clean), chars=cap.result_chars)
        except CapabilityError as exc:
            raise ServiceError(f"invalid arguments: {exc}") from exc
    except Exception as exc:
        store.journal(session.run_id, "capability_call", {"capability": capability, "args": args, "ok": False,
                                                          "error": f"{type(exc).__name__}: {exc}"})
        store.finish_run(session.run_id, "failed")
        raise
    store.journal(session.run_id, "capability_call", {"capability": capability, "args": clean, "ok": True})
    store.finish_run(session.run_id, "completed")
    return {"status": "completed", "run_id": session.run_id, "capability": capability, "result": data,
            "gateway": dict(session.gateway.stats)}


def routes(store, transport_factory, *, tenant: str, trigger: str | None = None,
           cadence: str | None = None, vertical: str | None = None) -> dict:
    env = request_envelope(tenant, "routes", {"trigger": trigger, "cadence": cadence})
    _admit(store, env, MANUAL)
    session = open_session(store, transport_factory(tenant), tenant=tenant, trigger=trigger or "on_request",
                           mode="routes", subscription_id=MANUAL.id, envelope=env, vertical=vertical)
    listed = session.runner.routes(trigger=trigger, cadence=cadence)
    offered = sorted(c.name for c in session.registry.advertised(
        session.ctx, available_tools=session.gateway.available_tools()))
    store.finish_run(session.run_id, "completed")
    return {"run_id": session.run_id, "ctx": session.ctx, "routes": listed, "offered": offered,
            "tools_listed": len(session.gateway.available_tools())}


def policy_check(tool: str, args: dict | None = None) -> dict:
    """What config/policy.yaml says about one call — no network, no run."""
    policy = PolicyEngine.load(POLICY_PATH)
    tier = classify(tool)
    verdict = policy.evaluate(CallFacts(tool=tool, tier=tier, args=dict(args or {}),
                                        allowlisted=tool in BASE_READ_ALLOWLIST))
    return {"tool": tool, "tier": tier.name, "allowed": verdict.allowed, "reason": verdict.reason,
            "rule_index": verdict.rule_index, "policy_error": policy.error}
