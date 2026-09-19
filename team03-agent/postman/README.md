# Postman collection

`AgentSwitch.postman_collection.json` covers every REST/MCP call used or referenced
in this repo: login, whoami, locale, schemas, the bug-report template, and the full
MCP handshake (`initialize` -> `notifications/initialized` -> `tools/list` ->
`tools/call`), including read-only examples (`Invoice.list`, `Invoice.get`,
`TaxLine.list`, `Vendor.list`) and write examples (`Invoice.update`,
`AgentMessage.create`) matching the playbooks.

**The collection itself contains no credentials** — every request uses
`{{base_url}}` / `{{email}}` / `{{password}}` / `{{token}}` variables and is safe to
commit. Real values live in a **Postman Environment** file, which is gitignored.

## Setup

1. In Postman: **Import** → select `AgentSwitch.postman_collection.json`.
2. Get your environment file:
   - Two real ones already exist locally on this machine (not in git):
     `AgentSwitch-Suryodaya.postman_environment.json` and
     `AgentSwitch-Keystone.postman_environment.json`. Import whichever you need.
   - On a fresh machine/teammate's laptop: copy
     `AgentSwitch.postman_environment.example.json`, fill in `email`/`password`,
     rename it to something ending in `.postman_environment.json` (that suffix is
     what `.gitignore` excludes), and import it. **Never commit the filled-in
     copy.**
3. Select the imported environment in Postman's environment dropdown (top right).
4. Run **Auth → Login** first. Its test script reads the response's `token` field
   and saves it into the environment's `{{token}}` variable automatically — every
   other request in the collection uses that via the collection-level Bearer auth.
5. Run **Auth → Whoami** to confirm the token works and matches your account.
6. Under **MCP**, run `initialize` → `notifications/initialized` → `tools/list` in
   order, then any `tools/call` example.

## Folders

- **Auth** — login, whoami, and a control test that confirms an unauthenticated
  request actually gets rejected (401).
- **REST API** — locale, schemas, and a bug-report *template* (field names are a
  best-effort guess from the brief's bug-bar description; confirm the real shape
  against `/api/schemas` or `/docs` before filing anything for real).
- **MCP** — the JSON-RPC handshake, a generic `tools/call` request driven by the
  `{{tool_name}}` / `{{tool_arguments}}` variables, and two example sub-folders:
  - *read-only* examples, safe to run any time.
  - *writes* examples — these mutate real rows in the ledger **shared with Teams
    01 and 02**. Each has a `REPLACE_ME` placeholder id; don't run them without
    editing that first, and only ever hold/flag records, never cancel or
    force-pay (see `playbooks/duplicate_audit.md`).

## Switching jurisdiction

The Suryodaya and Keystone environments only differ in `base_url`, `email` (same
for both), and `password`. Everything else — the collection, the tests, the tool
names — is identical, which is the point: the agent (and this collection) must not
hardcode which jurisdiction it's talking to.
