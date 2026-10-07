"""Agent loop for on_request (agent_design.md §4.6): a hand-written tool-calling loop.

It depends only on the LLMGateway protocol (aptax/llm/contract.py) — no provider SDK,
no agent framework. Limits are adapted from S17 planner.py:

    ≤ 8 model turns · ≤ 24 capability calls · ≤ 4 calls taken from one turn
    ≤ 3 repairs of invalid calls · stop when the same call has failed 4 times
    20% of the run budget kept for submit_answer · 1 corrective round for the evidence check

One turn: the model proposes calls → each is checked against the advertised set (the
authority boundary) and its argument contract → a repeat of a call that already
succeeded is answered with the earlier evidence id → the batch runs concurrently (the
transport's semaphore caps MCP traffic) → each result is clipped and given an evidence
id. The run ends only through submit_answer and the deterministic evidence check
(evidence.py). A failed check gets one corrective round; after that the answer ships
marked unverified, with the offending numbers listed.

Every model turn, capability call and evidence check is journaled (append-only).
"""

import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field

from aptax.capabilities.builtins import SUBMIT_ANSWER
from aptax.capabilities.registry import CapabilityError
from aptax.llm.contract import BudgetRefused
from aptax.runtime.evidence import EvidenceLedger, check_answer, parse_answer
from aptax.runtime.render import render_answer, render_stopped
from aptax.runtime.shaping import clip

MAX_CHARTER_CHARS = 12_000     # S17 skills/manager.py MAX_INJECTED_CHARS

FINISH_NOW = ("## Finish now\nThis run's call or budget limit is reached. Call submit_answer with what the "
              "evidence already gathered supports, and say in the caveats what could not be checked.")
NEED_SUBMIT = ("Finish by calling submit_answer: one section per part of the question, each citing the "
               "evidence ids its numbers come from. A plain-text reply is not accepted as an answer.")
FIX_EVIDENCE = ("The evidence check rejected this answer. Fix exactly the problems listed and call "
                "submit_answer again: cite the evidence id that contains each number, or remove the "
                "number. Do not compute new numbers; the capabilities return the totals.")


@dataclass(frozen=True)
class LoopLimits:
    max_turns: int = 8
    max_tool_calls: int = 24
    max_calls_per_turn: int = 4
    max_repairs: int = 3
    max_same_failures: int = 4
    max_corrections: int = 1
    max_tokens: int = 2048
    run_budget_usd: float = 0.05
    reserve_fraction: float = 0.20


@dataclass
class LoopResult:
    status: str                       # completed | unverified | failed
    answer_md: str
    stop_reason: str
    turns: int = 0
    tool_calls: int = 0
    usd: float = 0.0
    sections: list = field(default_factory=list)
    caveats: list = field(default_factory=list)
    check: dict | None = None


def call_key(name: str, args: dict) -> str:
    return name + ":" + json.dumps(args, sort_keys=True, separators=(",", ":"), default=str)


