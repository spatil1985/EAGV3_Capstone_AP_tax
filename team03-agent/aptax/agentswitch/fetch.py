"""Fetcher — paged reads with field quarantine (agent_design.md §4.10).

Ported from scripts/fetch.py (Repository pattern). Quarantine happens at fetch time so
no playbook can read a field with a filed defect by accident:

- `strip`    the field is removed;
- `suspect`  the field is renamed `_suspect_<name>`, so a playbook that recomputes it
             can compare and report an anomaly;
- `tax_heads` keep only `taxes[]` rows whose head is a real GST head; the rest move to
             `_suspect_taxes` (VendorCredit carries product names as heads, UC-25 §6).

Bill/Invoice `taxes[]` is deliberately kept: it reconciles to `total_tax` on 401/401
invoices and 63/64 bills (docs/usecases/IN/README.md, correction 2026-09-30).
"""

import re

from aptax.agentswitch.transport import ToolResult

QUARANTINE: dict[str, list[tuple[str, str, str]]] = {
    # entity: [(action, field, defect)]
    "CreditNote": [("strip", "taxes", "N128")],
    "Tax": [("strip", "group_taxes", "B6")],
    "Bill": [("suspect", "tds_amount", "N7"), ("suspect", "tds_section_code", "UC-39 §6"),
             ("strip", "match_status", "N2"), ("strip", "match_detail", "N2")],
    "ApprovalRequest": [("suspect", "is_overdue", "N1/N8")],
    "VendorCredit": [("tax_heads", "taxes", "UC-25 §6")],
}

GST_HEAD = re.compile(r"\b(IGST|CGST|SGST|UTGST|CESS)\b", re.I)


class FetchError(RuntimeError):
    pass


def quarantine(entity: str, record: dict) -> dict:
    rules = QUARANTINE.get(entity)
    if not rules or not isinstance(record, dict):
        return record
    clean = dict(record)
    for action, field, _defect in rules:
        if field not in clean:
            continue
        if action == "tax_heads":
            rows = clean.get(field) or []
            good = [r for r in rows if GST_HEAD.search(str(r.get("tax_type") or r.get("tax_name") or ""))]
            bad = [r for r in rows if r not in good]
            clean[field] = good
            if bad:
                clean[f"_suspect_{field}"] = bad
            continue
        value = clean.pop(field)
        if action == "suspect":
            clean[f"_suspect_{field}"] = value
    return clean


class Fetcher:
    def __init__(self, gateway, page_size: int = 1000, max_rows: int = 20000):
        self._gw = gateway
        self.page_size = page_size     # list tools reject limit > 1000
        self.max_rows = max_rows

    @staticmethod
    def _unwrap(tool: str, result: ToolResult) -> dict:
        if not result.ok:
            raise FetchError(f"{tool}: {result.error}")
        if not isinstance(result.data, dict):
            raise FetchError(f"{tool}: unexpected payload {type(result.data).__name__}")
        return result.data

    def page(self, entity: str, *, limit: int, offset: int = 0, **filters) -> tuple[list[dict], int | None]:
        """One page plus the server's total (for counts without fetching everything)."""
        tool = f"{entity}.list"
        page = self._unwrap(tool, self._gw.call_tool(tool, {**filters, "limit": limit, "offset": offset}))
        return [quarantine(entity, r) for r in page.get("data") or []], page.get("total")

    def list(self, entity: str, **filters) -> list[dict]:
        """All records matching flat, single-valued filters (IN README Rule 6)."""
        rows: list[dict] = []
        offset = 0
        while True:
            batch, total = self.page(entity, limit=self.page_size, offset=offset, **filters)
            rows.extend(batch)
            offset += len(batch)
            if (not batch or len(batch) < self.page_size
                    or (total is not None and offset >= total) or len(rows) >= self.max_rows):
                return rows[: self.max_rows]

    def call(self, tool: str, args: dict) -> dict:
        """One read endpoint (e.g. endpoint.accounting.bill_match). The policy decides whether
        the tool may run; a refusal or error raises FetchError like any other read."""
        return self._unwrap(tool, self._gw.call_tool(tool, args))

    def rest_get(self, path: str, params: dict | None = None):
        """An allowlisted REST read (aptax/agentswitch/risk.py REST_READS)."""
        return self._gw.rest("GET", path, params)

    def rest_post(self, path: str, body: dict):
        """An allowlisted REST POST that does not persist (e.g. the tax/compute oracle)."""
        return self._gw.rest("POST", path, None, body)

    def get(self, entity: str, record_id: str) -> dict:
        tool = f"{entity}.get"
        return quarantine(entity, self._unwrap(tool, self._gw.call_tool(tool, {"id": record_id})))
