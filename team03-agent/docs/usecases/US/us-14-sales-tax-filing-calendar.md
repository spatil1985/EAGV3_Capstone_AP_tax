# US-14 — Sales and Use Tax Filing Calendar and Timeliness

**US · Domains: all five · Verdict: 🟡 Partial — the calendar is derivable from jurisdiction data; filing can't be verified (no return or payment record exists)**
**IN counterpart:** [UC-27](../IN/uc-27-return-filing-timeliness.md) (GST return timeliness) · **live evidence 2026-10-04**

---

## 1. Question

> *"Which state returns are due when, are we ready to file them, and what do we lose if we're late?"*

## 2. Statutory basis

- Each registered state sets a **filing frequency** (monthly / quarterly / semi-annual / annual) and a due
  date. *Our understanding (caveat):*

  | State | Return due | Timely-filing discount |
  |---|---|---|
  | Ohio | **23rd** of the following month (R.C. 5739.12) | 0.75% (vendor's discount) |
  | Pennsylvania | **20th** after the period | 1%, capped by filing frequency |
  | Michigan | **20th** after the period | Small prepayment / timely discounts |
  | Illinois | **20th** after the period | 1.75%, capped per return |

  Exact rates and caps go in `us/sales_use_tax.yaml` with sources (G6).
- **Consequence of late filing:** penalty (often a percentage of tax per month, with minimums), interest,
  and the **loss of the timely-filing discount**. The discount is a small but certain saving that lateness
  forfeits outright.
- **Late-entered sales** after a period was filed need an amended return ([US-15](us-15-late-entered-documents.md)).

## 3. Trigger

- **Scheduled daily**, with reminders at T−7 and T−2 before each state's due date.
- **Scheduled monthly** after period end: hand the period's liability from [US-01](us-01-period-sales-use-tax-liability.md)
  into the filing pack.
- **On request.**

## 4. Input contract

| Call | Fields |
|---|---|
| `TaxNexus.list` | `state_code`, `is_registered`, `registered_on`, `filing_frequency`, `next_filing_due`, `status` |
| `TaxJurisdiction.list` | `state_code`, `jurisdiction_level`, `filing_frequency`, `tax_authority_name`, `status` |
| US-01 output | Liability per jurisdiction per period |
| Return / payment record | ❌ **None.** No entity records that a state return was filed or paid |

## 5. Algorithm

1. **Calendar:** for each registered state, generate periods from `registered_on` (or from the ledger
   start) at `filing_frequency`. Due date = the rulebook day after period end.
2. **`filing_due`:** periods due within 7 days, each with the US-01 liability and the discount at stake.
3. **`next_filing_due_missing`:** `TaxNexus.next_filing_due` null for a registered state → `data_quality`.
   The platform's own field doesn't drive anything.
4. **`frequency_conflict`:** a state's `TaxNexus.filing_frequency` ≠ its `TaxJurisdiction` frequencies.
5. **`filing_unverifiable`:** a period past due. With no return record, the agent can't tell filed from
   unfiled. It reports "due on X; no filing evidence in AgentSwitch" and escalates for confirmation.
6. **`registered_state_without_jurisdiction`:** nexus registered but no active jurisdiction rows (or the
   reverse).

### Worked example (REAL, 2026-10-04)

> | State | Registered | Frequency | Next return | Due | `next_filing_due` |
> |---|---|---|---|---|---|
> | OH | 2023-09-17 | monthly | September 2026 | **2026-10-23** | null |
> | MI | 2023-09-17 | quarterly | Q3 2026 (Jul–Sep) | **2026-10-20** | null |
> | PA | 2023-09-17 | quarterly | Q3 2026 | **2026-10-20** | null |
> | IL | not registered (monitoring) | quarterly | — | — | null |
>
> - Frequencies agree between `TaxNexus` and `TaxJurisdiction` (OH monthly for state and Stark County;
>   MI/PA quarterly).
> - `next_filing_due` is null on 4 of 4 → `next_filing_due_missing`.
> - No filing record exists for any period since 2026-01 → every past period is `filing_unverifiable`.
>
> Output: *"MI and PA Q3 returns are due 20 October and Ohio's September return 23 October. AgentSwitch
> holds no record of any filed return, so confirm past filings, especially because 147 invoices were
> entered on 16 September for January–August (US-15)."*

## 6. Known-bad data

- `next_filing_due` null on all `TaxNexus` rows.
- `TaxRateServiceConfig` has 0 rows. That is consistent with `rate_source: manual`, and isn't a finding
  (US README rule 3).

## 7. Output contract

`finding_type: "filing_calendar"`, `rule ∈ {filing_due, next_filing_due_missing, frequency_conflict,
filing_unverifiable, registered_state_without_jurisdiction}`. Fields: `state`, `period`, `due_date`,
`liability` (from US-01), `discount_at_stake`.

## 8. Limits

- Never files or pays a return. There's no filing tool, and filing is outside the platform.
- Until the platform records returns, "filed" can't be verified. The output says so explicitly instead of
  assuming.

## 9. Validation

1. **Live:** the 4-state table, recomputed.
2. **Fixture:** an OH monthly period ending 2026-09-30 → due 2026-10-23; a PA quarterly period ending
   2026-09-30 → due 2026-10-20.
3. **Fixture:** `TaxNexus` quarterly vs jurisdiction monthly for the same state → `frequency_conflict`.

## 10. Open questions

- Ask for a `SalesTaxReturn` record (period, state, filed date, amount paid), or at least for the platform
  to populate `TaxNexus.next_filing_due`. Without one, US-14 and US-15 can't prove compliance.
- Should discount rates be applied to US-01's liability so "file on time" shows a dollar saving?

## 11. Live evidence — actual calls, 2026-10-04

- `TaxNexus.list` → 4:
  - IL: economic, quarterly, not registered;
  - MI, PA: economic, quarterly, registered 2023-09-17;
  - OH: physical, monthly, registered 2023-09-17.
  `next_filing_due: null` on all.
- `TaxJurisdiction.list` → Ohio State Sales Tax 5.75% monthly, Stark County (OH) 0.75% monthly,
  Michigan 6% quarterly, Pennsylvania 6% quarterly.
- `TaxRateServiceConfig.list` → 0 rows.
