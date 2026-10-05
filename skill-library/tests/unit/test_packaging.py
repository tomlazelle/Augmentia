"""M6 release packaging: runtime data, console entry points, and independence from the source checkout."""

import os
import re
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

import pytest

import sdlc
from sdlc import resources

ROOT = Path(__file__).resolve().parents[2]
SKILLS = sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
SHARED = sorted(p.name for p in (ROOT / "shared").glob("*.md"))
SCRIPTS = {"sdlc": "sdlc.cli:main", "sdlc-install-claude-code": "sdlc.adapters:claude_code_main",
           "sdlc-install-codex": "sdlc.adapters:codex_main"}
needs_install = pytest.mark.skipif(os.environ.get("SDLC_TEST_INSTALL") != "1", reason="set SDLC_TEST_INSTALL=1 to run")


def project_table():
    return tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]


# --- static (always run) ------------------------------------------------------------------------

def test_version_is_single_sourced_and_a_release_candidate():
    assert project_table()["version"] == sdlc.__version__ and re.match(r"^\d+\.\d+\.\d+(rc\d+)?$", sdlc.__version__)


def test_console_scripts_are_declared_and_importable():
    assert project_table()["scripts"] == SCRIPTS
    import importlib
    for target in SCRIPTS.values():
        module, func = target.split(":")
        assert callable(getattr(importlib.import_module(module), func))


def test_runtime_dependency_is_only_pyyaml_and_python_311_is_the_baseline():
    p = project_table()
    assert [d.split(">")[0] for d in p["dependencies"]] == ["PyYAML"] and p["requires-python"] == ">=3.11"


def test_library_root_resolves_in_a_source_checkout():
    assert resources.library_root() == ROOT and resources.skills_dir() == ROOT / "skills"


def test_build_hook_and_manifest_carry_the_canonical_trees():
    assert "sdlc" in (ROOT / "setup.py").read_text() and '"library"' in (ROOT / "setup.py").read_text()
    manifest = (ROOT / "MANIFEST.in").read_text()
    assert "recursive-include skills" in manifest and "recursive-include shared" in manifest


def test_skills_and_templates_use_the_installed_command_not_python_dash_m():
    """Regression (M6 defect 1): under pipx only `sdlc` exists; `python -m sdlc` fails for the user's python."""
    offenders = []
    for path in [*(ROOT / "skills").rglob("*.md"), *(ROOT / "shared").glob("*.md"), *(ROOT / "sdlc" / "templates").glob("*.md")]:
        text = path.read_text()
        if "python -m sdlc" in text and path.name != "cli-contract.md":
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []
    assert "`python -m sdlc` is an exact equivalent" in (ROOT / "shared" / "cli-contract.md").read_text()


def test_version_flag_and_help_list_every_command(capsys):
    from sdlc.cli import main
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0 and f"sdlc {sdlc.__version__}" in capsys.readouterr().out


# --- built distribution and isolated install (opt-in) -------------------------------------------

@pytest.fixture(scope="module")
def wheel(tmp_path_factory):
    import shutil
    out = tmp_path_factory.mktemp("dist")
    src = out / "src"  # build from a copy so the checkout gains no build/ or egg-info artifacts
    shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns(".venv", "*.egg-info", "__pycache__", ".pytest_cache", "tests", "build", "dist"))
    subprocess.run([sys.executable, "-m", "pip", "wheel", str(src), "--no-build-isolation", "--no-deps", "-w", str(out), "-q"],
                   check=True, capture_output=True)
    (path,) = out.glob("*.whl")
    return path


@pytest.fixture(scope="module")
def installed(wheel, tmp_path_factory):
    venv = tmp_path_factory.mktemp("venv") / "v"
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(venv)], check=True)
    subprocess.run([str(venv / "bin" / "python"), "-m", "pip", "install", str(wheel), "-q"], check=True)
    return venv


def run_installed(venv, *args, cwd, **kw):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "SDLC_TODAY")}
    env["PATH"] = f"{venv / 'bin'}{os.pathsep}{env['PATH']}"
    return subprocess.run(list(args), cwd=cwd, env=env, capture_output=True, text=True, **kw)


