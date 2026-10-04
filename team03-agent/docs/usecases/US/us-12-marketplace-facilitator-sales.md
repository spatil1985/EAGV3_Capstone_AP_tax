# US-12 — Retail: Marketplace Facilitator Sales

**US · Domains: retail (sellers on Amazon, Walmart, Etsy-type marketplaces); clinic or school web stores that sell through a marketplace · Verdict: ⚪ Spec only — no sales channel in the data model; Keystone sells direct**
**IN counterpart:** [UC-36](../IN/uc-36-ecommerce-tcs-s52.md) (s.52 e-commerce TCS) · **live evidence 2026-10-04**

---

## 1. Question

> *"For sales we make through marketplaces, is the marketplace collecting the tax, and are we keeping those sales out of our own returns and nexus totals correctly?"*

## 2. Statutory basis

- **Marketplace facilitator laws:** every US state with a sales tax has adopted one since *Wayfair* (2018).
  The **marketplace collects and remits** the tax on sales it facilitates. The seller doesn't collect on
  those sales, and either excludes them from its return or reports and deducts them, depending on the
  state.
- **Nexus thresholds:** *our understanding (caveat):* states differ on whether a remote seller's
  marketplace sales count toward its own economic-nexus threshold ([US-03](us-03-economic-nexus-monitoring.md)).
  Some include them; many exclude them. Per-state rule in the rulebook.
- **Consequence:**
  - tax charged by both the seller and the marketplace → over-collection (refund liability to customers);
  - facilitated sales left in the seller's return → over-remittance;
  - facilitated sales wrongly counted (or not counted) toward nexus → missed or unnecessary registration.

## 3. Trigger

- **Scheduled monthly**, before the return (feeds [US-01](us-01-period-sales-use-tax-liability.md)).
- **On event:** `invoice.created` on a marketplace channel.
- **On request.**

## 4. Input contract: what would be needed

| Need | Platform today |
|---|---|
| Channel / marketplace on each sale | ❌ `Invoice` has no channel field. A marketplace as the `Party` (customer) is a workaround, but it loses the end buyer's state |
| Marketplace settlement or tax-collected report | ❌ No entity or import |
| `TaxNexus.nexus_type = marketplace_facilitator` | ✅ The option exists (it marks a state where the *company itself* is a facilitator) |

## 5. Algorithm (as specified)

1. **Facilitated sales:** invoices on a marketplace channel, per state and period.
2. **`marketplace_sale_taxed_by_seller`:** a facilitated invoice carrying our own tax rows → over-collection.
3. **`marketplace_sale_in_own_return`:** facilitated sales included in the US-01 liability base → remove,
   or report as a deduction per the state table.
4. **`marketplace_sales_nexus_treatment`:** pass facilitated sales to US-03 with the state's
   include/exclude flag.
5. **`facilitator_report_mismatch`:** our facilitated sales vs the marketplace's statement, per state.

### Worked example (CONSTRUCTED)

> A retailer sells $40,000 into Pennsylvania in August: $25,000 direct and $15,000 through a marketplace.
> - The PA return base is $25,000 × 6% = $1,500; the $15,000 is the marketplace's to collect.
> - If our invoices for the marketplace sales also carry 6% ($900) → `marketplace_sale_taxed_by_seller`.

## 6. Known-bad data

- None on Keystone (it sells direct). The India tenant has 26 stray `TaxNexus` rows typed
  `marketplace_facilitator` (UC-36 §6), and the US playbook must never read India-tenant nexus rows.

## 7. Output contract

`finding_type: "marketplace"`, `rule ∈ {marketplace_sale_taxed_by_seller, marketplace_sale_in_own_return,
marketplace_sales_nexus_treatment, facilitator_report_mismatch}`.

## 8. Limits

- Can't run until a sales channel exists. It routes `spec`.
- Never files returns or contacts marketplaces.

## 9. Validation

Fixtures only (§5). **No live case:** Keystone has no marketplace sales.

## 10. Open questions

- Minimum platform change: `Invoice.sales_channel` / `marketplace_id`, plus an import of marketplace
  tax-collected reports. The same ask as F22 on the India side. File it once as a cross-jurisdiction
  request.

## 11. Live evidence — actual calls, 2026-10-04

- `/api/schemas` → `Invoice` has no channel or marketplace field. `TaxNexus.nexus_type` options:
  `physical | economic | marketplace_facilitator | affiliate | none`.
- `TaxNexus.list` (Keystone) → 4 rows: IL / MI / PA economic, OH physical. None is a marketplace.
