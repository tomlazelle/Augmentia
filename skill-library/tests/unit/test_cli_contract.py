import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from sdlc.cli import main

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "validate"]


def test_module_help_lists_every_documented_command():
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    out = subprocess.run([sys.executable, "-m", "sdlc", "--help"], capture_output=True, text=True, env=env, check=True).stdout
    for command in COMMANDS:
        assert command in out


@pytest.mark.parametrize("command", COMMANDS)
def test_each_command_has_help(command, capsys):
    with pytest.raises(SystemExit) as exc:
        main([command, "--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "--root" in out and "--json" in out


def test_usage_error_exits_2(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["allocate-id"])
    assert exc.value.code == 2


def test_unknown_category_exits_2(sb):
    sb.init()
    with pytest.raises(SystemExit) as exc:
        sb.run("allocate-id", "--category", "XX")
    assert exc.value.code == 2


def test_command_outside_project_is_environment_error(sb):
    code, data, _ = sb.run("validate")
    assert code == 2
    assert data["diagnostics"][0]["code"] == "no-project"
    assert data["ok"] is False


def test_root_option_must_point_at_a_project(sb, tmp_path):
    other = tmp_path / "empty"
    other.mkdir()
    code, data, _ = sb.run("list", "--root", str(other))
    assert code == 2


def test_root_defaults_to_nearest_ancestor(sb, monkeypatch):
    sb.init()
    nested = sb.root / "BR"
    monkeypatch.chdir(nested)
    code, data, _ = sb.run("validate")
    assert code == 0


def test_json_envelope_shape_is_stable(proj):
    code, data, _ = proj.run("validate")
    assert set(data) == {"schema_version", "command", "ok", "exit_code", "result", "diagnostics"}
    assert data["schema_version"] == 1 and data["command"] == "validate" and data["ok"] is True
    assert set(data["result"]["summary"]) == {"error", "warning", "notice"}


def test_diagnostic_fields_are_stable(proj):
    (proj.root / "BR" / "junk.md").write_text("no front matter")
    _, data, _ = proj.run("validate")
    diag = data["diagnostics"][0]
    assert set(diag) == {"severity", "code", "message", "path", "id", "line"}


def test_human_output_is_default(proj):
    code, out, _ = proj.run("validate", json_out=False)
    assert code == 0 and "0 error(s)" in out
