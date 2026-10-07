"""Write actions behind an idempotency outbox (agent_design.md §4.7, S17 events/outbox.py).

Every write the agent makes on the shared ledger goes through `Actions._write`:

- key = sha256(run_id, step, tool, canonical args);
- a **completed** key returns its stored receipt (no second write);
- a key left **started** by a crash is *not* re-sent: it is reported as needing
  reconciliation, because the first attempt may have reached AgentSwitch;
- dry-run writes are recorded as **suppressed** by the gateway and never sent.

`AgentEscalation.create` requires a `session_id` (Phase 0 finding, 2026-10-03), so the
first escalating action in a run creates one `AgentSession` and reuses it.
"""

import hashlib
import json
from decimal import Decimal

from aptax.domain.contracts import fmt


def _key(run_id: str, step: str, tool: str, args: dict) -> str:
    body = json.dumps([run_id, step, tool, args], sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode()).hexdigest()


class Actions:
    def __init__(self, ctx, gateway, store):
        self.ctx = ctx
        self.gw = gateway
        self.store = store
        self._session_id: str | None = None

    def _write(self, step: str, tool: str, args: dict, *, effect: str) -> dict:
        key = _key(self.ctx.run_id, step, tool, args)
        prior = self.store.outbox_get(key)
        if prior:
            if prior["status"] == "completed":
                return {"ok": True, "data": prior["receipt"], "reused": True}
            if prior["status"] == "started":
                self.store.journal(self.ctx.run_id, "note", {"outbox": "reconcile", "key": key, "tool": tool})
                return {"ok": False, "uncertain": True,
                        "error": "an earlier attempt may have been sent; reconcile before retrying"}
        self.store.outbox_set(key, self.ctx.run_id, tool, "started")
        result = self.gw.call_tool(tool, args, effect=effect)
        if result.ok and isinstance(result.data, dict) and result.data.get("suppressed"):
            self.store.outbox_set(key, self.ctx.run_id, tool, "suppressed", receipt=result.data)
        elif result.ok:
            self.store.outbox_set(key, self.ctx.run_id, tool, "completed", receipt=result.data)
        else:
            self.store.outbox_set(key, self.ctx.run_id, tool, "failed", error=result.error)
        return {"ok": result.ok, "data": result.data, "error": result.error}

    def ensure_session(self) -> str | None:
        if self._session_id:
            return self._session_id
        out = self._write("session", "AgentSession.create",
                          {"channel": "api", "actor_kind": "system"}, effect="escalate")
        data = out.get("data") or {}
        if out["ok"] and not data.get("suppressed"):
            self._session_id = data.get("id")
            if self._session_id:
                self.store.set_run_session(self.ctx.run_id, self._session_id)
        elif data.get("suppressed"):
            self._session_id = "dry-run-session"
        return self._session_id

    def escalate_digest(self, manifest, summary: str, new_findings: list) -> dict | None:
        """One escalation per playbook per run, listing the NEW findings (G8 digest)."""
        if not new_findings:
            return None
        session_id = self.ensure_session()
        if not session_id:
            return {"ok": False, "error": "could not create an AgentSession for the escalation"}
        total = sum((f.total_exposure for f in new_findings), Decimal("0"))
        ranked = sorted(new_findings, key=lambda f: f.total_exposure, reverse=True)
        lines = [summary, "", f"{len(new_findings)} new finding(s), exposure {fmt(total, self.ctx.currency)}, "
                 f"run {self.ctx.run_id}. Top items:"]
        lines += [f"- [{f.rule}] {f.entity_ref}: {f.summary}" for f in ranked[:10]]
        if len(ranked) > 10:
            lines.append(f"- … {len(ranked) - 10} more in runs/{self.ctx.run_id}/report.json")
        args = {"session_id": session_id, "company_id": self.ctx.company_id,
                "subject": f"[{manifest.id.upper()}] {len(new_findings)} new: {manifest.title}"[:200],
                "reason": "\n".join(lines), "reason_code": "other"}
        return self._write(f"escalate:{manifest.id}", "AgentEscalation.create", args, effect="escalate")
