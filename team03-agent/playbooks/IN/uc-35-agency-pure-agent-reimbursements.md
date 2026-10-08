---
id: uc-35
title: Recharged costs and the pure-agent test (Rule 33)
capability: recharges
description: >-
  UC-35 (India, GST; agencies especially): checks costs passed back to clients — recharges that fail
  the Rule 33 pure-agent test but were charged below the service rate, pure-agent costs on which credit
  was also claimed, invoiced recharges that can't be traced to any invoice, billable costs left
  unbilled, and expenses whose billable flag and status disagree.
questions:
  - "When we pass client costs back to them, are we charging GST correctly on the recharge?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Expense.list, Invoice.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc35_pure_agent_recharges:PureAgentRecharges
tools: [Expense.list, Invoice.list]
escalate: digest
spec: docs/usecases/IN/uc-35-agency-pure-agent-reimbursements.md
---

# UC-35 · Recharged costs and the pure-agent test — SOP

**Full spec:** [`docs/usecases/IN/uc-35-agency-pure-agent-reimbursements.md`](../../docs/usecases/IN/uc-35-agency-pure-agent-reimbursements.md)
**Code:** [`scripts/uc/IN/uc35_pure_agent_recharges.py`](../../scripts/uc/IN/uc35_pure_agent_recharges.py)

## When it runs
Monthly, when an invoice or a recharge is created, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `recharge_unlinked` | Billable expense marked invoiced; no invoice links to it (by `expense_id`, or customer + amount within 30 days) |
| `reimbursement_undertaxed` | Linked recharge fails the pure-agent test and carries less than 18% |
| `pure_agent_with_itc` | Passes the test, yet credit was claimed on the expense |
| `billable_not_recharged` | Billable and still unbilled after 60 days |
| `billable_flag_conflict` (data_quality) | `unbilled` while `is_billable` is off (aggregate) |

Pure-agent contract clauses come from `config/overrides/pure_agent_contracts.yaml`, since the data
model has none.

## How to explain the result
On this tenant no invoice carries `expense_id`, so every invoiced recharge is untraceable: say so
rather than calling them compliant. A recharge is taxed at our service rate unless every Rule 33
condition holds.

## Limits
Exposure figures inherit UC-33's doubts about expense amounts.
