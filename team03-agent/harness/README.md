# harness — AgentSwitch server runs

`agentswitch-harness.toml` (git root) tells the AgentSwitch server how to run us.
"Our harness → Submit for a run" checks out the saved commit and runs `install`. It then
runs `cd team03-agent && python -m harness` once per instance (suryodaya, keystone)
against a fresh copy of that instance, and reads `team03-agent/results.json`. You get one
run every 3 days.

The harness runs every live aptax playbook in **dry-run**. Each playbook becomes one task:
`passed` means it ran with no error and no failed MCP call, and `score` is 1.0 when it
reproduced its figure in `goldens.yaml` (0.5 when it didn't). Blocked and spec-only
playbooks are not tasks; the `routing_floor` task lists their ids.
Full explanation with diagrams: [`docs/HARNESS.md`](../docs/HARNESS.md). Design:
`docs/superpowers/specs/2026-10-12-agentswitch-harness-design.md`.

## Run it locally (same env vars as the server)

```bash
source team03-agent/scripts/harness_env.sh suryodaya      # or keystone; reads team03-agent/.env
cd team03-agent && python -m harness && python -m harness.validate results.json
```

Use a fresh shell afterwards for other `aptax` commands: the script points `AGENTSWITCH_*`
at the instance you chose.
