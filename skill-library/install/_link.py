"""Shared symlink installer used by the thin per-agent adapters.

Skills are never copied: each `skills/<name>` directory is symlinked into the agent's
skill-discovery directory, so the central library remains the only source of Skill text.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LIBRARY = Path(__file__).resolve().parents[1]
SKILLS = LIBRARY / "skills"


def available_skills() -> list[str]:
    return sorted(p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file())


def _points_into_library(link: Path) -> bool:
    try:
        return link.is_symlink() and Path(link.resolve()).is_relative_to(SKILLS.resolve())
    except OSError:
        return False


def install(target: Path, names: list[str], force: bool = False) -> list[tuple[str, str]]:
    target.mkdir(parents=True, exist_ok=True)
    results = []
    for name in names:
        source, link = SKILLS / name, target / name
        if link.is_symlink() and link.resolve() == source.resolve():
            results.append((name, "unchanged"))
        elif link.is_symlink() and force:
            link.unlink()
            link.symlink_to(source, target_is_directory=True)
            results.append((name, "replaced"))
        elif link.exists() or link.is_symlink():
            results.append((name, "conflict"))  # never remove real directories or foreign links
        else:
            link.symlink_to(source, target_is_directory=True)
            results.append((name, "installed"))
    return results


def uninstall(target: Path, names: list[str]) -> list[tuple[str, str]]:
    results = []
    for name in names:
        link = target / name
        if _points_into_library(link):
            link.unlink()
            results.append((name, "removed"))
        else:
            results.append((name, "skipped" if link.exists() or link.is_symlink() else "absent"))
    return results


def run(agent: str, user_dir: Path, project_rel: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog=f"install/{agent}.py",
        description=f"Link the central SDLC Skills into {agent}'s skill discovery directory (symlinks, no copies).")
    parser.add_argument("--scope", choices=["user", "project"], default="user",
                        help=f"user: {user_dir}; project: <project-dir>/{project_rel} (default: user)")
    parser.add_argument("--project-dir", default=".", help="project directory for --scope project (default: current directory)")
    parser.add_argument("--target", help="override the destination directory entirely")
    parser.add_argument("--skill", action="append", metavar="NAME", help="install only this Skill (repeatable)")
    parser.add_argument("--force", action="store_true", help="replace an existing symlink that points elsewhere")
    parser.add_argument("--uninstall", action="store_true", help="remove the links this adapter created")
    args = parser.parse_args(argv)

    names = args.skill or available_skills()
    unknown = sorted(set(names) - set(available_skills()))
    if unknown:
        print(f"error: unknown Skill(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    if args.target:
        target = Path(args.target)
    elif args.scope == "project":
        target = Path(args.project_dir).resolve() / project_rel
    else:
        target = user_dir
    results = uninstall(target, names) if args.uninstall else install(target, names, args.force)
    for name, state in results:
        print(f"{state:<10} {target / name}")
    return 1 if any(state == "conflict" for _, state in results) else 0
