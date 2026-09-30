"""Fetcher — paged reads with field quarantine (harness_plan.md §6.3).

Pattern: **Repository**. Playbooks ask for records by entity ("EWayBill", filters);
how they are paged, parsed and cleaned lives here. Nothing downstream sees a raw
MCP response.

Quarantine happens at fetch time, so no playbook can read a field with a filed defect
by accident:
- `strip`   — the field is removed.
- `suspect` — the field is renamed `_suspect_<name>`; a playbook that recomputes it
  can compare the two and report an anomaly.

Deliberate difference from harness_plan.md §6.3: Bill/Invoice document-level `taxes[]`
is **not** stripped. It reconciles to `total_tax` on 401/401 manual invoices and 63/64
header-taxed bills (docs/usecases/README.md, "Correction 2026-09-30"). Only
CreditNote.taxes[] (N128) is stripped.
"""

from harness.transport import ToolResult

QUARANTINE: dict[str, list[tuple[str, str, str]]] = {
    # entity: [(action, field, defect)]
    "CreditNote": [("strip", "taxes", "N128")],
    "Tax": [("strip", "group_taxes", "B6")],
    "Bill": [("suspect", "tds_amount", "N7"), ("strip", "match_status", "N2"),
             ("strip", "match_detail", "N2")],
    "ApprovalRequest": [("suspect", "is_overdue", "N1/N8")],
}


class FetchError(RuntimeError):
    pass


def quarantine(entity: str, record: dict) -> dict:
    rules = QUARANTINE.get(entity)
    if not rules:
        return record
    clean = dict(record)
    for action, field, _defect in rules:
        if field not in clean:
            continue
        value = clean.pop(field)
        if action == "suspect":
            clean[f"_suspect_{field}"] = value
    return clean


class Fetcher:
    def __init__(self, gateway, page_size: int = 1000, max_rows: int = 20000):
        self._gw = gateway
        self.page_size = page_size   # Bill.list inputSchema: limit max 1000
        self.max_rows = max_rows

    def _unwrap(self, tool: str, result: ToolResult) -> dict:
        if not result.ok:
            raise FetchError(f"{tool}: {result.error}")
        if not isinstance(result.data, dict):
            raise FetchError(f"{tool}: unexpected payload {type(result.data).__name__}")
        return result.data

    def list(self, entity: str, **filters) -> list[dict]:
        """All records matching `filters`. Filters are flat, one value each
        (docs/usecases/README.md Rule 6); range filtering is the caller's job."""
        tool = f"{entity}.list"
        rows: list[dict] = []
        offset = 0
        while True:
            page = self._unwrap(tool, self._gw.call_tool(
                tool, {**filters, "limit": self.page_size, "offset": offset}))
            batch = page.get("data") or []
            rows.extend(quarantine(entity, r) for r in batch)
            total = page.get("total")
            offset += len(batch)
            if (not batch or len(batch) < self.page_size
                    or (total is not None and offset >= total) or len(rows) >= self.max_rows):
                return rows[: self.max_rows]

    def get(self, entity: str, record_id: str) -> dict:
        tool = f"{entity}.get"
        return quarantine(entity, self._unwrap(tool, self._gw.call_tool(tool, {"id": record_id})))
