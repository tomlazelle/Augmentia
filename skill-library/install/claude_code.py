#!/usr/bin/env python3
"""Claude Code adapter: links Skills into ~/.claude/skills (user) or <project>/.claude/skills (project)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _link import run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run("claude-code", Path.home() / ".claude" / "skills", ".claude/skills"))
