"""LLM-generated, not graded. agentswitch-harness.toml agrees with the harness code."""

import subprocess
import sys
import tomllib
from pathlib import Path

import harness.__main__ as hm
from harness import tasks as T

AGENT_DIR = Path(__file__).resolve().parents[2]
GIT_ROOT = AGENT_DIR.parent
CFG = tomllib.loads((GIT_ROOT / "agentswitch-harness.toml").read_text(encoding="utf-8"))


def test_toml_values():
    assert CFG["install"] == "pip install -r team03-agent/requirements.txt"
    assert CFG["run"] == "cd team03-agent && python -m harness"
    assert CFG["instances"] == ["suryodaya", "keystone"]
    assert CFG["timeout_minutes"] == 20
    assert set(CFG["instances"]) <= set(T.INSTANCES)
    assert hm.DEADLINE_SECONDS < CFG["timeout_minutes"] * 60


def test_results_path_matches_toml():
    assert (GIT_ROOT / CFG["results"]).resolve() == hm.RESULTS_PATH


def test_requirements_cover_harness_imports():
    reqs = (AGENT_DIR / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "requests" in reqs and "pyyaml" in reqs


def test_results_file_is_gitignored():
    proc = subprocess.run(["git", "check-ignore", "-q", "team03-agent/results.json"], cwd=GIT_ROOT)
    assert proc.returncode == 0


def test_runs_from_another_cwd_and_writes_the_toml_path(tmp_path):
    """No server env vars → one failed task, written where the toml says even from another cwd."""
    target = GIT_ROOT / CFG["results"]
    target.unlink(missing_ok=True)
    proc = subprocess.run([sys.executable, "-m", "harness"], cwd=tmp_path,
                          env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(AGENT_DIR)},
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert "harness:environment" in proc.stdout
    assert target.exists() and not (tmp_path / "results.json").exists()


def test_harness_import_chain_avoids_python_311_only_names():
    """The server's Python is unknown (>= 3.10): datetime.UTC only exists from 3.11."""
    offenders = [f"{p.relative_to(AGENT_DIR)}:{i}"
                 for top in ("aptax", "scripts", "harness") for p in (AGENT_DIR / top).rglob("*.py")
                 for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
                 if "import" in line and "datetime" in line and " UTC" in line.replace(",", " ")]
    assert offenders == []