class AgentLoop:
    def __init__(self, *, ctx, registry, llm, store, available_tools, charter: str, playbook_index: str,
                 limits: LoopLimits = LoopLimits(), allowed_effects=frozenset()):
        self.ctx = ctx
        self.registry = registry
        self.llm = llm
        self.store = store
        self.limits = limits
        self.charter = charter
        self.playbook_index = playbook_index
        self.offered = {c.name: c for c in registry.advertised(
            ctx, allowed_effects=allowed_effects, available_tools=available_tools)}
        self.ledger = EvidenceLedger()
        self.turns = self.calls = self.repairs = self.corrections = 0
        self.usd = 0.0
        self.failures: Counter = Counter()
        self.succeeded: dict[str, str] = {}          # call key → evidence id
        self.last_answer = None                      # (sections, caveats, report) rejected once

    # -- the loop ---------------------------------------------------------------------

    def run(self, question: str) -> LoopResult:
        limits = self.limits
        self._journal("loop_start", {"question": question, "offered": sorted(self.offered),
                                     "limits": asdict(limits)})
        messages = [{"role": "user", "content": question}]
        while self.turns < limits.max_turns:
            self.turns += 1
            if self.usd >= limits.run_budget_usd:
                return self._stop(question, "the run's LLM budget is spent")
            finishing = self._finishing()
            tools = [self.offered[SUBMIT_ANSWER]] if finishing else list(self.offered.values())
            try:
                reply = self.llm.complete(system=self._system(finishing), messages=messages,
                                          tools=[c.spec() for c in tools], role="planner",
                                          run_id=self.ctx.run_id, max_tokens=limits.max_tokens)
            except BudgetRefused as exc:
                self._journal("model_refused", {"turn": self.turns, "reason": str(exc), "detail": exc.detail})
                return self._stop(question, f"the LLM gateway refused the call: {exc}")
            except Exception as exc:  # noqa: BLE001 — a plugged-in gateway may raise anything
                self._journal("model_error", {"turn": self.turns, "error": f"{type(exc).__name__}: {exc}"})
                return self._stop(question, f"LLM error: {type(exc).__name__}: {exc}")
            self._meter(reply)

            assistant = {"role": "assistant", "content": reply.content or ""}
            if reply.tool_calls:
                assistant["tool_calls"] = [tc.as_message_part() for tc in reply.tool_calls]
            messages.append(assistant)
            if not reply.tool_calls:
                if not self._repair("reply without a tool call"):
                    return self._stop(question, "the model did not call submit_answer", text=reply.content)
                messages.append({"role": "user", "content": NEED_SUBMIT})
                continue
            result = self._turn(reply.tool_calls, question, messages)
            if result is not None:
                return result
        return self._stop(question, f"no accepted submit_answer within {limits.max_turns} turns")

    def _finishing(self) -> bool:
        limits = self.limits
        return (self.turns >= limits.max_turns or self.calls >= limits.max_tool_calls
                or self.usd >= limits.run_budget_usd * (1 - limits.reserve_fraction))

    def _system(self, finishing: bool) -> str:
        parts = [self.charter[:MAX_CHARTER_CHARS],
                 "## Playbooks\n" + self.playbook_index,
                 "## Run context\n```json\n" + json.dumps(self.ctx.summary(), indent=1, default=str) + "\n```"]
        if finishing:
            parts.append(FINISH_NOW)
        return "\n\n".join(parts)

    # -- one turn ---------------------------------------------------------------------

    def _turn(self, calls, question: str, messages: list) -> LoopResult | None:
        limits = self.limits
        replies: dict[str, dict] = {}
        submit = next((c for c in calls if c.name == SUBMIT_ANSWER), None)
        if submit is not None:
            for c in calls:
                if c is not submit:
                    replies[c.id] = {"error": "skipped: submit_answer ends the run, so it must be the only call in its turn"}
            outcome, replies[submit.id] = self._submit(submit, question)
            self._reply(calls, replies, messages)
            return outcome

        batch, pending = [], set()
        for i, c in enumerate(calls):
            if i >= limits.max_calls_per_turn:
                replies[c.id] = {"error": f"dropped: at most {limits.max_calls_per_turn} calls are taken from one turn"}
                continue
            admitted = self._admit(c, pending)
            if isinstance(admitted, dict):
                replies[c.id] = admitted
            else:
                batch.append(admitted)
                pending.add(admitted[3])
        if self.repairs > limits.max_repairs:
            replies.update({c.id: {"error": "not run: too many invalid calls"} for c, *_ in batch})
            self._reply(calls, replies, messages)
            return self._stop(question, "too many invalid capability calls")

        stop_reason = None
        if batch:
            with ThreadPoolExecutor(max_workers=limits.max_calls_per_turn) as pool:
                outcomes = list(pool.map(self._execute, batch))
            for (c, cap, args, key), (ok, data, error, ms) in zip(batch, outcomes):
                self.calls += 1
                if ok:
                    eid = self.ledger.add(cap.name, args, data)
                    self.succeeded[key] = eid
                    replies[c.id] = {"evidence_id": eid, "result": data}
                else:
                    self.failures[key] += 1
                    replies[c.id] = {"error": error}
                    if error.startswith("invalid arguments"):
                        self._repair(f"{cap.name}: {error}")
                    if self.failures[key] >= limits.max_same_failures:
                        stop_reason = f"{cap.name} failed {self.failures[key]} times with the same arguments"
                self._journal("capability_call", {"turn": self.turns, "capability": cap.name, "args": args,
                                                  "ok": ok, "ms": ms, "evidence_id": replies[c.id].get("evidence_id"),
                                                  "error": error})
        self._reply(calls, replies, messages)
        if stop_reason:
            return self._stop(question, stop_reason)
        if self.repairs > limits.max_repairs:
            return self._stop(question, "too many invalid capability calls")
        return None

    def _admit(self, call, pending: set):
        """(call, capability, clean args, key) to run, or the error dict to reply with."""
        if call.name not in self.offered:
            self._repair(f"capability {call.name!r} not offered")
            why = "is not offered in this run" if call.name in self.registry else "does not exist"
            return {"error": f"capability {call.name!r} {why}; use one of the tools provided"}
        cap = self.offered[call.name]
        try:
            args = cap.validate(call.arguments)
        except CapabilityError as exc:
            self._repair(f"invalid arguments for {call.name}")
            return {"error": f"invalid arguments: {exc}"}
        key = call_key(call.name, args)
        if key in self.succeeded:
            return {"evidence_id": self.succeeded[key],
                    "note": "this exact call was already answered in this run; reuse that evidence"}
        if key in pending:
            return {"error": "duplicate of another call in this turn"}
        if self.calls + len(pending) >= self.limits.max_tool_calls:
            return {"error": "the run's capability-call limit is reached; call submit_answer"}
        return call, cap, args, key

    @staticmethod
    def _execute(item):
        _call, cap, args, _key = item
        started = time.monotonic()
        try:
            data = clip(cap.worker(args), chars=cap.result_chars)
            ok, error = True, None
        except CapabilityError as exc:
            data, ok, error = None, False, f"invalid arguments: {exc}"
        except Exception as exc:  # noqa: BLE001 — a failing capability is reported to the model
            data, ok, error = None, False, f"{type(exc).__name__}: {exc}"
        return ok, data, error, int((time.monotonic() - started) * 1000)

    def _submit(self, call, question: str):
        """(LoopResult or None to continue, the reply for the submit call)."""
        try:
            sections, caveats = parse_answer(self.offered[SUBMIT_ANSWER].validate(call.arguments))
        except CapabilityError as exc:
            if not self._repair("invalid submit_answer"):
                return self._stop(question, "submit_answer was malformed too many times"), {"error": str(exc)}
            return None, {"error": f"invalid submit_answer: {exc}"}
        report = check_answer(sections, self.ledger, question=question)
        self._journal("answer_check", {"turn": self.turns, **report.as_dict()})
        if report.ok:
            return self._finish("completed", question, sections, caveats, report), {"accepted": True}
        if self.corrections < self.limits.max_corrections and self.turns < self.limits.max_turns:
            self.corrections += 1
            self.last_answer = (sections, caveats, report)
            return None, {"error": FIX_EVIDENCE, "problems": report.problems}
        return (self._finish("unverified", question, sections, caveats, report),
                {"accepted": True, "status": "unverified"})

    def _reply(self, calls, replies: dict, messages: list) -> None:
        for c in calls:
            payload = replies.get(c.id, {"error": "not run"})
            messages.append({"role": "tool", "tool_call_id": c.id, "name": c.name,
                             "content": json.dumps(payload, ensure_ascii=False, default=str)})

    # -- bookkeeping ------------------------------------------------------------------

    def _journal(self, kind: str, payload: dict) -> None:
        self.store.journal(self.ctx.run_id, kind, payload)

    def _repair(self, why: str) -> bool:
        self.repairs += 1
        self._journal("repair", {"turn": self.turns, "n": self.repairs, "why": why})
        return self.repairs <= self.limits.max_repairs

    def _meter(self, reply) -> None:
        usage = reply.usage
        self.usd += float(usage.usd or 0.0)
        self.store.record_llm_call(run_id=self.ctx.run_id, role="planner", provider=reply.provider,
                                   model=reply.model, input_tokens=usage.input_tokens,
                                   output_tokens=usage.output_tokens, cache_tokens=usage.cache_tokens,
                                   usd=float(usage.usd or 0.0), latency_ms=usage.latency_ms)
        self._journal("model_turn", {
            "turn": self.turns, "provider": reply.provider, "model": reply.model,
            "stop_reason": reply.stop_reason, "text": (reply.content or "")[:4_000],
            "calls": [{"id": c.id, "name": c.name, "arguments": c.arguments} for c in reply.tool_calls],
            "usage": asdict(usage)})

    def _stats(self) -> dict:
        return {"turns": self.turns, "tool_calls": self.calls, "usd": self.usd,
                "repairs": self.repairs, "corrections": self.corrections}

    def _finish(self, status: str, question: str, sections, caveats, report) -> LoopResult:
        answer = render_answer(ctx=self.ctx, question=question, sections=sections, caveats=caveats,
                               ledger=self.ledger, report=report, stats=self._stats())
        self._journal("loop_end", {"status": status, **self._stats()})
        return LoopResult(status, answer, "submit_answer", self.turns, self.calls, self.usd,
                          sections=[asdict(s) for s in sections], caveats=caveats, check=report.as_dict())

    def _stop(self, question: str, reason: str, text: str | None = None) -> LoopResult:
        if self.last_answer:
            # A rejected answer exists: ship it marked unverified rather than nothing.
            sections, caveats, report = self.last_answer
            report.problems.append(f"no corrected answer followed: {reason}")
            result = self._finish("unverified", question, sections, caveats, report)
            result.stop_reason = reason
            return result
        answer = render_stopped(ctx=self.ctx, question=question, reason=reason, ledger=self.ledger,
                                stats=self._stats(), text=text)
        self._journal("loop_end", {"status": "failed", "reason": reason, **self._stats()})
        return LoopResult("failed", answer, reason, self.turns, self.calls, self.usd)
