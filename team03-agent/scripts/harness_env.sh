# shellcheck shell=bash
# Recreate the AgentSwitch harness runner's environment on a laptop (local runs only).
#
#   source team03-agent/scripts/harness_env.sh suryodaya   # or keystone
#   cd team03-agent && python -m harness
#
# Logs in with the seat's email/password -- from the environment, else from
# team03-agent/.env (or the file in AGENTSWITCH_ENV_FILE) -- and exports what the server
# gives a run: AGENTSWITCH_BASE_URL, AGENTSWITCH_TOKEN, AGENTSWITCH_INSTANCE.
# The password reaches curl on stdin, never on a command line; the token is never printed
# in full or written to disk. Works in bash and zsh.

_ase_sourced=0
if [ -n "${ZSH_VERSION:-}" ]; then
  case "${ZSH_EVAL_CONTEXT:-}" in *:file*) _ase_sourced=1 ;; esac
elif [ -n "${BASH_VERSION:-}" ]; then
  [ "${BASH_SOURCE[0]}" != "$0" ] && _ase_sourced=1
fi
if [ "$_ase_sourced" != 1 ]; then
  echo "usage: source $0 suryodaya|keystone  (use 'source': run directly, the exports would be lost)" >&2
  exit 1
fi
unset _ase_sourced

_ase_dotenv() {  # _ase_dotenv KEY FILE -> KEY's value in FILE, surrounding quotes removed
  local v
  { [ -n "$2" ] && [ -f "$2" ]; } || return 0
  v=$(sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$2" | tail -n 1)
  v=${v%$'\r'}
  case "$v" in
    \"*\") v=${v#\"}; v=${v%\"} ;;
    \'*\') v=${v#\'}; v=${v%\'} ;;
  esac
  printf '%s' "$v"
}

_ase_json_field() {  # _ase_json_field KEY... < json -> first non-empty KEY at top level or under "user"
  python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
d = d if isinstance(d, dict) else {}
u = d.get("user") if isinstance(d.get("user"), dict) else {}
for k in sys.argv[1:]:
    v = d.get(k) or u.get(k)
    if v:
        print(v)
        break
' "$@"
}

_ase_main() {
  local instance="${1:-}" url prefix env_file email password resp code body token user
  case "$instance" in
    suryodaya) url="https://agentswitch.theschoolofai.in"; prefix="AGENTSWITCH" ;;
    keystone)  url="https://class.agentswitch.theschoolofai.in"; prefix="US_AGENTSWITCH" ;;
    *) echo "usage: source scripts/harness_env.sh suryodaya|keystone" >&2; return 2 ;;
  esac

  env_file="${AGENTSWITCH_ENV_FILE:-}"
  if [ -z "$env_file" ]; then
    if [ -f team03-agent/.env ]; then env_file="team03-agent/.env"; elif [ -f .env ]; then env_file=".env"; fi
  fi
  email=$(printenv "${prefix}_EMAIL")
  password=$(printenv "${prefix}_PASSWORD")
  [ -n "$email" ] || email=$(_ase_dotenv "${prefix}_EMAIL" "$env_file")
  [ -n "$password" ] || password=$(_ase_dotenv "${prefix}_PASSWORD" "$env_file")
  if [ -z "$email" ] || [ -z "$password" ]; then
    echo "set ${prefix}_EMAIL and ${prefix}_PASSWORD (in the environment or team03-agent/.env)" >&2
    return 1
  fi

  resp=$(AS_EMAIL="$email" AS_PASSWORD="$password" python3 -c \
           'import json, os; print(json.dumps({"email": os.environ["AS_EMAIL"], "password": os.environ["AS_PASSWORD"]}))' \
         | curl -sS -X POST "$url/api/auth/login" -H 'Content-Type: application/json' \
             --data-binary @- -w '\n%{http_code}') \
    || { echo "login request to $url failed" >&2; return 1; }
  code=${resp##*$'\n'}
  body=${resp%$'\n'*}
  if [ "$code" != "200" ]; then
    echo "login failed: HTTP $code $(printf '%s' "$body" | _ase_json_field detail error message)" >&2
    return 1
  fi
  token=$(printf '%s' "$body" | _ase_json_field token)
  if [ -z "$token" ]; then
    echo "login response has no token" >&2
    return 1
  fi

  resp=$(printf 'Authorization: Bearer %s\n' "$token" | curl -sS "$url/api/auth/me" -H @- -w '\n%{http_code}') \
    || { echo "token check against $url failed" >&2; return 1; }
  code=${resp##*$'\n'}
  body=${resp%$'\n'*}
  if [ "$code" != "200" ]; then
    echo "token check failed: HTTP $code" >&2
    return 1
  fi
  user=$(printf '%s' "$body" | _ase_json_field email)

  export AGENTSWITCH_BASE_URL="$url" AGENTSWITCH_TOKEN="$token" AGENTSWITCH_INSTANCE="$instance"
  echo "instance=$instance user=${user:-?} token=${token:0:8}…"
  echo "note: AGENTSWITCH_* in this shell now target $instance; use a fresh shell for other aptax commands" >&2
}

_ase_main "$@"
_ase_rc=$?
unset -f _ase_main _ase_dotenv _ase_json_field
return "$_ase_rc"
