"""Record helpers: party names, document references and status sets used across use cases."""

from aptax.playbooks.base import Dataset

# Documents in these states never reached the books (or were reversed out of them).
NOT_POSTED = {"draft", "void", "cancelled", "rejected"}


def posted(records, status_field: str = "status"):
    return [r for r in records if (r.get(status_field) or "").lower() not in NOT_POSTED]


def party_of(doc: dict, data: Dataset | None = None, source: str = "parties") -> tuple[str | None, str | None]:
    """(id, display name) of a document's counterparty, whichever field the entity uses."""
    pid = doc.get("party_id") or doc.get("vendor_id") or doc.get("customer_id")
    name = (doc.get("_party_id_display") or doc.get("_vendor_id_display")
            or doc.get("_customer_id_display") or doc.get("vendor_name") or doc.get("customer_name"))
    if not name and data is not None and pid:
        party = data.index(source, "id").get(pid)
        if party:
            name = party.get("name") or party.get("display_name") or party.get("_display")
    return pid, name


def ref(doc: dict, *keys: str) -> str | None:
    """A human reference for a document: the first non-empty of the given keys, then number/id."""
    for key in (*keys, "bill_number", "invoice_number", "number", "reference_number", "_display"):
        if doc.get(key):
            return str(doc[key])
    return doc.get("id")


def by(records, key: str) -> dict:
    out: dict = {}
    for r in records:
        out.setdefault(r.get(key), []).append(r)
    return out
