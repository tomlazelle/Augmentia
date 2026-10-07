#!/usr/bin/env python3
"""Replay the recorded behavioral corpus against an implementation of `sdlc` and report any difference.

    replay.py [--corpus DIR] [--command "python -m sdlc"] [--jobs N] [--only SUBSTRING] [--inprocess]

Parity rules (docs/SDLC-M7-NODE-MIGRATION-PLAN.md §6.5): exit code, human-readable stdout/stderr and the complete
post-state file tree (including the stub-gh call log) must match byte for byte; `--json` stdout is compared as
parsed JSON values. `--inprocess` (Python oracle only) calls sdlc.cli.main directly so coverage can be measured.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import gzip
import hashlib
import io
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
DEFAULT_CORPUS = TOOLS.parent / "corpus"
ROOT_TOKEN = "<ROOT>"
CLEAN_ENV_PREFIXES = ("SDLC_", "FAKE_GH", "GH_", "GITHUB_")


def read_jsonl(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


class Corpus:
    def __init__(self, directory: Path):
        self.cases = list(read_jsonl(directory / "cases.jsonl.gz"))
        self.trees = {t["id"]: t["entries"] for t in read_jsonl(directory / "trees.jsonl.gz")}
        self.blobs = {}
        for b in read_jsonl(directory / "blobs.jsonl.gz"):
            self.blobs[b["id"]] = b["data"].encode("utf-8") if b["enc"] == "utf8" else base64.b64decode(b["data"])

    def materialize(self, tree_id: str, base: Path) -> None:
        base.mkdir(parents=True, exist_ok=True)
        for rel, entry in sorted(self.trees[tree_id].items()):
            path = base / rel
            if entry[0] == "d":
                path.mkdir(parents=True, exist_ok=True)
            elif entry[0] == "l":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(entry[1])
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(self.blobs[entry[1]])

    def snapshot(self, base: Path) -> dict:
        entries = {}
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(base).as_posix()
            if p.is_symlink():
                entries[rel] = ["l", os.readlink(p)]
            elif p.is_dir():
                entries[rel] = ["d"]
            elif p.is_file():
                entries[rel] = ["f", hashlib.sha256(p.read_bytes()).hexdigest()]
        return entries


def gh_state(path: Path):
    return {p.name: p.read_text(errors="replace") for p in sorted(path.iterdir()) if p.is_file()}


def make_stub(workdir: Path) -> Path:
    script = workdir / "stubbin" / "gh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(f"#!{sys.executable}\nimport sys\nsys.path.insert(0, {str(TOOLS)!r})\nimport stub_gh\nsys.exit(stub_gh.main(sys.argv[1:]))\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def case_environment(case: dict, base: Path, stub: Path, ghdir: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith(CLEAN_ENV_PREFIXES)}
    env["COLUMNS"] = "80"
    for key, value in case["env"].items():
        if key == "SDLC_GH_COMMAND":
            value = str(stub) if value == "<STUB_GH>" else str(base / value.split(":", 1)[1].rstrip(">"))
        elif key == "FAKE_GH_STATE":
            value = str(ghdir)
        elif key in ("GH_TOKEN", "GITHUB_TOKEN"):
            value = "replay-token-placeholder"
        env[key] = value
    return env


def compare(case: dict, rc, out: str, err: str, base: Path, corpus: Corpus, ghdir: Path | None) -> list[str]:
    exp = case["expected"]
    problems = []
    norm = lambda s: s.replace(str(base), ROOT_TOKEN)  # noqa: E731
    out, err = norm(out), norm(err)
    if rc != exp["exit"]:
        problems.append(f"exit {rc!r} != {exp['exit']!r}")
    if "--json" in case["argv"] and exp["stdout"].strip():
        try:
            if json.loads(out) != json.loads(exp["stdout"]):
                problems.append("JSON stdout differs (parsed values)")
        except ValueError:
            problems.append("stdout is not valid JSON")
    elif out != exp["stdout"]:
        problems.append("stdout differs (bytes)")
    if err != exp["stderr"]:
        problems.append("stderr differs (bytes)")
    want = corpus.trees[exp["post"]]
    got = corpus.snapshot(base)
    expected_hashes = {k: (v if v[0] != "f" else ["f", hashlib.sha256(corpus.blobs[v[1]]).hexdigest()]) for k, v in want.items()}
    if got != expected_hashes:
        diff = sorted(set(got) ^ set(expected_hashes)) + sorted(k for k in set(got) & set(expected_hashes) if got[k] != expected_hashes[k])
        problems.append("post-state tree differs: " + ", ".join(diff[:6]))
    if ghdir is not None and exp["gh_post"] is not None and gh_state(ghdir) != exp["gh_post"]:
        problems.append("stub gh call log/state differs")
    return problems


def arguments(case: dict, base: Path) -> list[str]:
    return [a.replace(ROOT_TOKEN, str(base)) for a in case["argv"]]


def run_subprocess(case: dict, corpus: Corpus, command: list[str]) -> list[str]:
    with tempfile.TemporaryDirectory(prefix="sdlc-replay-") as tmp:
        work = Path(tmp).resolve()
        base = work / "project"
        corpus.materialize(case["pre"], base)
        ghdir = work / "ghstate"
        ghdir.mkdir()
        for name, text in (case["gh_pre"] or {}).items():
            (ghdir / name).write_text(text)
        stub = make_stub(work)
        env = case_environment(case, base, stub, ghdir)
        done = subprocess.run(command + arguments(case, base), cwd=base / case["cwd"], env=env, capture_output=True, text=True)
        return compare(case, done.returncode, done.stdout, done.stderr, base, corpus, ghdir if case["env"].get("FAKE_GH_STATE") else None)


def run_inprocess(case: dict, corpus: Corpus) -> list[str]:
    from sdlc.cli import main

    with tempfile.TemporaryDirectory(prefix="sdlc-replay-") as tmp:
        work = Path(tmp).resolve()
        base = work / "project"
        corpus.materialize(case["pre"], base)
        ghdir = work / "ghstate"
        ghdir.mkdir()
        for name, text in (case["gh_pre"] or {}).items():
            (ghdir / name).write_text(text)
        stub = make_stub(work)
        env = case_environment(case, base, stub, ghdir)
        saved_env, saved_cwd = dict(os.environ), os.getcwd()
        os.environ.clear()
        os.environ.update(env)
        os.chdir(base / case["cwd"])
        out, err = io.StringIO(), io.StringIO()
        rc = 0
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    rc = main(arguments(case, base))
                except SystemExit as exc:
                    rc = exc.code
        finally:
            os.chdir(saved_cwd)
            os.environ.clear()
            os.environ.update(saved_env)
        return compare(case, rc, out.getvalue(), err.getvalue(), base, corpus, ghdir if case["env"].get("FAKE_GH_STATE") else None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    ap.add_argument("--command", default=f"{sys.executable} -m sdlc")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", default="")
    ap.add_argument("--inprocess", action="store_true")
    ap.add_argument("--sdlc-path", type=Path, default=TOOLS.parents[1], help="directory containing the `sdlc` package for --inprocess")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    corpus = Corpus(args.corpus)
    cases = [c for c in corpus.cases if args.only in c["id"] and c.get("replayable", True)]
    skipped = [c for c in corpus.cases if not c.get("replayable", True)]
    command = shlex.split(args.command)
    if args.inprocess:
        sys.path.insert(0, str(args.sdlc_path))
        results = [(c, run_inprocess(c, corpus)) for c in cases]
    else:
        with ThreadPoolExecutor(args.jobs) as pool:
            results = list(zip(cases, pool.map(lambda c: run_subprocess(c, corpus, command), cases)))
    failed = [(c, p) for c, p in results if p]
    print(f"replayed {len(cases)} case(s): {len(cases) - len(failed)} matched, {len(failed)} differed; {len(skipped)} flagged non-replayable")
    for c in skipped:
        print(f"  SKIP {c['id']}: {c['not_replayable_reason']}")
    for case, problems in failed[:50]:
        print(f"  DIFF {case['id']}  argv={case['argv'][:4]}")
        for problem in problems:
            print(f"       - {problem}")
    if args.report:
        args.report.write_text(json.dumps([{"id": c["id"], "problems": p} for c, p in failed], indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
