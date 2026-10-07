#!/usr/bin/env python3
"""Condition-level coverage that line/branch coverage cannot see: both outcomes of every conditional expression
(`a if c else b`), and every comprehension filter (`[x for x in xs if c]`). Instruments a COPY of the Python implementation and replays the corpus over it.

    condition_trace.py [--json OUT]
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

LIB = Path(__file__).resolve().parents[2]
REPLAY = Path(__file__).resolve().parent / "replay.py"
SKIP = {"adapters.py", "resources.py", "__main__.py"}

HELPER = '''import atexit, json, os
_seen = {}
def cond(key, value):
    _seen.setdefault(key, [False, False])[0 if value else 1] = True
    return value
def _dump():
    path = os.environ.get("SDLC_TRACE_OUT")
    if path:
        existing = json.load(open(path)) if os.path.exists(path) else {}
        for k, v in _seen.items():
            cur = existing.setdefault(k, [False, False])
            existing[k] = [cur[0] or v[0], cur[1] or v[1]]
        json.dump(existing, open(path, "w"))
atexit.register(_dump)
'''


class Instrument(ast.NodeTransformer):
    def __init__(self, rel: str, src_lines: list[str], sites: dict):
        self.rel, self.lines, self.sites = rel, src_lines, sites

    def _wrap(self, node: ast.expr, kind: str) -> ast.expr:
        key = f"{self.rel}:{node.lineno}:{node.col_offset}:{kind}"
        self.sites[key] = {"file": self.rel, "line": node.lineno, "kind": kind, "text": self.lines[node.lineno - 1].strip()[:110]}
        call = ast.Call(func=ast.Attribute(value=ast.Name(id="_sdlc_trace", ctx=ast.Load()), attr="cond", ctx=ast.Load()),
                        args=[ast.Constant(key), node], keywords=[])
        return ast.copy_location(call, node)

    def visit_IfExp(self, node):
        self.generic_visit(node)
        node.test = self._wrap(node.test, "ifexp")
        return node

    def visit_comprehension(self, node):
        self.generic_visit(node)
        node.ifs = [self._wrap(c, "comprehension-filter") for c in node.ifs]
        return node


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    sites: dict[str, dict] = {}
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "sdlc"
        shutil.copytree(LIB / "sdlc", copy, ignore=shutil.ignore_patterns("__pycache__"))
        (copy / "_sdlc_trace.py").write_text(HELPER)
        for path in copy.glob("*.py"):
            if path.name in SKIP | {"_sdlc_trace.py", "__init__.py"}:
                continue
            text = path.read_text()
            tree = ast.parse(text)
            Instrument(f"sdlc/{path.name}", text.split("\n"), sites).visit(tree)
            ast.fix_missing_locations(tree)
            body = ast.unparse(tree)
            path.write_text("from . import _sdlc_trace\n" + body.replace("from __future__ import annotations\n", "", 1) if "from __future__" in body else "from . import _sdlc_trace\n" + body)
        out = Path(tmp) / "trace.json"
        env = {**os.environ, "SDLC_TRACE_OUT": str(out), "PYTHONPATH": tmp}
        done = subprocess.run([sys.executable, str(REPLAY), "--inprocess", "--sdlc-path", tmp], env=env, capture_output=True, text=True)
        line = next((ln for ln in done.stdout.splitlines() if ln.startswith("replayed")), done.stdout[-300:] + done.stderr[-300:])
        seen = json.loads(out.read_text()) if out.exists() else {}
    rows = []
    for key, info in sorted(sites.items(), key=lambda kv: (kv[1]["file"], kv[1]["line"])):
        t, f = seen.get(key, [False, False])
        if not (t and f):
            rows.append({**info, "true_seen": t, "false_seen": f})
    result = {"replay": line, "sites": len(sites), "incomplete": rows}
    print(f"{line}\nconditional sites instrumented: {len(sites)}; sites missing an outcome: {len(rows)}")
    for r in rows:
        print(f"  {r['file']}:{r['line']} [{r['kind']}] true={r['true_seen']} false={r['false_seen']}  {r['text']}")
    if args.json:
        args.json.write_text(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
