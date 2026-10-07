-- aptax store (agent_design.md §4.13). One SQLite file under runs/ (gitignored).
-- Every table is keyed so a crash and restart never loses or doubles state.

PRAGMA journal_mode = WAL;

-- Every trigger, admitted or refused. (source, id) is the dedupe key (S17 events/store.py).
CREATE TABLE IF NOT EXISTS envelopes (
    source      TEXT NOT NULL,
    id          TEXT NOT NULL,
    type        TEXT NOT NULL,
    tenant      TEXT NOT NULL,
    trust       TEXT NOT NULL,
    actor       TEXT,
    subject     TEXT,
    occurred_at TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    data_json   TEXT NOT NULL,
    admitted    INTEGER,
    PRIMARY KEY (source, id)
);

-- Every subscription match decision, including "no".
CREATE TABLE IF NOT EXISTS decisions (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    source          TEXT NOT NULL,
    envelope_id     TEXT NOT NULL,
    subscription_id TEXT,
    decision        TEXT NOT NULL,
    reason          TEXT
);

-- Work a control prevented. Without this it leaves no trace (S17 events/report.py).
CREATE TABLE IF NOT EXISTS refusals (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT NOT NULL,
    control         TEXT NOT NULL,
    reason          TEXT NOT NULL,
    source          TEXT,
    envelope_id     TEXT,
    subscription_id TEXT,
    detail_json     TEXT
);

-- Persisted daily windows, so a restart never resets a ceiling (S17 events/governor.py).
CREATE TABLE IF NOT EXISTS governor_windows (
    subscription_id TEXT NOT NULL,
    day             TEXT NOT NULL,
    kind            TEXT NOT NULL,          -- run | llm
    count           INTEGER NOT NULL DEFAULT 0,
    usd             REAL    NOT NULL DEFAULT 0,
    PRIMARY KEY (subscription_id, day, kind)
);

CREATE TABLE IF NOT EXISTS runs (
    run_id           TEXT PRIMARY KEY,
    tenant           TEXT NOT NULL,
    trigger          TEXT NOT NULL,
    mode             TEXT NOT NULL,          -- agent | pipeline | playbook
    subscription_id  TEXT,
    envelope_source  TEXT,
    envelope_id      TEXT,
    status           TEXT NOT NULL,          -- running | waiting | completed | failed | expired | unverified
    started_at       TEXT NOT NULL,
    finished_at      TEXT,
    question         TEXT,
    answer_md        TEXT,
    llm_usd          REAL NOT NULL DEFAULT 0,
    agent_session_id TEXT,
    dry_run          INTEGER NOT NULL DEFAULT 1
);

-- Append-only journal: never UPDATE or DELETE (glc audit/schema.sql). Enforced below.
CREATE TABLE IF NOT EXISTS journal (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    kind         TEXT NOT NULL,              -- tool_call | llm_turn | capability | decision | note | answer
    payload_json TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS journal_no_update BEFORE UPDATE ON journal
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER IF NOT EXISTS journal_no_delete BEFORE DELETE ON journal
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE INDEX IF NOT EXISTS idx_journal_run ON journal(run_id, seq);

-- Write idempotency (S17 events/outbox.py): a 'started' row left by a crash is
-- reconciled, never blindly re-sent.
CREATE TABLE IF NOT EXISTS outbox (
    key          TEXT PRIMARY KEY,
    run_id       TEXT NOT NULL,
    tool         TEXT NOT NULL,
    status       TEXT NOT NULL,              -- started | completed | failed | suppressed
    receipt_json TEXT,
    error        TEXT,
    updated_at   TEXT NOT NULL
);

-- Cross-run memory of findings, so a sweep only escalates what is new.
CREATE TABLE IF NOT EXISTS findings (
    tenant        TEXT NOT NULL,
    fingerprint   TEXT NOT NULL,
    dry_run       INTEGER NOT NULL,          -- rehearsals keep their own memory
    playbook      TEXT NOT NULL,
    rule          TEXT NOT NULL,
    entity_type   TEXT,
    entity_id     TEXT,
    entity_ref    TEXT,
    exposure      TEXT,
    rules_used    TEXT,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    last_run_id   TEXT NOT NULL,
    escalation_id TEXT,
    disposition   TEXT,
    PRIMARY KEY (tenant, fingerprint, dry_run)
);

-- Rows of one run, so the agent can page through them (get_findings).
CREATE TABLE IF NOT EXISTS run_findings (
    run_id      TEXT NOT NULL,
    playbook    TEXT NOT NULL,
    seq         INTEGER NOT NULL,
    fingerprint TEXT NOT NULL,
    rule        TEXT NOT NULL,
    row_json    TEXT NOT NULL,
    PRIMARY KEY (run_id, playbook, seq)
);

CREATE TABLE IF NOT EXISTS approvals (
    run_id        TEXT NOT NULL,
    step          INTEGER NOT NULL,
    escalation_id TEXT,
    choices_json  TEXT,
    resolution    TEXT,
    PRIMARY KEY (run_id, step)
);

CREATE TABLE IF NOT EXISTS watermarks (
    tenant     TEXT NOT NULL,
    entity     TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tenant, entity)
);

CREATE TABLE IF NOT EXISTS snapshots (
    tenant      TEXT NOT NULL,
    entity      TEXT NOT NULL,
    record_id   TEXT NOT NULL,
    fields_hash TEXT NOT NULL,
    fields_json TEXT NOT NULL,
    PRIMARY KEY (tenant, entity, record_id)
);

CREATE TABLE IF NOT EXISTS leases (
    schedule_id TEXT PRIMARY KEY,
    holder      TEXT NOT NULL,
    expires_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_calls (
    seq           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    run_id        TEXT,
    role          TEXT,
    provider      TEXT,
    model         TEXT,
    input_tokens  INTEGER,
    output_tokens INTEGER,
    cache_tokens  INTEGER,
    usd           REAL,
    latency_ms    INTEGER
);

CREATE TABLE IF NOT EXISTS anomalies (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    playbook     TEXT,
    payload_json TEXT NOT NULL
);
