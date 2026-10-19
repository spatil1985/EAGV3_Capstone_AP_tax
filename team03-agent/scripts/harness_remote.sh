#!/usr/bin/env bash
# shellcheck shell=bash
# Run the AgentSwitch harness on the server (the API behind "Our harness → Submit for a run").
#
#   team03-agent/scripts/harness_remote.sh preflight     # is origin/main what passed locally?
#   team03-agent/scripts/harness_remote.sh status        # saved harness + latest server runs
#   team03-agent/scripts/harness_remote.sh submit        # preflight, confirm, queue a run
#   team03-agent/scripts/harness_remote.sh discover      # list the platform's harness endpoints
#
# The server runs whatever is on origin/main, and one submission locks you out for 3 days,
# so preflight checks that the commit it will check out is the one that passed
# run_harness_local.sh on both instances. submit refuses unless preflight passes, then
# asks you to type "submit" before it calls POST /api/harness-runs/mine.
#
# Every command except preflight logs in like harness_env.sh (Suryodaya account, reads
# team03-agent/.env). The token goes over stdin to curl, never on a command line, and is
# never printed.

set -uo pipefail

repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || { echo "not inside the repo" >&2; exit 1; }
history="$repo_root/team03-agent/harness/results/HISTORY.md"
instances=(suryodaya keystone)

# What the server's run depends on. Docs and saved results are left out, so committing them
# doesn't invalidate a local run.
code_paths=(team03-agent/harness team03-agent/aptax team03-agent/scripts team03-agent/playbooks
            team03-agent/requirements.txt ':(exclude)*.md' ':(exclude)team03-agent/harness/results'
            # Local-only helpers: the server never runs these.
            ':(exclude)team03-agent/scripts/harness_remote.sh' ':(exclude)team03-agent/scripts/harness_env.sh'
            ':(exclude)team03-agent/scripts/run_harness_local.sh')

newest_matching_run() {  # newest_matching_run INSTANCE MAIN_SHA -> HISTORY.md row or nothing
  local row sha
  grep -E "^\| [0-9TZ]+ \| $1 \| \`[0-9a-f]+(-dirty)?\` " "$history" | awk '{ r[NR] = $0 } END { for (i = NR; i > 0; i--) print r[i] }' \
    | while IFS= read -r row; do
        sha=$(printf '%s' "$row" | sed -nE 's/^[^`]*`([0-9a-f]+)(-dirty)?`.*/\1/p')
        if git -C "$repo_root" cat-file -e "$sha^{commit}" 2>/dev/null \
           && git -C "$repo_root" diff --quiet "$sha" "$2" -- "${code_paths[@]}" 2>/dev/null; then
          printf '%s\n' "$row"
          break
        fi
      done
}

preflight() {
  local ok=0 head main i row
  git -C "$repo_root" fetch -q origin main || { echo "✗ could not fetch origin/main" >&2; return 1; }
  main=$(git -C "$repo_root" rev-parse --short origin/main)
  head=$(git -C "$repo_root" rev-parse --short HEAD)
  echo "server will run: origin/main @ $main"

  if [ "$head" = "$main" ]; then
    echo "✓ local HEAD is origin/main"
  else
    echo "✗ local HEAD is $head, not origin/main ($main) — local results may not describe the server's commit"
    ok=1
  fi

  if ! git -C "$repo_root" diff --quiet origin/main -- "${code_paths[@]}" 2>/dev/null; then
    echo "✗ harness/agent code in your working tree differs from origin/main — merge it first, or it won't be in the run"
    ok=1
  fi

  [ -f "$history" ] || { echo "✗ no $history — run scripts/run_harness_local.sh both first"; return 1; }
  for i in "${instances[@]}"; do
    # Newest run for this instance whose commit has the same code as origin/main. Committing
    # results moves HEAD without touching code, so the run's own sha rarely equals main.
    row=$(newest_matching_run "$i" "$main")
    if [ -z "$row" ]; then
      echo "✗ $i: no local run on code identical to $main — run scripts/run_harness_local.sh $i"
      ok=1
    elif ! printf '%s' "$row" | grep -q '| valid |'; then
      echo "✗ $i: last local run on $main failed the results.json contract"
      ok=1
    else
      # Summary column looks like "suryodaya: 40/40 passed · goldens 3/3 exact".
      local summary passed total
      summary=$(printf '%s' "$row" | awk -F' \\| ' '{print $4}')
      passed=$(printf '%s' "$summary" | sed -nE 's/.*: ([0-9]+)\/([0-9]+) passed.*/\1/p')
      total=$(printf '%s' "$summary" | sed -nE 's/.*: ([0-9]+)\/([0-9]+) passed.*/\2/p')
      if [ -n "$passed" ] && [ "$passed" = "$total" ]; then
        echo "✓ $summary"
      else
        echo "✗ $summary"
        ok=1
      fi
      local run_sha
      run_sha=$(printf '%s' "$row" | sed -nE 's/^[^`]*`([0-9a-f]+)(-dirty)?`.*/\1/p')
      [ "$run_sha" = "$main" ] || echo "  ran on $run_sha: differs from $main only outside the code"
      case "$row" in *"$run_sha-dirty"*)
        echo "  note: that run had uncommitted changes; fine if they were outside the harness/agent code" ;;
      esac
    fi
  done

  echo
  if [ "$ok" -eq 0 ]; then
    echo "READY. Submit in AgentSwitch → Our harness → Submit for a run (3-day cooldown applies)."
    echo "Then add the run to the table in team03-agent/docs/HARNESS.md §8."
  else
    echo "NOT READY — fix the ✗ items above before spending a submission."
  fi
  return "$ok"
}

