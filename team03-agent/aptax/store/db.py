"""SQLite store (agent_design.md §4.13): one file, safe across threads and restarts.

The agent loop runs tool calls on a thread pool, so every write takes one lock and
commits immediately (autocommit). Reads use the same connection; SQLite in WAL mode
handles a reader and a writer without blocking.

The journal is append-only at the database level (triggers in schema.sql), the way
glc_v5 keeps its audit log: there is no update or delete method here at all.
"""

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _dumps(value) -> str:
    return json.dumps(value, default=str, ensure_ascii=False, sort_keys=True)


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA.read_text(encoding="utf-8"))

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def _exec(self, sql: str, params=()) -> sqlite3.Cursor:
        with self._lock:
            return self._db.execute(sql, params)

    def _rows(self, sql: str, params=()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._db.execute(sql, params).fetchall()]

    # -- envelopes, decisions, refusals ------------------------------------------

    def ingest_envelope(self, env) -> bool:
        """Store an envelope; False if (source, id) was already seen (a duplicate)."""
        try:
            self._exec(
                "INSERT INTO envelopes (source, id, type, tenant, trust, actor, subject, "
                "occurred_at, observed_at, data_json) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (env.source, env.id, env.type, env.tenant, env.trust, env.actor, env.subject,
                 env.occurred_at, env.observed_at, _dumps(env.data)))
            return True
        except sqlite3.IntegrityError:
            return False

    def set_admitted(self, source: str, envelope_id: str, admitted: bool) -> None:
        self._exec("UPDATE envelopes SET admitted=? WHERE source=? AND id=?",
                   (int(admitted), source, envelope_id))

    def count_recent_envelopes(self, source: str, since_iso: str) -> int:
        row = self._rows("SELECT COUNT(*) AS n FROM envelopes WHERE source=? AND observed_at>=?",
                         (source, since_iso))
        return row[0]["n"]

    def add_decision(self, source, envelope_id, subscription_id, decision, reason="") -> None:
        self._exec("INSERT INTO decisions (ts, source, envelope_id, subscription_id, decision, reason) "
                   "VALUES (?,?,?,?,?,?)", (now_iso(), source, envelope_id, subscription_id, decision, reason))

    def add_refusal(self, control, reason, *, source=None, envelope_id=None,
                    subscription_id=None, detail=None) -> None:
        self._exec("INSERT INTO refusals (ts, control, reason, source, envelope_id, subscription_id, "
                   "detail_json) VALUES (?,?,?,?,?,?,?)",
                   (now_iso(), control, reason, source, envelope_id, subscription_id, _dumps(detail or {})))

    def refusals(self, since_iso: str = "") -> list[dict]:
        return self._rows("SELECT * FROM refusals WHERE ts>=? ORDER BY seq", (since_iso,))

    # -- governor windows ----------------------------------------------------------

    def window_reserve(self, subscription_id: str, day: str, kind: str,
                       limit: int | None) -> tuple[bool, int]:
        """Atomically claim one slot in a daily window (S17 window_reserve)."""
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                row = self._db.execute(
                    "SELECT count FROM governor_windows WHERE subscription_id=? AND day=? AND kind=?",
                    (subscription_id, day, kind)).fetchone()
                count = row["count"] if row else 0
                if limit is not None and count >= limit:
                    self._db.execute("ROLLBACK")
                    return False, count
                self._db.execute(
                    "INSERT INTO governor_windows (subscription_id, day, kind, count, usd) "
                    "VALUES (?,?,?,1,0) ON CONFLICT(subscription_id, day, kind) "
                    "DO UPDATE SET count = count + 1", (subscription_id, day, kind))
                self._db.execute("COMMIT")
                return True, count + 1
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def window_add_spend(self, subscription_id: str, day: str, kind: str, usd: float) -> None:
        self._exec("INSERT INTO governor_windows (subscription_id, day, kind, count, usd) VALUES (?,?,?,0,?) "
                   "ON CONFLICT(subscription_id, day, kind) DO UPDATE SET usd = usd + excluded.usd",
                   (subscription_id, day, kind, usd))

    def window_spend(self, subscription_id: str, day: str, kind: str) -> float:
        row = self._rows("SELECT usd FROM governor_windows WHERE subscription_id=? AND day=? AND kind=?",
                         (subscription_id, day, kind))
        return row[0]["usd"] if row else 0.0

    # -- runs and journal -------------------------------------------------------------

    def start_run(self, run_id, *, tenant, trigger, mode, dry_run, question=None,
                  subscription_id=None, envelope=None) -> None:
        self._exec("INSERT INTO runs (run_id, tenant, trigger, mode, subscription_id, envelope_source, "
                   "envelope_id, status, started_at, question, dry_run) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                   (run_id, tenant, trigger, mode, subscription_id,
                    getattr(envelope, "source", None), getattr(envelope, "id", None),
                    "running", now_iso(), question, int(dry_run)))

    def finish_run(self, run_id, status, *, answer_md=None, llm_usd=0.0) -> None:
        self._exec("UPDATE runs SET status=?, finished_at=?, answer_md=COALESCE(?, answer_md), "
                   "llm_usd=llm_usd+? WHERE run_id=?", (status, now_iso(), answer_md, llm_usd, run_id))

    def set_run_session(self, run_id, agent_session_id) -> None:
        self._exec("UPDATE runs SET agent_session_id=? WHERE run_id=?", (agent_session_id, run_id))

    def get_run(self, run_id) -> dict | None:
        rows = self._rows("SELECT * FROM runs WHERE run_id=?", (run_id,))
        return rows[0] if rows else None

    def recent_runs(self, limit: int = 20) -> list[dict]:
        return self._rows("SELECT run_id, tenant, trigger, mode, status, started_at, finished_at "
                          "FROM runs ORDER BY started_at DESC LIMIT ?", (limit,))

    def journal(self, run_id: str, kind: str, payload: dict) -> None:
        self._exec("INSERT INTO journal (ts, run_id, kind, payload_json) VALUES (?,?,?,?)",
                   (now_iso(), run_id, kind, _dumps(payload)))

    def journal_entries(self, run_id: str) -> list[dict]:
        rows = self._rows("SELECT seq, ts, kind, payload_json FROM journal WHERE run_id=? ORDER BY seq",
                          (run_id,))
        for r in rows:
            r["payload"] = json.loads(r.pop("payload_json"))
        return rows

    # -- outbox -------------------------------------------------------------------------

    def outbox_get(self, key: str) -> dict | None:
        rows = self._rows("SELECT * FROM outbox WHERE key=?", (key,))
        if not rows:
            return None
        row = rows[0]
        row["receipt"] = json.loads(row.pop("receipt_json")) if row.get("receipt_json") else None
        return row

    def outbox_set(self, key: str, run_id: str, tool: str, status: str,
                   receipt=None, error: str | None = None) -> None:
        self._exec("INSERT INTO outbox (key, run_id, tool, status, receipt_json, error, updated_at) "
                   "VALUES (?,?,?,?,?,?,?) ON CONFLICT(key) DO UPDATE SET status=excluded.status, "
                   "receipt_json=excluded.receipt_json, error=excluded.error, updated_at=excluded.updated_at",
                   (key, run_id, tool, status, _dumps(receipt) if receipt is not None else None, error, now_iso()))

    # -- findings -----------------------------------------------------------------------

    def finding_is_new(self, tenant: str, fingerprint: str, dry_run: bool) -> bool:
        return not self._rows("SELECT 1 FROM findings WHERE tenant=? AND fingerprint=? AND dry_run=?",
                              (tenant, fingerprint, int(dry_run)))

    def remember_finding(self, tenant, fingerprint, dry_run, *, playbook, finding, run_id) -> None:
        now = now_iso()
        self._exec(
            "INSERT INTO findings (tenant, fingerprint, dry_run, playbook, rule, entity_type, entity_id, "
            "entity_ref, exposure, rules_used, first_seen, last_seen, last_run_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(tenant, fingerprint, dry_run) "
            "DO UPDATE SET last_seen=excluded.last_seen, last_run_id=excluded.last_run_id, "
            "exposure=excluded.exposure",
            (tenant, fingerprint, int(dry_run), playbook, finding.rule, finding.entity_type,
             finding.entity_id, finding.entity_ref, str(finding.total_exposure),
             _dumps(finding.details.get("rules_used", {})), now, now, run_id))

    def set_finding_escalation(self, tenant, fingerprints, dry_run, escalation_id) -> None:
        with self._lock:
            for fp in fingerprints:
                self._db.execute("UPDATE findings SET escalation_id=? WHERE tenant=? AND fingerprint=? "
                                 "AND dry_run=?", (escalation_id, tenant, fp, int(dry_run)))

    def add_run_findings(self, run_id: str, playbook: str, rows: list[dict]) -> None:
        with self._lock:
            for seq, row in enumerate(rows):
                self._db.execute("INSERT OR REPLACE INTO run_findings (run_id, playbook, seq, fingerprint, "
                                 "rule, row_json) VALUES (?,?,?,?,?,?)",
                                 (run_id, playbook, seq, row.get("fingerprint") or "", row.get("rule", ""),
                                  _dumps(row)))

    def page_run_findings(self, run_id: str, *, playbook=None, rule=None,
                          offset: int = 0, limit: int = 20) -> tuple[int, list[dict]]:
        where, params = ["run_id=?"], [run_id]
        if playbook:
            where.append("playbook=?")
            params.append(playbook)
        if rule:
            where.append("rule=?")
            params.append(rule)
        clause = " AND ".join(where)
        total = self._rows(f"SELECT COUNT(*) AS n FROM run_findings WHERE {clause}", params)[0]["n"]
        rows = self._rows(f"SELECT row_json FROM run_findings WHERE {clause} ORDER BY playbook, seq "
                          "LIMIT ? OFFSET ?", params + [limit, offset])
        return total, [json.loads(r["row_json"]) for r in rows]

    # -- llm, anomalies, watermarks, snapshots, leases ---------------------------------

    def record_llm_call(self, *, run_id, role, provider, model, input_tokens, output_tokens,
                        cache_tokens=0, usd=0.0, latency_ms=0) -> None:
        self._exec("INSERT INTO llm_calls (ts, run_id, role, provider, model, input_tokens, output_tokens, "
                   "cache_tokens, usd, latency_ms) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (now_iso(), run_id, role, provider, model, input_tokens, output_tokens,
                    cache_tokens, usd, latency_ms))

    def record_anomaly(self, run_id: str, playbook: str | None, payload: dict) -> None:
        self._exec("INSERT INTO anomalies (ts, run_id, playbook, payload_json) VALUES (?,?,?,?)",
                   (now_iso(), run_id, playbook, _dumps(payload)))

    def get_watermark(self, tenant: str, entity: str) -> str | None:
        rows = self._rows("SELECT updated_at FROM watermarks WHERE tenant=? AND entity=?", (tenant, entity))
        return rows[0]["updated_at"] if rows else None

    def set_watermark(self, tenant: str, entity: str, updated_at: str) -> None:
        self._exec("INSERT INTO watermarks (tenant, entity, updated_at) VALUES (?,?,?) "
                   "ON CONFLICT(tenant, entity) DO UPDATE SET updated_at=excluded.updated_at",
                   (tenant, entity, updated_at))

    def get_snapshot(self, tenant: str, entity: str, record_id: str) -> dict | None:
        rows = self._rows("SELECT fields_json FROM snapshots WHERE tenant=? AND entity=? AND record_id=?",
                          (tenant, entity, record_id))
        return json.loads(rows[0]["fields_json"]) if rows else None

    def put_snapshot(self, tenant: str, entity: str, record_id: str, fields_hash: str, fields: dict) -> None:
        self._exec("INSERT INTO snapshots (tenant, entity, record_id, fields_hash, fields_json) VALUES (?,?,?,?,?) "
                   "ON CONFLICT(tenant, entity, record_id) DO UPDATE SET fields_hash=excluded.fields_hash, "
                   "fields_json=excluded.fields_json", (tenant, entity, record_id, fields_hash, _dumps(fields)))

    def acquire_lease(self, schedule_id: str, holder: str, ttl_seconds: int = 900) -> tuple[bool, str]:
        """One lease per schedule (S17 events/lease.py). Expired leases may be stolen."""
        now = datetime.now(UTC)
        with self._lock:
            self._db.execute("BEGIN IMMEDIATE")
            row = self._db.execute("SELECT holder, expires_at FROM leases WHERE schedule_id=?",
                                   (schedule_id,)).fetchone()
            if row and datetime.fromisoformat(row["expires_at"]) > now and row["holder"] != holder:
                self._db.execute("ROLLBACK")
                return False, f"held by {row['holder']} until {row['expires_at']}"
            expires = datetime.fromtimestamp(now.timestamp() + ttl_seconds, UTC).isoformat(timespec="seconds")
            self._db.execute("INSERT INTO leases (schedule_id, holder, expires_at) VALUES (?,?,?) "
                             "ON CONFLICT(schedule_id) DO UPDATE SET holder=excluded.holder, "
                             "expires_at=excluded.expires_at", (schedule_id, holder, expires))
            self._db.execute("COMMIT")
            return True, "stolen expired lease" if row and row["holder"] != holder else "granted"

    def release_lease(self, schedule_id: str, holder: str) -> None:
        self._exec("DELETE FROM leases WHERE schedule_id=? AND holder=?", (schedule_id, holder))
