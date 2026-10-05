"""Locate the packaged Skill library (skills/ and shared/) in an installed distribution or a source checkout."""

from __future__ import annotations

from pathlib import Path

_PACKAGE = Path(__file__).resolve().parent


def library_root() -> Path:
    """Directory that contains `skills/` and `shared/`.

    An installed distribution carries them at `sdlc/library/` (copied at build time from the canonical
    `skills/` and `shared/` sources, never forked). In a source checkout they sit beside the `sdlc/` package.
    """
    packaged = _PACKAGE / "library"
    if (packaged / "skills").is_dir() and (packaged / "shared").is_dir():
        return packaged
    return _PACKAGE.parent


def skills_dir() -> Path:
    return library_root() / "skills"
