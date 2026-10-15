#!/usr/bin/env bash
# shellcheck shell=bash
# Run the AgentSwitch harness locally and keep a versioned copy of the result.
#
#   team03-agent/scripts/run_harness_local.sh suryodaya          # or keystone, or both
#
# For each instance: log in via harness_env.sh, run `python -m harness` (dry-run, never
# writes), validate results.json, then copy it and the console log to
#
#   team03-agent/harness/results/<instance>/<UTC timestamp>_<git sha>[-dirty].json / .log
#
# and append one row to team03-agent/harness/results/HISTORY.md. Nothing is committed;
# review and `git add team03-agent/harness/results` yourself. The token is never written:
# the one line that shows its prefix is redacted in the saved log.
#
# Exit code: 0 when every instance ran and validated, 1 otherwise.

set -uo pipefail

usage() { echo "usage: $0 suryodaya|keystone|both" >&2; exit 2; }
[ $# -eq 1 ] || usage
case "$1" in
  suryodaya|keystone) instances=("$1") ;;
  both) instances=(suryodaya keystone) ;;
  *) usage ;;
esac

repo_root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || { echo "not inside the repo" >&2; exit 1; }
agent_dir="$repo_root/team03-agent"
out_root="$agent_dir/harness/results"
python="$repo_root/.venv/bin/python"
[ -x "$python" ] || python=python3

sha=$(git -C "$repo_root" rev-parse --short HEAD)
git -C "$repo_root" diff --quiet HEAD -- || sha="$sha-dirty"

run_one() {  # run_one INSTANCE -> 0 if the harness ran and results.json validated
  local instance=$1 stamp dest log summary verdict rc=0
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  dest="$out_root/$instance"
  mkdir -p "$dest"
  log="$dest/${stamp}_${sha}.log"

  echo "=== $instance · $stamp · $sha ==="
  # Subshell: harness_env.sh exports AGENTSWITCH_* for this instance only, so a second
  # instance (or the caller's shell) never inherits the first one's token.
  (
    cd "$repo_root" || exit 1
    # shellcheck source=/dev/null
    source team03-agent/scripts/harness_env.sh "$instance" || exit 3
    cd "$agent_dir" && "$python" -m harness
  ) 2>&1 | sed -E 's/(token=)[^ ]+/\1<redacted>/' | tee "$log"
  rc=${PIPESTATUS[0]}

  if [ "$rc" -eq 3 ]; then
    echo "login failed for $instance — no harness run, nothing versioned" >&2
    rm -f "$log"
    rmdir "$dest" "$out_root" 2>/dev/null
    return 1
  fi
  if [ ! -f "$agent_dir/results.json" ]; then
    echo "harness wrote no results.json" >&2
    return 1
  fi

  cp "$agent_dir/results.json" "$dest/${stamp}_${sha}.json"
  if (cd "$agent_dir" && "$python" -m harness.validate results.json) >>"$log" 2>&1; then
    verdict="valid"
  else
    verdict="INVALID"; rc=1
  fi
  summary=$("$python" -c 'import json,sys; print(json.load(open(sys.argv[1])).get("summary",""))' \
            "$dest/${stamp}_${sha}.json")

  local history="$out_root/HISTORY.md"
  if [ ! -f "$history" ]; then
    printf '%s\n\n%s\n%s\n' "# Local harness runs" \
      "| UTC | Instance | Commit | Summary | Contract | Files |" \
      "|---|---|---|---|---|---|" > "$history"
  fi
  printf '| %s | %s | `%s` | %s | %s | [json](%s/%s_%s.json) · [log](%s/%s_%s.log) |\n' \
    "$stamp" "$instance" "$sha" "$summary" "$verdict" \
    "$instance" "$stamp" "$sha" "$instance" "$stamp" "$sha" >> "$history"

  echo "saved: ${dest#"$repo_root"/}/${stamp}_${sha}.{json,log}  ($verdict)"
  return "$rc"
}

status=0
for i in "${instances[@]}"; do
  run_one "$i" || status=1
done
exit "$status"
