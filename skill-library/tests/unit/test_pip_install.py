"""Opt-in: proves `pip install -e .` works. Run with SDLC_TEST_INSTALL=1 (uses --no-build-isolation, so
setuptools must be available in the interpreter; add --system-site-packages if it is not)."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "validate"]

pytestmark = pytest.mark.skipif(os.environ.get("SDLC_TEST_INSTALL") != "1", reason="set SDLC_TEST_INSTALL=1 to run")


def test_editable_install_exposes_module_and_commands(tmp_path):
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(venv)], check=True)
    py = venv / "bin" / "python"
    subprocess.run([str(py), "-m", "pip", "install", "-e", str(ROOT), "--no-build-isolation", "-q"], check=True)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    out = subprocess.run([str(py), "-m", "sdlc", "--help"], capture_output=True, text=True, check=True, cwd=tmp_path, env=env).stdout
    assert all(c in out for c in COMMANDS)
    project = tmp_path / "p"
    project.mkdir()
    subprocess.run([str(py), "-m", "sdlc", "init"], check=True, cwd=project, env=env, capture_output=True)
    assert subprocess.run([str(py), "-m", "sdlc", "validate"], cwd=project, env=env, capture_output=True).returncode == 0


def test_non_editable_install_ships_instruction_templates(tmp_path):
    """Regression: init must find its AGENTS.md/CLAUDE.md templates in a regular (wheel-style) install."""
    import shutil
    src = tmp_path / "src"
    shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns(".venv", "*.egg-info", "__pycache__", ".pytest_cache", "tests"))
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(venv)], check=True)
    py = venv / "bin" / "python"
    subprocess.run([str(py), "-m", "pip", "install", str(src), "--no-build-isolation", "-q"], check=True)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    project = tmp_path / "p"
    project.mkdir()
    subprocess.run([str(py), "-m", "sdlc", "init"], check=True, cwd=project, env=env, capture_output=True)
    for name in ("AGENTS.md", "CLAUDE.md"):
        assert "create-brd" in (project / name).read_text()
