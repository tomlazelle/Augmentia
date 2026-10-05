import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILLS = sorted(p.name for p in (ROOT / "skills").iterdir())
ADAPTERS = {"claude_code": (".claude", "skills"), "codex": (".agents", "skills")}


def run(adapter, *args, home):
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run([sys.executable, str(ROOT / "install" / f"{adapter}.py"), *args],
                          capture_output=True, text=True, env=env)


@pytest.mark.parametrize("adapter,parts", ADAPTERS.items())
def test_user_scope_links_every_skill_without_copying(adapter, parts, tmp_path):
    proc = run(adapter, home=tmp_path)
    assert proc.returncode == 0, proc.stderr
    base = tmp_path.joinpath(*parts)
    assert sorted(p.name for p in base.iterdir()) == SKILLS
    for name in SKILLS:
        link = base / name
        assert link.is_symlink() and link.resolve() == (ROOT / "skills" / name).resolve()
        assert (link / "SKILL.md").read_text() == (ROOT / "skills" / name / "SKILL.md").read_text()


@pytest.mark.parametrize("adapter,parts", ADAPTERS.items())
def test_project_scope_and_idempotence(adapter, parts, tmp_path):
    project = tmp_path / "proj"
    project.mkdir()
    assert run(adapter, "--scope", "project", "--project-dir", str(project), home=tmp_path).returncode == 0
    again = run(adapter, "--scope", "project", "--project-dir", str(project), home=tmp_path)
    assert again.returncode == 0 and "installed" not in again.stdout and "unchanged" in again.stdout
    assert (project.joinpath(*parts) / "sdlc-init").is_symlink()


@pytest.mark.parametrize("adapter,parts", ADAPTERS.items())
def test_source_edits_are_visible_through_the_link(adapter, parts, tmp_path):
    run(adapter, "--skill", "sdlc-init", home=tmp_path)
    linked = tmp_path.joinpath(*parts) / "sdlc-init"
    assert linked.is_symlink() and not any(p.is_symlink() for p in linked.iterdir())
    assert linked.resolve() == (ROOT / "skills" / "sdlc-init").resolve()


@pytest.mark.parametrize("adapter,parts", ADAPTERS.items())
def test_conflicts_are_reported_and_never_destroyed(adapter, parts, tmp_path):
    base = tmp_path.joinpath(*parts)
    (base / "sdlc-init").mkdir(parents=True)
    (base / "sdlc-init" / "mine.txt").write_text("keep")
    proc = run(adapter, home=tmp_path)
    assert proc.returncode == 1 and "conflict" in proc.stdout
    assert (base / "sdlc-init" / "mine.txt").read_text() == "keep"
    assert (base / "sdlc-explore").is_symlink()


@pytest.mark.parametrize("adapter,parts", ADAPTERS.items())
def test_uninstall_removes_only_our_links(adapter, parts, tmp_path):
    run(adapter, home=tmp_path)
    base = tmp_path.joinpath(*parts)
    (base / "other").mkdir()
    (base / "sdlc-init").unlink()
    (base / "sdlc-init").mkdir()  # a real directory that must survive
    proc = run(adapter, "--uninstall", home=tmp_path)
    assert proc.returncode == 0
    assert (base / "sdlc-init").is_dir() and (base / "other").is_dir()
    assert not (base / "sdlc-explore").exists()


def test_unknown_skill_is_usage_error(tmp_path):
    assert run("codex", "--skill", "nope", home=tmp_path).returncode == 2
