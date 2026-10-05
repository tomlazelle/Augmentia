"""`init` and `create-dir`: idempotent creation of the standard project structure."""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

from . import frontmatter
from .ledger import HEADER, LEDGER_REL, atomic_write
from .maps import specs, sync_map
from .model import ARTIFACT_SUBDIRS, Diagnostic, Outcome
from .project import DEFAULT_DIRECTORIES, SCHEMA_VERSION, Project, load_config, scan_documents

CONFIG_REL = ".sdlc/config.md"
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md")  # centrally maintained in sdlc/templates/


def _install_instruction_file(root: Path, name: str) -> bool:
    """Create <root>/<name> from the packaged template unless anything (file, symlink, even a dangling one)
    already exists there. Existing instructions are never read, appended to or overwritten."""
    target = root / name
    if os.path.lexists(target):
        return False
    text = resources.files("sdlc").joinpath("templates", name).read_text(encoding="utf-8")
    try:
        with open(target, "x", encoding="utf-8") as handle:  # 'x': never clobber, even on a race
            handle.write(text)
    except FileExistsError:
        return False
    return True


def _config_text(name: str) -> str:
    data = {"project_name": name, "schema_version": SCHEMA_VERSION, "directories": dict(DEFAULT_DIRECTORIES)}
    return (f"---\n{frontmatter.dump(data)}---\n\n# SDLC Configuration\n\n"
            "Internal configuration maintained by the `sdlc` CLI.\n"
            "It is not an authored document and is not listed in any map.\n")


def init_project(root: Path, project_name: str | None) -> Outcome:
    root = root.resolve()
    if not root.is_dir():
        return Outcome(2, diagnostics=[Diagnostic("error", "bad-root", f"{root} is not a directory")])
    created: list[str] = []
    existing: list[str] = []
    diags: list[Diagnostic] = []

    def note(path: Path, was_created: bool) -> None:
        rel = path.relative_to(root).as_posix()
        (created if was_created else existing).append(rel)

    (root / ".sdlc").mkdir(exist_ok=True)
    config_path = root / CONFIG_REL
    if config_path.exists():
        note(config_path, False)
        _, cfg_diags = load_config(root)
        diags += [d for d in cfg_diags if d.severity == "error"]
    else:
        atomic_write(config_path, _config_text(project_name or root.name))
        note(config_path, True)
    ledger_path = root / LEDGER_REL
    if ledger_path.exists():
        note(ledger_path, False)
    else:
        atomic_write(ledger_path, HEADER)
        note(ledger_path, True)

    for name in INSTRUCTION_FILES:
        note(root / name, _install_instruction_file(root, name))

    project = Project.open(root)
    for key in DEFAULT_DIRECTORIES:
        directory = project.top(key)
        was_new = not directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        if was_new:
            created.append(project.rel(directory) + "/")
    docs, _ = scan_documents(project)
    for spec in specs(project):
        action, diag = sync_map(project, spec, docs) if not spec.path.exists() else ("exists", None)
        note(spec.path, action == "created")
    return Outcome(0 if not diags else 1, {
        "root": root.as_posix(), "created": sorted(created), "existing": sorted(existing)}, diags)


def create_artifact_dir(project: Project, sub: str) -> Outcome:
    if sub not in ARTIFACT_SUBDIRS:
        return Outcome(2, diagnostics=[Diagnostic("error", "bad-artifact", f"unknown artifact directory {sub!r}")])
    artifacts = project.top("Artifacts")
    if not artifacts.is_dir():
        return Outcome(1, diagnostics=[Diagnostic(
            "error", "missing-directory", "Artifacts directory does not exist; run 'sdlc init'", path=project.rel(artifacts))])
    target = artifacts / sub
    dir_created = not target.exists()
    target.mkdir(exist_ok=True)
    docs, _ = scan_documents(project)
    diags: list[Diagnostic] = []
    result = {"directory": project.rel(target), "directory_created": dir_created}
    for spec in specs(project):
        if spec.key in (sub, "Artifacts"):
            action, diag = sync_map(project, spec, docs)
            result[f"{spec.key}_map"] = action
            if diag:
                diags.append(diag)
    return Outcome(0 if not diags else 1, result, diags)
