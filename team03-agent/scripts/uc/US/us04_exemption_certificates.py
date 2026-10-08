"""US-04 — Exemption certificate coverage for untaxed sales.

Spec: docs/usecases/US/us-04-exemption-certificate-coverage.md.
Question: "For every sale we didn't charge tax on, do we hold a valid exemption certificate?"

Statute: an exempt sale (resale, manufacturing, nonprofit) must be supported by a certificate valid on
the sale date for the destination state (e.g. Ohio STEC B); otherwise the seller owes the tax it didn't
collect.

Rules:
  exemption_without_certificate  an exempt invoice with no active certificate for that customer and
                                 state covering its date; exposure = net × the state's combined rate
  certificate_expiring           an active certificate in use that expires within 90 days
  certificate_unsupported        (data_quality) a certificate with no file attached: recorded, not evidenced
The invoice's state comes from the exempt row's state_code, never its jurisdiction_level (US-01 §6).
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day

EXPIRY_WARN = 90


def exempt_invoices(data):
    for inv in data.get("invoices", []):
        if (inv.get("status") or "").lower() in ("draft", "void", "cancelled"):
            continue
        rows = [r for r in inv.get("taxes") or [] if r.get("is_exempt")]
        if rows:
            yield inv, str(rows[0].get("state_code") or "").upper(), rows[0].get("tax_type")


def covering(inv, state, certs):
    when = day(inv.get("date"))
    for c in certs:
        if (c.get("party_id") == inv.get("party_id") and (c.get("status") or "") == "active"
                and (not c.get("state_code") or str(c["state_code"]).upper() == state)
                and (day(c.get("issue_date")) or when) <= when <= (day(c.get("expiry_date")) or when)):
            return c
    return None


class Certificates(Rule):
    id = "sales_exemption"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        certs = data.get("certificates", [])
        rates: dict = {}
        for j in data.get("jurisdictions", []):
            s = str(j.get("state_code")).upper()
            rates[s] = rates.get(s, Decimal("0")) + money(j.get("rate_percentage"))
        used = {}
        for inv, state, label in exempt_invoices(data):
            cert = covering(inv, state, certs)
            if cert:
                used[cert["id"]] = cert
                continue
            net = money(inv.get("net_total"))
            risk = (net * rates.get(state, Decimal("0")) / 100).quantize(CENTS)
            yield Finding(
                finding_type="sales_exemption", rule="exemption_without_certificate", severity=self.severity,
                entity_type="Invoice", entity_id=inv["id"], entity_ref=inv.get("number"), total_exposure=risk,
                currency=ctx.currency, counterparty_id=inv.get("party_id"), counterparty_name=inv.get("_party_id_display"),
                summary=f"{inv.get('number')} ({inv.get('date')}, {fmt(net, ctx.currency)}) was sold tax-exempt in {state} "
                        f"({label}) with no valid certificate on file for {inv.get('_party_id_display')}: "
                        f"{fmt(risk, ctx.currency)} of uncollected tax at risk.",
                details={"state_code": state, "net_total": str(net), "rate": str(rates.get(state, Decimal("0")))})
        for cert in used.values():
            expiry = day(cert.get("expiry_date"))
            if expiry and expiry <= ctx.as_of + timedelta(days=EXPIRY_WARN):
                yield Finding(finding_type="sales_exemption", rule="certificate_expiring", severity=50,
                              entity_type="ExemptionCertificate", entity_id=cert["id"],
                              entity_ref=cert.get("certificate_number"), currency=ctx.currency,
                              summary=f"Certificate {cert.get('certificate_number')} ({cert.get('_party_id_display')}) "
                                      f"expires on {expiry}: collect a renewal before then.",
                              details={"expiry_date": str(expiry)})
        for cert in certs:
            if (cert.get("status") or "") == "active" and not cert.get("certificate_file"):
                yield Finding(finding_type=DATA_QUALITY, rule="certificate_unsupported", status=DATA_QUALITY,
                              severity=20, entity_type="ExemptionCertificate", entity_id=cert["id"],
                              entity_ref=cert.get("certificate_number"), currency=ctx.currency,
                              summary=f"Certificate {cert.get('certificate_number')} ({cert.get('_party_id_display')}) has "
                                      f"no file attached: coverage is recorded, not evidenced for an auditor.",
                              details={"field": "certificate_file"})


class ExemptionCertificateCoverage(Playbook):

    @property
    def rules(self):
        return [Certificates()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice"), certificates=fetcher.list("ExemptionCertificate"),
                       jurisdictions=fetcher.list("TaxJurisdiction"))

    def context(self, data, findings, ctx):
        rows = list(exempt_invoices(data))
        return {"exempt invoices": len(rows), "exempt sales": str(sum((money(i.get("net_total")) for i, _, _ in rows),
                                                                      Decimal("0"))),
                "certificates on file": len(data["certificates"])}

    def summary(self, outcome, ctx):
        c = outcome.context
        bare = [f for f in outcome.findings if f.rule == "exemption_without_certificate"]
        unsupported = sum(1 for f in outcome.findings if f.rule == "certificate_unsupported")
        if not bare:
            return (f"All {c['exempt invoices']} exempt sale(s) ({fmt(money(c['exempt sales']), ctx.currency)}) are covered "
                    f"by a valid certificate." + (f" {unsupported} certificate(s) have no file attached." if unsupported else ""))
        risk = sum((f.total_exposure for f in bare), Decimal("0"))
        return (f"{len(bare)} of {c['exempt invoices']} exempt sale(s) have no valid certificate: {fmt(risk, ctx.currency)} "
                f"of uncollected tax at risk.")
