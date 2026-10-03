# Use-case specs — by jurisdiction

The agent serves two tenants from one codebase, and the use cases differ because the
tax law differs. A use case is written once per jurisdiction where it applies.

| Folder | Tenant | Regime | Specs |
|---|---|---|---|
| [`IN/`](IN/README.md) | Suryodaya Precision Works Pvt. Ltd. | `gst` (India) | UC-01 … UC-22, from [`spec.md`](../planning/spec.md) |
| [`US/`](US/README.md) | Keystone Precision Works LLC | `sales_use_tax` (US) | US-01 … US-10 |

**How they relate.** Every IN use case maps to a US counterpart, to a regime-agnostic
US instance of the same check, or to "no US equivalent", with the reason. The full
mapping is in [`US/README.md`](US/README.md#mapping-from-the-india-use-cases).

**In the harness**, a playbook manifest declares `tax_regimes: [gst]` or
`[sales_use_tax]` (or `[all]` for regime-agnostic checks), and the router picks by the
tenant's locale. See [`../../harness/README.md`](../../harness/README.md).