discover() {
  (
    cd "$repo_root" || exit 1
    # shellcheck source=/dev/null
    source team03-agent/scripts/harness_env.sh suryodaya >/dev/null || exit 1
    spec=$(mktemp "${TMPDIR:-/tmp}/agentswitch-openapi.XXXXXX")
    trap 'rm -f "$spec"' EXIT
    code=$(printf 'Authorization: Bearer %s\n' "$AGENTSWITCH_TOKEN" \
           | curl -sS -H @- -o "$spec" -w '%{http_code}' "$AGENTSWITCH_BASE_URL/openapi.json") || exit 1
    if [ "$code" != 200 ]; then
      echo "openapi.json returned HTTP $code" >&2
      exit 1
    fi
    python3 - "$spec" <<'EOF'
import json, re, sys
spec = json.load(open(sys.argv[1]))
hits = []
for path, ops in spec.get("paths", {}).items():
    for method, op in ops.items():
        if not isinstance(op, dict):
            continue
        text = " ".join([path, op.get("summary", ""), op.get("operationId", ""), " ".join(op.get("tags", []))])
        if re.search(r"harness|submission|eval", text, re.I):
            hits.append(f"{method.upper():6} {path}  — {op.get('summary') or op.get('operationId') or ''}")
print("\n".join(sorted(hits)) or "no harness-related endpoints in the spec")
EOF
  )
}

api() {  # api METHOD PATH -> body on stdout; needs AGENTSWITCH_TOKEN/BASE_URL (call inside with_login)
  printf 'Authorization: Bearer %s\n' "$AGENTSWITCH_TOKEN" \
    | curl -sS -X "$1" -H @- -H 'Accept: application/json' -w '\n%{http_code}' "$AGENTSWITCH_BASE_URL$2"
}

with_login() {  # with_login FUNC -> runs FUNC in a subshell logged in to Suryodaya
  (
    cd "$repo_root" || exit 1
    # shellcheck source=/dev/null
    source team03-agent/scripts/harness_env.sh suryodaya >/dev/null 2>&1 \
      || { echo "login failed (check team03-agent/.env)" >&2; exit 1; }
    "$1"
  )
}

show_runs() {  # stdin: GET /api/harness-runs/mine body + status line
  python3 -c '
import json, sys
raw = sys.stdin.read()
body, _, code = raw.rpartition("\n")
if code != "200":
    sys.exit(f"harness-runs/mine returned HTTP {code}: {body[:300]}")
runs = json.loads(body)
runs = runs if isinstance(runs, list) else runs.get("runs") or runs.get("items") or []
for r in runs[:5]:
    score = r.get("score")
    score = "-" if score is None else f"{score:.3f}"
    passed, total = r.get("tasks_passed"), r.get("tasks_total")
    tally = f"{passed:g}/{total:g}" if passed is not None and total else "-"
    when, status, sha, rid = r.get("submitted_at"), r.get("status") or "", (r.get("commit_sha") or "")[:7], r.get("id")
    print(f"{when}  {status:9}  {sha}  {tally:>7}  score {score}  id {rid}")
    for line in (r.get("summary") or "").splitlines():
        print(f"    {line}")
if not runs:
    print("no server runs yet")
'
}

_status() {
  local body
  body=$(api GET /api/team-harness/mine)
  printf '%s' "${body%$'\n'*}" | python3 -c '
import json, sys
h = (json.load(sys.stdin) or {}).get("harness") or {}
print("saved harness:", h.get("repo_url"), "@", h.get("branch"), " (updated", str(h.get("updated_at")) + ")")'
  api GET /api/harness-runs/mine | show_runs
}

_submit() {
  local resp code body
  resp=$(api POST /api/harness-runs/mine)
  code=${resp##*$'\n'}
  body=${resp%$'\n'*}
  echo "HTTP $code"
  printf '%s\n' "$body" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$body"
  [ "$code" = 200 ] || [ "$code" = 201 ] || [ "$code" = 202 ]
}

submit() {
  preflight || { echo "submit: preflight failed, not submitting" >&2; return 1; }
  echo
  with_login _status || return 1
  echo
  echo "This queues an official run of origin/main and starts the 3-day cooldown."
  read -r -p 'Type "submit" to queue it: ' answer
  [ "$answer" = submit ] || { echo "not submitted"; return 1; }
  with_login _submit || { echo "submit failed" >&2; return 1; }
  echo
  echo "Queued. Check progress with: $0 status   (a run takes about 10 minutes)"
}

case "${1:-}" in
  preflight) preflight ;;
  status) with_login _status ;;
  submit) submit ;;
  discover) discover ;;
  *) echo "usage: $0 preflight|status|submit|discover" >&2; exit 2 ;;
esac
