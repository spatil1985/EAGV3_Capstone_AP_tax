# UC-34 — School: GST Charged on Inward Services That Are Exempt (Entry 66(b))

**Domains: school · Category: input tax, domain-specific · Verdict: ⚪ Spec only — the fields exist; no education tenant exists on either instance**
**Status: draft · constructed example · added 2026-10-04 · US counterpart: [US-11](../US/us-11-sales-tax-on-exempt-purchases.md) (nonprofit/government purchase exemption)**

[UC-07](uc-07-school-exempt-taxable-split.md) and [UC-08](uc-08-rule-42-apportionment-school.md) deal
with the school's **outward** exemption and the credit it loses because of it. This use case is the
**inward** side: services sold *to* a school that are themselves exempt, so a vendor who charges GST on
them is charging tax nobody owes.

---

## 1. Question

> *"Are our bus, canteen, security, cleaning and exam vendors charging us GST they shouldn't?"*

---

## 2. Statutory basis

- **Notification 12/2017-CT(R), entry 66(b):** services provided **to an educational institution** are
  exempt when they are:
  - (i) transport of students, faculty and staff;
  - (ii) catering, including mid-day meals under a government scheme;
  - (iii) security, cleaning or housekeeping performed in the institution;
  - (iv) services relating to admission to, or conduct of examinations by, the institution;
  - (v) online educational journals and periodicals.
- *Our understanding (caveat):* items (i)–(iii) apply only to institutions providing pre-school education
  and education up to higher secondary school (or equivalent), not to colleges. Item (v) applies to
  institutions providing higher education leading to a recognised qualification. Confirm against the
  amended notification before relying on it.
- **Why it costs money:** the school's own output (tuition) is exempt (entry 66(a)), so it can't take
  credit for GST it pays ([UC-08](uc-08-rule-42-apportionment-school.md)). GST wrongly charged by a vendor
  is pure cost. The remedy is a vendor credit note ([UC-25](uc-25-vendor-credit-debit-notes-itc.md)) and
  stopping the charge.

---

## 3. Trigger

- **On event:** `bill.created` from a vendor whose lines fall in the exempt classes. Catching it before
  payment is when the money can still be held back.
- **Scheduled monthly** sweep.
- **On request.**
- **Gate:** runs only when `OrgProfile.industry = education`, or the vertical profile says school.

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `OrgProfile.list` | `industry` (`education` gates the playbook) |
| `Bill.list` | `items[]` (`hsn_or_sac`, `description`, tax fields), `taxes[]`, `vendor_id`, `gst_treatment` |
| `Expense.list` | `hsn_or_sac`, `tax_amount`, `description`: for services paid as expenses |
| `Item.list` | `hsn_or_sac`, `product_type`, for item-linked lines |

**Exempt-class table** (`domain/reference/in/education_inward_exempt.yaml`, G6). SAC prefixes are
indicative; the table is the authority:

| Class | Indicative SAC | Notes |
|---|---|---|
| Student/staff transport | 9964 (passenger transport), 996601 (vehicle hire with operator) | School bus contracts |
| Catering / mid-day meal | 9963 (food and beverage services) | Canteen contracts |
| Security | 99852 | Guards on campus |
| Cleaning / housekeeping | 99853 | Performed in the institution |
| Admission / examination services | 9992 (education support) | Exam conduct, admission processing |

---

## 5. Algorithm

1. **Gate:** the tenant is a school (above). Otherwise route as `not_applicable`.
2. For each bill or expense line whose SAC (or description, when SAC is missing) matches an exempt class,
   **and** carries tax above 0 → `exempt_service_charged_gst`. Exposure = tax charged.
3. **Group by vendor:** a vendor charging on every bill → `vendor_charges_gst_on_exempt_service`, with the
   year-to-date total. This is the conversation to have with the vendor.
4. **Exclude** lines whose vendor is unregistered (no GST charged) and lines the playbook table marks as
   outside the exemption (e.g. a college for classes (i)–(iii)).

### Worked example (CONSTRUCTED: no school tenant exists)

> School "Vidya Niketan" (pre-primary to class XII). Bill from a bus operator for September: ₹2,40,000
> taxable, SAC 996601, CGST ₹14,400 + SGST ₹14,400 (6% + 6%).
> ```
> class = student transport (entry 66(b)(i)) → exempt to a school up to higher secondary
> tax charged = ₹28,800 → not creditable (output exempt) → pure cost
> ```
> Output: *"Your bus operator charged ₹28,800 GST in September on transport that is exempt for a school.
> Ask for a credit note and stop paying the GST."*

---

## 6. Known-bad data

- **22% of bill lines on Suryodaya have no HSN/SAC** ([UC-02](uc-02-blocked-credit-audit.md) §11). A
  school tenant with the same gaps would fall back to description matching, which is weaker, and must say
  so.
- Rule 0 line validity applies before the tax on a line is trusted.

---

## 7. Output contract

`finding_type: "exempt_inward_service"`, `rule ∈ {exempt_service_charged_gst,
vendor_charges_gst_on_exempt_service, sac_missing}`. Exposure is the GST charged, which is the amount
recoverable from the vendor.

---

## 8. Limits

- Never tells the vendor or edits a bill. It produces the evidence for a human to request a credit note.
- Legal scope (school vs college, "in such institution") is in the playbook table, flagged for
  confirmation, not decided by the agent.

---

## 9. Validation

1. **Fixture:** transport line with SAC 996601 and tax 28,800 at a school → finding. The same at a
   manufacturer → `not_applicable`.
2. **Fixture:** a security line at a college → excluded (classes (i)–(iii) are school-only).
3. **No live validation possible.** There's no education tenant, and §9 says so plainly (assignment §5).

---

## 10. Open questions

- Should `OrgProfile.industry` drive vertical routing directly? It exists, with `education`,
  `healthcare`, `retail`, `consulting`, etc. That is simpler than inferring the vertical from the `Item`
  mix (spec.md §7.1).
- Hostel and boarding services: exempt as part of education, or taxable accommodation? Advance rulings
  differ. Keep this as a table entry marked "disputed".

---

## 11. Live evidence — actual calls, 2026-10-04

- `OrgProfile.list` → both tenants report `industry: manufacturing`. **No education tenant**, so the
  playbook routes `not_applicable` on both today.
- The schema confirms `Bill.items[].hsn_or_sac`, `Expense.hsn_or_sac`, and the `OrgProfile.industry`
  options (`education | manufacturing | retail | healthcare | technology | consulting | … | non_profit |
  government | other`).
