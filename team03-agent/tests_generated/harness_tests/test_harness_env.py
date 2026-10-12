"""LLM-generated, not graded. scripts/harness_env.sh against a fake curl (no network)."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

AGENT_DIR = Path(__file__).resolve().parents[2]
TOKEN = "abcdefgh12345678"
PASSWORD = 'pa"ss $HOME word'
FAKE_CURL = r'''#!/bin/bash
printf '%s\n' "$*" >> "$FAKE_LOG"
case "$*" in
  *api/auth/login*) cat > "$FAKE_BODY"; printf '%s\n%s' "$FAKE_LOGIN_BODY" "${FAKE_LOGIN_CODE:-200}" ;;
  *api/auth/me*) cat > /dev/null; printf '%s\n%s' '{"email": "team03@theschoolofai.in"}' "${FAKE_ME_CODE:-200}" ;;
  *) echo "unexpected curl call: $*" >&2; exit 7 ;;
esac
'''
PROBE = ('source scripts/harness_env.sh "$@"; rc=$?; '
         'printf "RC=%s\\nURL=%s\\nTOKEN=%s\\nINSTANCE=%s\\n" "$rc" "${AGENTSWITCH_BASE_URL:-}" '
         '"${AGENTSWITCH_TOKEN:-}" "${AGENTSWITCH_INSTANCE:-}"')
PROBE_KEYS = {"RC", "URL", "TOKEN", "INSTANCE"}


@pytest.fixture
def fake(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(FAKE_CURL)
    curl.chmod(0o755)
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "HOME": str(tmp_path),
           "FAKE_LOG": str(tmp_path / "argv.log"), "FAKE_BODY": str(tmp_path / "body.json"),
           "FAKE_LOGIN_BODY": json.dumps({"token": TOKEN}),
           "AGENTSWITCH_ENV_FILE": str(tmp_path / "no.env")}
    return tmp_path, env


def source(env, *args, shell="bash"):
    proc = subprocess.run([shell, "-c", PROBE, "probe", *args], cwd=AGENT_DIR, env=env,
                          capture_output=True, text=True, timeout=30)
    vals = {}
    script_lines = []
    for line in proc.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in PROBE_KEYS:
            vals[key] = value
        else:
            script_lines.append(line)
    return proc, vals, "\n".join(script_lines)


def test_success_keystone_exports_and_hides_secrets(fake):
    tmp, env = fake
    env.update(US_AGENTSWITCH_EMAIL="team03@theschoolofai.in", US_AGENTSWITCH_PASSWORD=PASSWORD)
    proc, vals, own_out = source(env, "keystone")
    assert vals == {"RC": "0", "URL": "https://class.agentswitch.theschoolofai.in", "TOKEN": TOKEN,
                    "INSTANCE": "keystone"}, proc.stderr
    assert json.loads((tmp / "body.json").read_text()) == {"email": "team03@theschoolofai.in",
                                                            "password": PASSWORD}
    assert PASSWORD not in (tmp / "argv.log").read_text()
    assert TOKEN not in (tmp / "argv.log").read_text()
    assert "instance=keystone user=team03@theschoolofai.in token=abcdefgh…" in own_out
    assert TOKEN not in own_out and TOKEN not in proc.stderr
    assert PASSWORD not in proc.stdout + proc.stderr


def test_suryodaya_uses_the_india_prefix_and_url(fake):
    _, env = fake
    env.update(AGENTSWITCH_EMAIL="a@b", AGENTSWITCH_PASSWORD="pw",
               US_AGENTSWITCH_EMAIL="x@y", US_AGENTSWITCH_PASSWORD="wrong")
    _, vals, _ = source(env, "suryodaya")
    assert vals["RC"] == "0" and vals["URL"] == "https://agentswitch.theschoolofai.in"


def test_reads_dotenv_when_env_is_unset(fake):
    tmp, env = fake
    dotenv = tmp / "team.env"
    dotenv.write_text('AGENTSWITCH_PASSWORD=india\nUS_AGENTSWITCH_EMAIL=team03@theschoolofai.in\n'
                      'US_AGENTSWITCH_PASSWORD="from file"\n')
    env["AGENTSWITCH_ENV_FILE"] = str(dotenv)
    _, vals, _ = source(env, "keystone")
    assert vals["RC"] == "0"
    assert json.loads((tmp / "body.json").read_text())["password"] == "from file"


def test_environment_beats_dotenv(fake):
    tmp, env = fake
    dotenv = tmp / "team.env"
    dotenv.write_text("US_AGENTSWITCH_EMAIL=file@x\nUS_AGENTSWITCH_PASSWORD=file\n")
    env.update(AGENTSWITCH_ENV_FILE=str(dotenv), US_AGENTSWITCH_EMAIL="env@x", US_AGENTSWITCH_PASSWORD="env")
    source(env, "keystone")
    assert json.loads((tmp / "body.json").read_text()) == {"email": "env@x", "password": "env"}


def test_login_failure_exports_nothing(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD="bad",
               FAKE_LOGIN_CODE="401", FAKE_LOGIN_BODY='{"detail": "Invalid credentials"}')
    proc, vals, _ = source(env, "keystone")
    assert vals == {"RC": "1", "URL": "", "TOKEN": "", "INSTANCE": ""}
    assert "HTTP 401" in proc.stderr and "Invalid credentials" in proc.stderr


def test_token_check_failure_exports_nothing(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD="pw", FAKE_ME_CODE="401")
    proc, vals, _ = source(env, "keystone")
    assert vals["RC"] == "1" and vals["TOKEN"] == ""
    assert "token check failed: HTTP 401" in proc.stderr


def test_missing_credentials(fake):
    tmp, env = fake
    proc, vals, _ = source(env, "keystone")
    assert vals["RC"] == "1"
    assert "US_AGENTSWITCH_EMAIL" in proc.stderr
    assert not (tmp / "argv.log").exists()


@pytest.mark.parametrize("args", [(), ("atlantis",)])
def test_bad_instance(fake, args):
    _, env = fake
    proc, vals, _ = source(env, *args)
    assert vals["RC"] == "2" and "usage" in proc.stderr


def test_refuses_to_run_unsourced(fake):
    _, env = fake
    proc = subprocess.run(["bash", "scripts/harness_env.sh", "keystone"], cwd=AGENT_DIR, env=env,
                          capture_output=True, text=True, timeout=30)
    assert proc.returncode == 1 and "source" in proc.stderr


def test_warns_that_the_shell_now_targets_the_instance(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD="pw")
    proc, _, _ = source(env, "keystone")
    assert "AGENTSWITCH_* in this shell now target keystone" in proc.stderr


@pytest.mark.skipif(shutil.which("zsh") is None, reason="zsh not installed")
def test_works_in_zsh(fake):
    _, env = fake
    env.update(US_AGENTSWITCH_EMAIL="a@b", US_AGENTSWITCH_PASSWORD=PASSWORD)
    proc, vals, _ = source(env, "keystone", shell="zsh")
    assert vals["RC"] == "0" and vals["TOKEN"] == TOKEN, proc.stderr
