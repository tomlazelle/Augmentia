#!/usr/bin/env python3
"""Sensitivity check: apply small deliberate behavior changes to a COPY of the Python implementation and confirm the
corpus replay detects each one. A corpus that cannot fail is not a specification."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LIB = Path(__file__).resolve().parents[2]
REPLAY = Path(__file__).resolve().parent / "replay.py"

MUTATIONS = [
    ("ids.py: ID zero-padding width", "sdlc/model.py", 'f"{category}-{number:03d}"', 'f"{category}-{number:04d}"'),
    ("validate.py: severity of stale-map", "sdlc/maps.py", '"stale-map"', '"stale-maps"'),
    ("cli.py: human init wording", "sdlc/cli.py", "Initialized SDLC project at", "Initialised SDLC project at"),
    ("cli.py: JSON envelope field", "sdlc/cli.py", '"schema_version": JSON_SCHEMA_VERSION', '"schema_version": JSON_SCHEMA_VERSION + 1'),
    ("query.py: overlap title weight", "sdlc/query.py", 'WEIGHTS = {"title": 0.5', 'WEIGHTS = {"title": 0.6'),
    ("publish.py: digest canonical form", "sdlc/publish.py", 'separators=(",", ":")', 'separators=(", ", ": ")'),
    ("publish.py: Issue title format", "sdlc/publish.py", 'f"[{doc.id}] {doc.title}"', 'f"{doc.id}: {doc.title}"'),
    ("publication.py: record layout", "sdlc/publication.py", '"- **Provider:** {provider}"', '"- **Provider** {provider}"'),
    ("ledger.py: retire keeps note", "sdlc/ledger.py", "entry.note = existing.note", "entry.note = ''"),
    ("status.py: attention ordering", "sdlc/status.py", '"in-progress": 4, "ready-to-implement": 5', '"in-progress": 5, "ready-to-implement": 4'),
    ("maps.py: relationship dedupe", "sdlc/maps.py", "if tuple(item[3]) not in seen:", "if True:"),
    ("validate.py: exit code on errors", "sdlc/validate.py", 'Outcome(1 if counts["error"] else 0', 'Outcome(2 if counts["error"] else 0'),
    ("technical.py: TBD heading level", "sdlc/technical.py", "s.level in (2, 3) and s.title.lower() == UNRESOLVED_HEADING", "s.level == 3 and s.title.lower() == UNRESOLVED_HEADING"),
    ("init_cmd.py: instruction files overwritten (both guards removed)", "sdlc/init_cmd.py",
     ("if os.path.lexists(target):\n        return False", 'open(target, "x", encoding="utf-8")'),
     ("if False:\n        return False", 'open(target, "w", encoding="utf-8")')),
    ("github_provider.py: redaction", "sdlc/github_provider.py", 'return _SECRET_RE.sub("[redacted]", text)', "return text"),
    ("frontmatter.py: date normalisation", "sdlc/frontmatter.py", "return value.isoformat()", "return str(value) + 'T'"),
]


def main() -> int:
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, rel, old, new in MUTATIONS:
            copy = Path(tmp) / "m"
            shutil.rmtree(copy, ignore_errors=True)
            shutil.copytree(LIB / "sdlc", copy / "sdlc")
            target = copy / rel
            text = target.read_text()
            pairs = list(zip(old, new)) if isinstance(old, tuple) else [(old, new)]
            if any(o not in text for o, _ in pairs):
                results.append({"mutation": name, "status": "NOT-APPLIED"})
                continue
            for o, n in pairs:
                text = text.replace(o, n, 1)
            target.write_text(text)
            env = {**os.environ, "PYTHONPATH": str(copy)}
            done = subprocess.run([sys.executable, str(REPLAY), "--command", f"{sys.executable} -m sdlc"], env=env, capture_output=True, text=True)
            line = next((ln for ln in done.stdout.splitlines() if ln.startswith("replayed")), done.stdout[-200:])
            differed = int(line.split(",")[1].split()[0]) if "differed" in line else -1
            results.append({"mutation": name, "caught": differed > 0, "cases_differing": differed})
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
