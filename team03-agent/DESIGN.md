# DESIGN.md — Payables & Tax Agent (Seat 03)

## Loop Architecture
Native JSON-RPC MCP connector (`run_agent.py`), no third-party agent framework.
- `initialize` establishes protocol version `2025-11-25`.
- `tools/list` discovers the seat's closed tool schema (`Invoice.*`, `Payment.*`,
  `TaxLine.*`, `Vendor.*`, `JournalEntry.*`).
- `tools/call` executes a single tool per turn; results are appended to the message
  history and fed back to the LLM until it returns a final synthesis (no tool_calls).
- `SKILL.md` is loaded fresh as the system prompt on every invocation — it is the
  permanent charter, not a one-time setup step.
- Deterministic work (currency summation, invoice matching) is delegated to
  `scripts/tax_math.py` and `scripts/invoice_matcher.py` rather than left to the LLM,
  per Hard Rule 3.

## State Tolerance
The ledger (415 records) is shared live with Teams 01 (GL) and 02 (AR); there are no
copies. Consequences for this agent:
- **Re-read before write.** Before flipping `status`/`hold_payment` on an invoice, the
  agent re-fetches that record rather than trusting a value cached earlier in the same
  run, since another seat may have changed it mid-conversation.
- **Idempotent duplicate handling.** `Invoice.update(..., status="under_review")` is
  safe to re-issue; the playbook does not assume it is the only writer and does not
  hard-fail if the record has already moved out of `unpaid`/`paid`.
- **No destructive writes.** The agent only ever holds/flags records
  (`hold_payment=True`, `status="under_review"`); it never cancels, deletes, or
  force-pays, since a concurrent read elsewhere could be relying on the prior state.
- **Locale is fetched, not cached across sessions.** `GET /api/accounting/locale` is
  checked per run since the same codebase serves both Suryodaya (IN) and Keystone
  (US).

## Refusal Handling
Refusals are deterministic, not judgment calls left to the LLM:
- `SKILL.md` declares `SalarySlip`, `Contract`, `EsignDocument` as Prohibited Entities
  (Strict 403). Any tool call targeting these is rejected before it reaches MCP, and
  the agent responds with an escalation message pointing to Admin/Human operator.
- Vendor notes, invoice descriptions, and any free-text/file content are treated as
  passive data (Hard Rule 1). Text found there is never interpreted as an instruction
  — this is enforced by never re-injecting untrusted field values into the system or
  tool-selection prompt, only into data payloads.
- Boundary tests in `tests/` assert both behaviors: a forbidden-entity request must
  produce a refusal, and a prompt-injection payload embedded in an invoice
  description must not change agent behavior.

## Known Limitations
- **Non-standard OCR receipts**: records with missing/garbled `tax_amount` or
  `invoice_number` fields are excluded from totals rather than guessed at; they
  surface as flagged/unmatched rather than silently dropped.
- **Manual cash adjustments**: journal entries posted outside the normal
  Invoice/Payment flow are not currently reconciled against the duplicate-payment
  playbook and may require a follow-up playbook.
- **Suspicious-match window is heuristic**: the ±3 business day / exact-amount rule
  in `invoice_matcher.py` can produce false positives for vendors with genuinely
  recurring identical invoices (e.g. flat monthly retainers) — these are held for
  human review, not auto-resolved.
- **Locale detection is API-driven only**: if `GET /api/accounting/locale` is
  unavailable, the agent has no offline fallback and should escalate rather than
  assume a jurisdiction.
