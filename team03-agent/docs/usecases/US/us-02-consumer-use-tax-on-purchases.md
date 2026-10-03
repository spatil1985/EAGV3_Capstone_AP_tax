# US-02 — Consumer Use Tax on Untaxed Purchases

**US · Proposed owner: Sudip · Verdict: 🟡 Buildable, but the amount depends on a taxability classification the data doesn't carry**
**IN counterpart:** UC-03 / UC-21 (tax the buyer self-assesses) · **live evidence 2026-10-03**

---

## 1. Question

> *"Which purchases did nobody charge us sales tax on, where we owe use tax ourselves?"*

## 2. Statutory basis

- **Use tax** is the complement of sales tax. When a business buys taxable goods or
  services for its own use and the vendor charges no sales tax, the **buyer** owes use
  tax at the rate where the item is used, reported on its own sales/use tax return.
  In Ohio, R.C. 5741.02 imposes use tax at the same combined state and county rate as
  sales tax.
- **Exemptions decide most of it.** Ohio exempts items used directly in manufacturing
  (R.C. 5739.02(B)(42)(g)) and purchases for resale. Some services are taxable in
  Ohio, notably building maintenance/janitorial and exterminating, while consulting is
  not. *Classification needs a CPA's confirmation (US README caveats).*
- **Consequence if missed:** use tax is the most common audit adjustment for
  manufacturers, and is assessed with interest and penalty.

## 3. Trigger

- **Event:** on each new bill with no vendor tax.
- **Monthly sweep** before the return.
- **Period:** filing month.

## 4. Input contract

| Call | Fields |
|---|---|
| `Bill.list {"limit":1000}` | `vendor_id`, `date`, `status`, `currency_code`, `net_total`, `total_tax`, `taxes[]`, `use_tax_accrued`, `items[].description`, `items[].amount`, `items[].item_id` |
| `Party.get {"id": vendor_id}` | `addresses[].state` (in-state or out-of-state vendor) |
| `Item.get {"id": item_id}` | the item's classification (`product_type`, account) when present |
| `TaxJurisdiction.list` | use-tax rate for the place of use (OH 5.75% + Stark County 0.75% = 6.5%) |

## 5. Algorithm

1. Bills in the period, excluding `draft` and `void`, in USD (INR bills are filed B8
   residue).
2. Keep bills where the vendor charged nothing (`total_tax = 0` and `taxes[]` empty)
   and `use_tax_accrued` is null or 0.
3. **Classify each line** by a playbook table keyed on item or description:
   `exempt_manufacturing` (production material consumed in manufacturing),
   `exempt_resale`, `taxable_goods`, `taxable_service` (e.g. janitorial,
   exterminating), `non_taxable_service` (consulting, transportation by a common
   carrier) and `unclassified`.
4. **Use tax due** = Σ (taxable lines) × the combined rate at the place of use.
   `unclassified` lines are reported separately, as a range, not counted as due.
5. Emit `use_tax_due` per bill and an `unclassified` summary row. If
   `use_tax_accrued` is later set, compare it and emit `stored_value_mismatch` on
   disagreement.

### Worked example (REAL — 2026 to date, before classification)

81 bills, all from Ohio vendors, $588,555.24 net: **$0 vendor sales tax, $0 use tax
accrued**.

| Line class (by description) | Amount | Vendors | Treatment pending classification |
|---|---|---|---|
| "… production material" | $327,570.24 | Apex Metals Supply, Stark County Powder Coating | likely exempt (manufacturing) |
| "Inbound and outbound freight" | $120,150.00 | Ohio Valley Freight Lines | common-carrier transport, likely non-taxable |
| "Perishable tooling and abrasives" | $113,800.00 | Midwest Tool & Abrasive Co | depends on direct use in manufacturing |
| Services (machining, ISO audit, welding call-out, signage) | $27,035.00 | Canton Industrial Consulting, J. Miller Welding, Hartville Sign & Graphics | mixed |

> Output: *"$588,555.24 of 2026 purchases carried no sales tax and no use tax was
> accrued. $327,570.24 is production material, likely exempt. $260,985.00 needs
> classification; if all of it were taxable at 6.5%, use tax would be $16,964.03."*

## 6. Known-bad data

- `use_tax_accrued` is null on 101/101 bills, so there is no stored value to check.
- Item-level GST fields on bills are GST leftovers (B8 class) and are never read.
- 15 INR bills are void, and 1 INR bill is a draft (B8 residue) — excluded by step 1.

## 7. Output contract

`finding_type: "use_tax"`, `rule ∈ {use_tax_due, use_tax_unclassified,
stored_value_mismatch}`, `entity_type: "Bill"`, `total_exposure` = use tax,
`details: {line_class, taxable_base, rate, place_of_use}`. Same shape as IN UC-03's
`rcm_undeclared_liability`, since both are self-assessed tax.

## 8. Limits

- Never sets `use_tax_accrued` and never posts.
- Taxability is a legal determination; the playbook table carries the team's reading,
  dated, and a CPA confirms it.
- Assumes use in Ohio (Keystone's only operating jurisdiction in the data).

## 9. Validation

1. Live control: 81 bills, 0 with vendor tax, $588,555.24 total.
2. Fixture: one $10,000 janitorial bill with no tax → $650.00 use tax at 6.5%.
3. Once classification is agreed, recompute and compare with the CPA's working paper.

## 10. Open questions

- **Perishable tooling ($113,800):** exempt as used directly in manufacturing, or
  taxable? It is the largest swing item.
- **Freight:** separately stated, common-carrier freight is generally not taxable.
  Confirm for Ohio Valley Freight Lines.
- Should the classification live on `Item` (one field) rather than in a playbook
  table keyed on descriptions?

## 11. Live evidence — actual calls, 2026-10-03

- `Bill.list {"limit":1000}` → 101 bills: paid 67, void 15, open 14, draft 5. 2026
  non-draft/void: 81, all USD, all from Ohio-address vendors, `total_tax` 0 and
  `taxes[]` empty on all 81, `use_tax_accrued` null on all.
- Examples: BILL-2026-00029 (`858f6a9d-e1c8-4dc6-aedb-85a794d3a50f`) Apex Metals
  Supply, Massillon OH, $16,739.38, "Hot-Rolled Steel Sheet 14 ga … — production
  material"; BILL-2026-00065 (`9c24fdb1-61a0-4363-9aed-9fdb7ef2557f`) Midwest Tool &
  Abrasive, $10,000.00, tooling; BILL-2026-00081 (`6d7e27f8-e0e3-4bc5-af60-f5e2e9d6ea74`)
  Ohio Valley Freight Lines, $6,750.00, freight.
