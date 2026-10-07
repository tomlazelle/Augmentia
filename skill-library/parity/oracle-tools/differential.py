#!/usr/bin/env python3
"""Layer C — side-by-side differential run: the same generated inputs through the Python oracle and the Node port.

    differential.py --python "<python> -m sdlc" --node "node node/bin/sdlc.js" [--seed N] [--jobs N] [--report out.json]

Inputs (deterministic for a seed): every fixture project and a sample of corpus project trees, a read/write command
battery on each, per-document mutations of front matter and structure (dropped/emptied/corrupted keys, broken YAML,
BOM, CRLF, tabs, NUL, invalid UTF-8, truncation, duplicate IDs, broken links, ...), Unicode titles for allocate-id /
find-overlaps, and the stub-gh publish flow on every project that has Stories. Each input runs on two fresh copies; exit
code, stdout, stderr (``--json`` as parsed values), the complete post-state tree and the stub call log must agree, under
the approved exceptions only (002 argparse prose, 003 version, 004 YAML parser prose, 005 ASCII IDs; 001/006 are
provider-spawn/response cases covered by their own tests).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
LIB = TOOLS.parents[1]
sys.path.insert(0, str(TOOLS))
from replay import Corpus, DEFAULT_CORPUS  # noqa: E402

ROOT = "<ROOT>"
UNICODE_TITLES = ["Plain title", "Café déjà vu", "日本語のタイトル", "Ünïcödé — dash “quotes”", "emoji 🚀 launch", "العربية عنوان", "é combining", "full－width ＡＢＣ",
                  "nbsp here", "zero​width", "tab\there", "a" * 120, "  padded  ", "UPPER lower MiXeD", "dots...and/slashes\\", "quote's \"double\"", "#hash *star* `tick`",
                  "Straße ǅ ß İ", "𝔘𝔫𝔦𝔠𝔬𝔡𝔢 astral", "Ωmega ⅷ ① ٣", "line sep", "title: with colon", "- dash start", "[bracket] {brace}", "!bang & amp", "ÆØÅ ñ ü"]
YAML_VALUES = ["", "null", "~", "[unclosed", "'", "\"", "2026-13-45", "2026-02-30", "!!python/object:os.system x", "&a x", "*unknown", "{a: 1}", "[1, 2]", "yes", "0x1F", "1e3",
               "text # comment", "ünï", "a: b", "- x", "|", ">", "\t", "x" * 300, "2026-09-29T10:00:00", "9999-99-99", "True", "'quoted'"]


def structure_mutations(text: str, rng: random.Random) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    lines = text.split("\n")
    fm_end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None) if lines and lines[0] == "---" else None
    keys = [(i, l.split(":", 1)[0]) for i, l in enumerate(lines[1:fm_end], 1) if re.match(r"^[A-Za-z_]+:", l)] if fm_end else []
    for i, k in keys:
        out.append((f"drop-{k}", "\n".join(lines[:i] + lines[i + 1:]).encode()))
        v = rng.choice(YAML_VALUES)
        out.append((f"set-{k}={v[:12]!r}", "\n".join(lines[:i] + [f"{k}: {v}"] + lines[i + 1:]).encode()))
        out.append((f"dup-{k}", "\n".join(lines[:i + 1] + [lines[i]] + lines[i + 1:]).encode()))
    out.append(("no-closing-fence", "\n".join(lines[:fm_end] + lines[fm_end + 1:]).encode() if fm_end else text.encode()))
    out.append(("no-front-matter", "\n".join(lines[fm_end + 1:]).encode() if fm_end else text.encode()))
    out.append(("bom", b"\xef\xbb\xbf" + text.encode()))
    out.append(("crlf", text.replace("\n", "\r\n").encode()))
    out.append(("cr-only", text.replace("\n", "\r").encode()))
    out.append(("tab-in-front-matter", text.replace("\ntitle:", "\n\ttitle:", 1).encode()))
    out.append(("nul", text.replace("\n\n", "\n\x00\n", 1).encode()))
    out.append(("invalid-utf8", text.encode()[: len(text) // 2] + b"\xff\xfe" + text.encode()[len(text) // 2:]))
    out.append(("truncate-half", text.encode()[: len(text) // 2]))
    out.append(("empty", b""))
    out.append(("headings-demoted", text.replace("\n## ", "\n# ").encode()))
    out.append(("headings-subsection", text.replace("\n## ", "\n### ").encode()))
    out.append(("links-broken", text.replace("](../", "](../nope/").encode()))
    out.append(("ac-removed", re.sub(r"\n\d+\. .*", "", text).encode()))
    out.append(("trailing-ws", re.sub(r"\n", "  \n", text).encode()))
    out.append(("unicode-title", text.replace("title: ", "title: Ünï 🚀 ", 1).encode()))
    return out


def make_stub(work: Path, flavor: str) -> Path:
    script = work / "stubbin" / "gh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(f"#!{sys.executable}\nimport sys\nsys.path.insert(0, {str(TOOLS)!r})\nimport stub_gh\nsys.exit(stub_gh.main(sys.argv[1:]))\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


def snapshot(base: Path) -> dict:
    out = {}
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base).as_posix()
        out[rel] = ["l", os.readlink(p)] if p.is_symlink() else ["d"] if p.is_dir() else ["f", hashlib.sha256(p.read_bytes()).hexdigest()]
    return out


YAML_PROSE = re.compile(r"(invalid YAML(?: value)?:)[^\n\"]*")


def norm_str(s: str, base: Path, argparse_ok: bool) -> str:
    s = s.replace(str(base), ROOT)
    return YAML_PROSE.sub(lambda m: m.group(1) if m.group(1) == "invalid YAML:" else m.group(0), s)


def norm_json(v, base):
    if isinstance(v, str):
        return norm_str(v, base, False)
    if isinstance(v, list):
        return [norm_json(x, base) for x in v]
    if isinstance(v, dict):
        return {k: norm_json(x, base) for k, x in v.items()}
    return v


def run_impl(command, tree: Path, argv: list[str], env_extra: dict, setup_stub: bool, rel_cwd: str = ".") -> dict:
    with tempfile.TemporaryDirectory(prefix="sdlc-diff-") as tmp:
        work = Path(tmp).resolve()
        base = work / "p"
        shutil.copytree(tree, base, symlinks=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("SDLC_", "FAKE_GH", "GH_", "GITHUB_", "PYTHON"))}
        env.update({"COLUMNS": "80", "SDLC_TODAY": "2026-09-29", **env_extra})
        ghdir = work / "gh"
        if setup_stub:
            ghdir.mkdir()
            env["SDLC_GH_COMMAND"] = str(make_stub(work, "py")); env["FAKE_GH_STATE"] = str(ghdir); env["GH_TOKEN"] = "diff-token-placeholder"
        args = [a.replace(ROOT, str(base)) for a in argv]
        done = subprocess.run(command + args, cwd=base / rel_cwd, env=env, capture_output=True, text=True, errors="surrogateescape")
        res = {"exit": done.returncode, "out": done.stdout, "err": done.stderr, "tree": snapshot(base), "base": base}
        res["gh"] = {p.name: p.read_text(errors="replace") for p in sorted(ghdir.iterdir())} if setup_stub else None
        return res


def compare(argv, a: dict, b: dict) -> list[str]:
    problems = []
    if "UnicodeDecodeError" in a["err"]:
        # PARITY-EXCEPTION-007: Python leaks a traceback on a non-UTF-8 project file; Node must report `invalid-encoding`
        # (no traceback, no stack, never rewriting the file). Everything else is not comparable for this input.
        text = b["out"] + b["err"]
        if argv[0] == "validate" and "invalid-encoding" not in text:
            problems.append("EX-007: validate did not report invalid-encoding")
        if b["exit"] not in (0, 1):
            problems.append(f"EX-007: unexpected exit {b['exit']}")
        if "Traceback" in b["err"] or "    at " in b["err"]:
            problems.append("EX-007: Node leaked a stack trace")
        return problems + [f"EX-007 tree: {k}" for k in sorted(set(a["tree"]) | set(b["tree"])) if k.endswith(".md") and "map" not in k and a["tree"].get(k) != b["tree"].get(k)]
    if a["exit"] != b["exit"]:
        problems.append(f"exit {a['exit']} != {b['exit']}")
    asked_help = "--help" in argv or "-h" in argv or "--version" in argv
    if not asked_help:
        for field in ("out", "err"):
            x, y = norm_str(a[field], a["base"], False), norm_str(b[field], b["base"], False)
            if field == "out" and "--json" in argv and x.strip() and y.strip():
                try:
                    if norm_json(json.loads(a[field]), a["base"]) != norm_json(json.loads(b[field]), b["base"]):
                        problems.append("JSON stdout differs")
                except ValueError:
                    problems.append("stdout not JSON on one side")
            elif x != y and not (a["exit"] == 2 and b["exit"] == 2 and field == "err" and "usage:" in x and "usage:" in y):
                problems.append(f"{field} differs")
    ta, tb = a["tree"], b["tree"]
    if ta != tb:
        problems.append("post tree differs: " + ", ".join(sorted(k for k in set(ta) | set(tb) if ta.get(k) != tb.get(k))[:5]))
    if a["gh"] != b["gh"]:
        problems.append("gh call log differs")
    return problems


def project_dirs(corpus_sample: int, rng: random.Random, work: Path) -> list[tuple[str, Path]]:
    projects = []
    for d in sorted((LIB / "tests" / "fixtures").glob("m*/*/")):
        if (d / ".sdlc").is_dir():
            projects.append((d.relative_to(LIB / "tests").as_posix(), d))
    corpus = Corpus(DEFAULT_CORPUS)
    seen: set[str] = set()
    ids = []
    for c in corpus.cases:
        if c["pre"] not in seen and not c["ephemeral"] and any(k.startswith(("Stories/", "BR/", "PR/")) for k in corpus.trees[c["pre"]]):
            seen.add(c["pre"]); ids.append(c["pre"])
    for tid in rng.sample(ids, min(corpus_sample, len(ids))):
        dest = work / f"corpus-{tid[:10]}"
        corpus.materialize(tid, dest)
        projects.append((f"corpus:{tid[:10]}", dest))
    return projects


def docs_of(tree: Path) -> list[Path]:
    return [p for sub in ("BR", "PR", "Stories", "Artifacts") for p in sorted((tree / sub).rglob("*.md")) if p.name != "map.md"] if tree.is_dir() else []


def doc_ids(tree: Path) -> list[str]:
    return sorted({m.group(0) for p in docs_of(tree) for m in [re.match(r"[A-Z]+-\d{3,}", p.name)] if m})


def build_cases(projects, rng: random.Random, tmp: Path) -> list[tuple[str, Path, list[str], bool]]:
    cases = []
    for name, tree in projects:
        ids = doc_ids(tree)
        stories = [i for i in ids if i.startswith("US-")]
        battery = [["validate"], ["validate", "--json"], ["status"], ["status", "--json"], ["list"], ["list", "--json"], ["list", "--category", "US", "--json"], ["update-map"],
                   ["update-map", "--json"], ["find-overlaps", "--category", "US", "--title", "Export report summary", "--json"], ["find-overlaps", "--category", "BR", "--title", "overview"]]
        battery += [["references", i, "--json"] for i in ids[:25]] + [["references", i] for i in ids[:5]]
        battery += [["publish-preview", "--json"], ["publish-preview", *stories[:2]], ["publish-preview", *stories, "--json"], ["publish-apply", *stories[:1], "--json"], ["publish-apply"]]
        for argv in battery:
            cases.append((f"{name}: {' '.join(argv)}", tree, argv, "publish" in argv[0]))
        # generated mutations of individual documents
        docs = docs_of(tree)
        for doc in rng.sample(docs, min(len(docs), 4)):
            text = doc.read_text(encoding="utf-8", errors="replace")
            muts = structure_mutations(text, rng)
            for label, data in rng.sample(muts, min(len(muts), 12)):
                mtree = tmp / f"m{len(cases)}"
                shutil.copytree(tree, mtree, symlinks=True)
                (mtree / doc.relative_to(tree)).write_bytes(data)
                mid = re.match(r"[A-Z]+-\d{3,}", doc.name)
                for argv in (["validate", "--json"], ["validate"], ["status", "--json"], ["list", "--json"], ["update-map", "--json"], ["publish-preview", "--json"],
                             *([["references", mid.group(0), "--json"]] if mid else [])):
                    cases.append((f"{name}: {doc.name} <{label}>: {' '.join(argv)}", mtree, argv, "publish" in argv[0]))
    # Unicode titles on a fresh project and on a populated one
    empty = tmp / "empty-init"
    for title in UNICODE_TITLES:
        for cat in ("BR", "US"):
            for argv in (["allocate-id", "--category", cat, "--title", title, "--json"], ["allocate-id", "--category", cat, "--title", title], ["find-overlaps", "--category", cat, "--title", title, "--json"]):
                cases.append((f"unicode: {' '.join(argv)}", empty, argv, False))
    return cases


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python", required=True)
    ap.add_argument("--node", required=True)
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--corpus-sample", type=int, default=60)
    ap.add_argument("--report")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", action="append", default=[], help="run only inputs whose label contains this text")
    ap.add_argument("--exclude", action="append", default=[], help="skip inputs whose label contains this text (for a class already escalated for a decision)")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    py, nd = shlex.split(a.python), shlex.split(a.node)
    with tempfile.TemporaryDirectory(prefix="sdlc-diff-work-") as t:
        tmp = Path(t).resolve()
        projects = project_dirs(a.corpus_sample, rng, tmp)
        (tmp / "empty-init").mkdir()
        subprocess.run(py + ["init", "--project-name", "U"], cwd=tmp / "empty-init", capture_output=True, env={**os.environ, "SDLC_TODAY": "2026-09-29", "PYTHONPATH": str(LIB)}, check=True)
        cases = build_cases(projects, rng, tmp)
        cases = [c for c in cases if not any(x in c[0] for x in a.exclude) and (not a.only or any(x in c[0] for x in a.only))]
        if a.limit:
            cases = rng.sample(cases, min(a.limit, len(cases)))

        def one(case):
            label, tree, argv, stub = case
            ra = run_impl(py, tree, argv, {"PYTHONPATH": str(LIB)}, stub)
            rb = run_impl(nd, tree, argv, {}, stub)
            return label, argv, compare(argv, ra, rb)

        with ThreadPoolExecutor(a.jobs) as ex:
            results = list(ex.map(one, cases))
    failed = [r for r in results if r[2]]
    print(f"differential: {len(results)} inputs, {len(results) - len(failed)} identical, {len(failed)} different")
    for label, _, problems in failed[:40]:
        print("DIFF", label, "->", "; ".join(problems))
    if a.report:
        Path(a.report).write_text(json.dumps({"seed": a.seed, "inputs": len(results), "different": len(failed), "differences": [{"input": l, "problems": p} for l, _, p in failed]}, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
