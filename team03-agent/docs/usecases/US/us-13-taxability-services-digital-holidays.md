# US-13 — Taxability by State: Services, Digital Products, Medical Items, Shipping and Sales Tax Holidays

**US · Domains: agency (services, digital), clinic (prescription and OTC, medical devices), retail (holidays, shipping), school (cafeteria and fundraiser sales); manufacturing for goods · Verdict: ⚪ Spec only for services and digital (Keystone sells only goods) · 🟢 goods checked, 0 findings**
**IN counterpart:** [UC-18](../IN/uc-18-hsn-rate-consistency.md) (rate by product code) · complements [US-05](us-05-sourcing-and-rate-correctness.md) (rate *given* taxable) and [US-04](us-04-exemption-certificate-coverage.md) (customer exemptions) · **live evidence 2026-10-04**

---

## 1. Question

> *"Is each thing we sell actually taxable in the customer's state on that date — and are we charging accordingly?"*

## 2. Statutory basis

US sales tax applies to goods by default and to **services only where a state lists them**. Rules differ
sharply by state. *Our understanding, to confirm per state (caveat):*

| Topic | Ohio | Pennsylvania | Michigan | Illinois |
|---|---|---|---|---|
| Services | Many listed services are taxable (R.C. 5739.01(B)(3)): computer and data-processing and electronic-information services for business use, building maintenance and janitorial, exterminating, landscaping, security, employment services, others | Selected services (e.g. building maintenance, help supply) | Generally not taxable | Generally not taxable (service-occupation tax applies to goods transferred with a service) |
| Canned software / digital products | Taxable | Taxable, including electronically delivered and digital products (Act 84 of 2016) | Prewritten software taxable | Varies; Chicago taxes cloud use under its lease tax |
| Prescription drugs | Exempt | Exempt | Exempt | Reduced rate |
| Delivery charges | Generally follow the item | Generally follow the item | Recent law change for separately stated charges | Depends |
| Sales tax holiday | Annual; expanded in 2024 to most items ≤ $500 | None | None | None |

- **Agency note:** *our understanding (caveat):* Washington began taxing advertising and several
  IT/digital services from **1 October 2025**. That matters as soon as an agency has Washington customers.
- **Consequence:**
  - charging tax on an exempt line → over-collection, which must be refunded to the customer or remitted;
  - not charging on a taxable line → the seller pays from its own pocket ([US-01](us-01-period-sales-use-tax-liability.md)).

## 3. Trigger

- **On event:** `invoice.created`, checking each line before the invoice goes out.
- **On event:** `item.tax_fields_changed` (product class or tax code edits, watcher G4).
- **Scheduled monthly** sweep before returns; **calendar:** holiday windows from `config/calendar.yaml`.
- **On request.**

## 4. Input contract

| Call | Fields |
|---|---|
| `Invoice.list` | `date`, `items[]` (`item_id`, description, amount), `taxes[]` (`state_code`, `jurisdiction_id`, `rate`, `amount`, `is_exempt`), `shipping_charge`, `party_id` |
| `Item.list` | `product_type` (`goods\|services`), `type` (`product\|service\|consumable`), `tax_code`, `taxable`, `tax_preference` |
| `Party.get` | `addresses[].state` (US README rule 2: the destination when there's no tax row) |
| Rulebook | `us/tables/taxability.yaml`: (state, product class, date range) → taxable / exempt / reduced rate / holiday; with source and review-by date (G6) |

## 5. Algorithm

1. **Product class** per line: `Item.tax_code` if set, otherwise `product_type` plus the item's class
   mapping in the rulebook.
2. **Destination state** per line (US-03 step 2).
3. **Expected treatment** = table lookup (state, class, invoice date). This includes holiday windows and
   delivery-charge rules.
4. Compare with the tax actually charged:
   - `untaxed_taxable_line`: taxable but no tax and no exemption certificate (US-04 covers certificates).
   - `taxed_exempt_line`: exempt by product (not by customer) but taxed.
   - `holiday_not_applied`: inside a holiday window, qualifying, yet taxed.
   - `shipping_taxability_mismatch`: shipping taxed or untaxed contrary to the state rule.
5. **`taxability_unmapped`:** a product class missing from the table for that state. Fail closed: report,
   don't guess.

### Worked example

> **Live:** 28 items, **all goods**, all `taxable`, `tax_code` null. 200 invoice lines, all goods, to OH,
> MI and PA customers. Goods are taxable in all three, so 0 product-taxability findings. Customer
> exemptions are US-04's job. `shipping_charge` is 0 on every invoice.
>
> **Constructed (agency):** an agency invoices an Ohio client $8,000 for "ongoing website hosting and data
> services" plus $12,000 for "brand strategy consulting", and charges no tax.
> - Hosting and data processing for business use is taxable in Ohio (6.5% with Stark County) → $520,
>   `untaxed_taxable_line`.
> - Consulting is not on Ohio's list → no tax due.

## 6. Known-bad data

- `Item.tax_code` is null on all 28 US items, so the class comes from the rulebook mapping, which is
  weaker.
- US documents carry GST item fields (`cgst/sgst/igst`, filed B8). They are never read.

## 7. Output contract

`finding_type: "taxability"`, `rule ∈ {untaxed_taxable_line, taxed_exempt_line, holiday_not_applied,
shipping_taxability_mismatch, taxability_unmapped}`. Each row cites the rulebook entry (state, class,
source, effective dates).

## 8. Limits

- Not a rate service. `rate_source: manual` and no Avalara/TaxJar call is ever made
  (`not_yet_supported.tax_rate_service`). This is a **documented gap**, not a bug.
- Taxability positions are engineering specifications, not tax advice. Each table row names its source
  for re-checking.

## 9. Validation

1. **Live:** 200 goods lines → 0 findings.
2. **Fixtures:**
   - Ohio + "computer services, business use" + untaxed → finding;
   - Michigan + the same service → none.
3. **Holiday fixture:** a qualifying Ohio item inside the configured holiday window, taxed →
   `holiday_not_applied`.

## 10. Open questions

- Should `Item.tax_code` carry a standard taxability code (e.g. the codes rate services use) so the table
  can key on it?
- Ohio's holiday dates change by statute each year. Who updates `config/calendar.yaml` when they're
  announced?

## 11. Live evidence — actual calls, 2026-10-04

- `Item.list` → 28: `product_type: goods` ×28, `tax_preference: taxable` ×28, `tax_code: null` ×28.
- `Invoice.list {"limit":1000}` → 158 invoices, 200 lines, all goods. Tax-row states OH 173, MI 28,
  PA 28. `shipping_charge > 0` on 0.
- `TaxJurisdiction.list` → OH state 5.75% (monthly), Stark County 0.75% (monthly), MI 6% (quarterly),
  PA 6% (quarterly). All `sourcing: destination`, `rate_source: manual`.