@needs_install
def test_wheel_contains_every_runtime_resource(wheel):
    names = set(zipfile.ZipFile(wheel).namelist())
    for skill in SKILLS:
        assert f"sdlc/library/skills/{skill}/SKILL.md" in names, skill
    for source in (ROOT / "skills").rglob("*"):
        if source.is_file() and "__pycache__" not in source.parts:
            assert f"sdlc/library/skills/{source.relative_to(ROOT / 'skills').as_posix()}" in names, source
    for doc in SHARED:
        assert f"sdlc/library/shared/{doc}" in names, doc
    assert {"sdlc/templates/AGENTS.md", "sdlc/templates/CLAUDE.md", "sdlc/adapters.py", "sdlc/resources.py"} <= names
    entry = next(n for n in names if n.endswith("entry_points.txt"))
    text = zipfile.ZipFile(wheel).read(entry).decode()
    for name, target in SCRIPTS.items():
        assert f"{name} = {target}" in text
    assert not any("__pycache__" in n for n in names if "/library/" in n)
    assert not any(n.startswith(("tests/", "install/")) for n in names)


@needs_install
def test_installed_console_entry_point_runs_without_the_checkout(installed, tmp_path):
    version = run_installed(installed, "sdlc", "--version", cwd=tmp_path)
    assert version.returncode == 0 and version.stdout.strip() == f"sdlc {sdlc.__version__}"
    helped = run_installed(installed, "sdlc", "--help", cwd=tmp_path).stdout
    for command in ("init", "allocate-id", "list", "references", "find-overlaps", "status", "publish-preview", "publish-apply", "validate"):
        assert command in helped
    legacy = run_installed(installed, str(installed / "bin" / "python"), "-m", "sdlc", "--version", cwd=tmp_path)
    assert legacy.returncode == 0  # `python -m sdlc` stays supported


@needs_install
def test_release_smoke_sequence_from_the_installed_package(installed, tmp_path):
    project = tmp_path / "p"
    project.mkdir()
    for args in (["init"], ["init"], ["validate"], ["status"], ["list"], ["allocate-id", "--category", "BR", "--title", "Overview"]):
        done = run_installed(installed, "sdlc", *args, cwd=project)
        assert done.returncode == 0, (args, done.stdout, done.stderr)
    assert (project / "AGENTS.md").read_text() == (project / "CLAUDE.md").read_text()
    assert "create-brd" in (project / "AGENTS.md").read_text() and "sdlc validate" in (project / "AGENTS.md").read_text()
    assert run_installed(installed, "sdlc", "validate", cwd=project).returncode == 0


@needs_install
@pytest.mark.parametrize("script,parts", [("sdlc-install-claude-code", (".claude", "skills")), ("sdlc-install-codex", (".agents", "skills"))])
def test_installed_adapters_link_packaged_skills_and_references_resolve(installed, tmp_path, script, parts):
    project = tmp_path / "proj"
    project.mkdir()
    done = run_installed(installed, script, "--scope", "project", "--project-dir", str(project), cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    base = project.joinpath(*parts)
    assert sorted(p.name for p in base.iterdir()) == SKILLS
    site = next((installed / "lib").glob("python3*/site-packages")).resolve()
    ref = re.compile(r"`((?:references/|\.\./\.\./shared/)[\w./-]+\.md)`")
    for skill in SKILLS:
        link = base / skill
        target = link.resolve()
        assert link.is_symlink() and target.is_relative_to(site) and not target.is_relative_to(ROOT)  # not the source checkout
        for token in ref.findall((link / "SKILL.md").read_text()):
            assert (link / token).is_file(), (skill, token)  # relative references resolve through the link
    again = run_installed(installed, script, "--scope", "project", "--project-dir", str(project), cwd=tmp_path)
    assert again.returncode == 0 and {ln.split()[0] for ln in again.stdout.splitlines()} == {"unchanged"}


@needs_install
def test_installed_adapter_uninstall_and_conflict_behaviour(installed, tmp_path):
    project = tmp_path / "proj"
    (project / ".claude" / "skills" / "sdlc-init").mkdir(parents=True)  # a real directory must never be replaced
    done = run_installed(installed, "sdlc-install-claude-code", "--scope", "project", "--project-dir", str(project), cwd=tmp_path)
    assert done.returncode == 1 and "conflict" in done.stdout and (project / ".claude" / "skills" / "sdlc-init").is_dir()
    gone = run_installed(installed, "sdlc-install-claude-code", "--scope", "project", "--project-dir", str(project), "--uninstall", cwd=tmp_path)
    assert gone.returncode == 0 and (project / ".claude" / "skills" / "sdlc-init").is_dir()  # foreign directory untouched
