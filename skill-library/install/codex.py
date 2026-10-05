#!/usr/bin/env python3
"""Codex adapter: links Skills into ~/.agents/skills (user) or <project>/.agents/skills (project)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # source checkout: make `sdlc` importable
from sdlc.adapters import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run("codex", Path.home() / ".agents" / "skills", ".agents/skills"))
