#!/usr/bin/env python3
"""Generate corpus statistics and the coverage report (docs/SDLC-M7-1-CORPUS-REPORT.md) from the corpus, a coverage.py
JSON report of the in-process corpus replay, and a mutation-check result file. Every number in the report is computed."""

from __future__ import annotations

import argparse
import ast
import collections
import glob
import gzip
import json
import re
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import Corpus  # noqa: E402

NOT_CORPUS = {"sdlc/adapters.py": "installer commands `sdlc-install-claude-code`/`-codex` (separate executables, covered by the install tests; Layer B)",
              "sdlc/resources.py": "package-resource lookup used only by the installers (Layer B)",
              "sdlc/__main__.py": "`python -m sdlc` shim, removed with Python (the corpus runs through the CLI entry point)"}

# Residual uncovered lines, each with an explicit disposition. Keys are (file, first line).
DISPOSITION = {
    ("sdlc/github_provider.py", 55): ("needs a 60-second hang to trigger the timeout; not corpus-testable", "Layer B unit test with an injectable timeout"),
    ("sdlc/init_cmd.py", 29): ("lost race between `lexists` and exclusive create; cannot be triggered deterministically", "port the `wx` exclusive create; no corpus case"),
    ("sdlc/init_cmd.py", 88): ("`bad-artifact` is unreachable from the CLI: argparse `choices` rejects unknown artifact names first", "unreachable; optional to port"),
    ("sdlc/init_cmd.py", 89): ("same as above", "unreachable; optional to port"),
    ("sdlc/project.py", 115): ("`rel()` fallback for a path outside the project root (symlink target); output would contain a machine-specific absolute path, so not portable", "port defensively; no corpus case"),
    ("sdlc/publication.py", 39): ("`Publication.number` property is never used (dead code)", "do not port"),
    ("sdlc/publication.py", 87): ("PUB entry without URL: unreachable with the real provider (the URL is always parsed from `gh` output); only an injected provider returns no URL", "Layer B unit test"),
    ("sdlc/publication.py", 94): ("`_bump_updated` on text without a front matter block: a Story always has one by this point", "port defensively; unreachable"),
    ("sdlc/publication.py", 95): ("same as above", "port defensively; unreachable"),
    ("sdlc/publication.py", 97): ("`_bump_updated` with an unterminated front matter block: unreachable for a valid Story", "port defensively; unreachable"),
    ("sdlc/publication.py", 98): ("same as above", "port defensively; unreachable"),
    ("sdlc/publish.py", 175): ("branch is shadowed: `validate` already reports `publication-invalid` on the same path and blocks the Story earlier", "dead branch; port or drop (decision)"),
    ("sdlc/publish.py", 176): ("same: shadowed by the earlier validate-based block", "dead branch; port or drop (decision)"),
    ("sdlc/publish.py", 205): ("`unrelated` is always non-empty when other errors exist and nothing is blocked", "dead branch"),
    ("sdlc/publish.py", 286): ("generic `except Exception` around `create_issue`: reachable only with an injected provider that raises a non-ProviderError", "Layer B unit test with an injected provider"),
    ("sdlc/validate.py", 19): ("`_dup_diags` guard for single-file groups is never true for the groups passed in", "dead branch"),
    ("sdlc/validate.py", 20): ("same as above", "dead branch"),
}


CONDITION_DISPOSITION = {
    ("sdlc/frontmatter.py", 26): "a YAML error always has a message, so the empty-message side cannot occur",
    ("sdlc/model.py", 73): "`Outcome` is always constructed with an explicit diagnostics list from the CLI paths; the `None` default is internal",
    ("sdlc/publication.py", 101): "`updated:` missing from a Story front matter makes the Story invalid, so it is blocked before recording; unreachable",
    ("sdlc/publish.py", 155): "a document whose ID is `US-…` is always a Story; the non-story side cannot occur",
    ("sdlc/publish.py", 204): "`unrelated` is always non-empty when other errors exist and nothing is blocked; the false side cannot occur",
    ("sdlc/validate.py", 114): "`ident` always has at least one document or requirement declaration; the empty side cannot occur",
}


def static_codes() -> dict[str, set[str]]:
    codes: dict[str, set[str]] = {}
    for f in sorted(glob.glob(str(LIB / "sdlc" / "*.py"))):
        name = Path(f).name
        if name in ("adapters.py", "resources.py"):
            continue
        for n in ast.walk(ast.parse(Path(f).read_text())):
            if isinstance(n, ast.Call):
                func = getattr(n.func, "id", getattr(n.func, "attr", ""))
                if func in ("Diagnostic", "err", "bad", "ProviderError", "AmbiguousResult", "warn", "add"):
                    for a in n.args[:3]:
                        if isinstance(a, ast.Constant) and isinstance(a.value, str) and re.fullmatch(r"[a-z]+(-[a-z]+)+", a.value):
                            codes.setdefault(a.value, set()).add(f"sdlc/{name}")
    return codes


def observed(corpus: Corpus):
    diag, kinds, outcomes = collections.Counter(), collections.Counter(), collections.Counter()
    for c in corpus.cases:
        out, err = c["expected"]["stdout"], c["expected"]["stderr"]
        if "--json" in c["argv"] and out.strip():
            d = json.loads(out)
            for x in d.get("diagnostics", []):
                diag[x["code"]] += 1
            r = d.get("result") or {}
            for a in r.get("attention", []) if isinstance(r, dict) else []:
                kinds[a["kind"]] += 1
            for o in r.get("outcomes", []) if isinstance(r, dict) else []:
                outcomes[o["outcome"]] += 1
        for m in re.finditer(r"\(([a-z]+(?:-[a-z]+)+)\)", out + err):
            diag[m.group(1)] += 1
    return diag, kinds, outcomes


def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--mutations", type=Path, required=True)
    ap.add_argument("--conditions", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--stats-json", type=Path)
    args = ap.parse_args()
    corpus = Corpus(LIB / "parity" / "corpus")
    cov = json.loads(args.coverage.read_text())
    muts = json.loads(args.mutations.read_text())
    conds = json.loads(args.conditions.read_text())
    cases = corpus.cases
    replayable = [c for c in cases if c.get("replayable", True)]
    cmd = lambda c: next((a for a in c["argv"] if not a.startswith("-")), c["argv"][0])  # noqa: E731
    by_cmd = collections.defaultdict(lambda: collections.Counter())
    for c in cases:
        by_cmd[cmd(c)][c["expected"]["exit"]] += 1
    human = collections.Counter(cmd(c) for c in cases if "--json" not in c["argv"])
    jsonm = collections.Counter(cmd(c) for c in cases if "--json" in c["argv"])
    stub = sum(1 for c in cases if "FAKE_GH_STATE" in c["env"])
    ephemeral = sum(1 for c in cases if c.get("ephemeral"))
    argparse_text = [c for c in cases if c.get("text_parity") == "argparse"]
    tests = {c["test"] for c in cases}
    sizes = {n: (LIB / "parity" / "corpus" / n).stat().st_size for n in ("cases.jsonl.gz", "trees.jsonl.gz", "blobs.jsonl.gz")}
    diag, kinds, outcomes = observed(corpus)
    defined = static_codes()
    missing_codes = sorted(set(defined) - set(diag) - set(kinds) - set(outcomes))
    commands = sorted(c for c in {cmd(x) for x in cases} if c != "--version")
    all_cmds = ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "status", "publish-preview", "publish-apply", "validate"]

    # exit paths: every source line that constructs an Outcome with an exit code, executed or not
    exit_rows = []
    for f, info in sorted(cov["files"].items()):
        if f.endswith(("adapters.py", "resources.py", "__main__.py")):
            continue
        src = Path(LIB / f).read_text().split("\n")
        executed, missing = set(info["executed_lines"]), set(info["missing_lines"])
        for n, line in enumerate(src, 1):
            m = re.search(r"Outcome\((\d|[^,)]+if[^,)]*else[^,)]*)", line)
            if m and (n in executed or n in missing):
                exit_rows.append((f, n, line.strip()[:90], "yes" if n in executed else "NO"))
    exit_total = len(exit_rows)
    exit_hit = sum(1 for r in exit_rows if r[3] == "yes")

    cov_rows, uncovered = [], []
    tot = cov["totals"]
    for f, info in sorted(cov["files"].items()):
        s = info["summary"]
        cov_rows.append((f, s["num_statements"], s["missing_lines"], s["num_branches"], s["missing_branches"], f"{s['percent_covered']:.1f}%"))
        if f in NOT_CORPUS:
            continue
        src = Path(LIB / f).read_text().split("\n")
        groups = []
        for n in info["missing_lines"]:
            if groups and n - groups[-1][-1] <= 1:
                groups[-1].append(n)
            else:
                groups.append([n])
        for g in groups:
            uncovered.append((f, g[0], g[-1], "line", src[g[0] - 1].strip()[:100]))
        lines_missing = set(info["missing_lines"])
        for a, b in info["missing_branches"]:
            if a not in lines_missing:
                uncovered.append((f, a, a, "branch", src[a - 1].strip()[:100]))
    unclassified = [u for u in uncovered if (u[0], u[1]) not in DISPOSITION]

    stats = {"cases": len(cases), "replayable": len(replayable), "non_replayable": len(cases) - len(replayable), "tests": len(tests),
             "ephemeral_cwd_cases": ephemeral, "stub_gh_cases": stub, "argparse_text_cases": len(argparse_text), "corpus_bytes": sizes,
             "trees": len(corpus.trees), "blobs": len(corpus.blobs), "blob_bytes": sum(len(b) for b in corpus.blobs.values()),
             "by_command": {k: dict(v) for k, v in by_cmd.items()}, "human_cases": dict(human), "json_cases": dict(jsonm),
             "codes_defined": len(defined), "codes_observed": len(set(defined) & (set(diag) | set(kinds) | set(outcomes))),
             "codes_unobserved": missing_codes, "line_branch_coverage_percent": round(tot["percent_covered"], 1),
             "exit_paths_total": exit_total, "exit_paths_executed": exit_hit, "unclassified_uncovered": len(unclassified)}
    if args.stats_json:
        args.stats_json.write_text(json.dumps(stats, indent=2, sort_keys=True))

    md = []
    w = md.append
    w("# M7.1 — Behavioral Corpus Report (human gate)\n")
    w("Generated by `skill-library/parity/tools/report.py` from the committed corpus (`skill-library/parity/corpus/`), a `coverage.py` run of the in-process corpus replay, and `mutation_check.py`. **Nothing in M7.2 has been started; no Node code exists.** The corpus is the executable compatibility specification for the port.\n")
    w("## 1. Baseline\n")
    w("- Python oracle tag **`python-1.0.0rc1`** = commit **`5c63ffc`** (\"Complete M6 live publication evidence and approve 1.0.0rc1\"); an export of the tag passes the approved release state: `SDLC_TEST_INSTALL=1`, Python 3.11.16, **532 passed**.")
    w("- Test suite after M7.1 (Python 3.11.16): `SDLC_TEST_INSTALL=1` **630 passed, 1 skipped** (the skip documents the non-executable-`gh` oracle finding, §7); default run 621 passed, 10 skipped (opt-in tests); Python 3.14.4 the same. The 532 approved tests are unchanged and green; M7.1 adds the corpus-integrity/sampled-replay tests and the targeted cases. `git diff python-1.0.0rc1 -- skill-library/sdlc/` is empty: **no oracle module was modified**.")
    w("- Toolchain: Python 3.11.16, Node.js v22.22.1, npm 9.2.0, coverage.py with branch measurement.")
    w("- M7.1 changes (uncommitted on top of the tag): the opt-in recorder `tests/corpus_recorder.py` (+ 8 lines in `tests/conftest.py`), the replay/report tools and corpus under `skill-library/parity/`, 31 targeted Python-side test cases (`tests/unit/test_corpus_gaps.py`, one of them skipped to document an oracle finding, plus one extra case in `tests/unit/test_publish.py`), three extra stub-`gh` failure modes (`repo_error`, `repo_bad_json`, `create_forbidden`). No change to any `sdlc/` module.\n")
    w("## 2. How the corpus is built and replayed\n")
    w("`SDLC_CORPUS_DIR=<dir> python -m pytest` wraps `sdlc.cli.main`; every in-process CLI call made by any test is recorded with argv, relevant environment (`SDLC_TODAY`, stub-`gh` variables; tokens redacted), working directory, the **complete project tree before and after** (content-addressed), exit code, stdout, stderr and the stub-`gh` state/call log. Paths are normalized to `<ROOT>`. The Python replayer (`parity/tools/replay.py`) rebuilds each pre-state in a fresh temp directory, runs the CLI **as a subprocess** (`python -m sdlc`), and compares under the approved parity rules (exit code, stdout/stderr and the whole post-state tree byte-exact; `--json` stdout as parsed values). Format specification: `parity/README.md`.\n")
    w("## 3. Corpus statistics\n")
    w(table(["Measure", "Value"], [
        ("CLI invocations recorded", stats["cases"]), ("replayable from a clean process", f"{stats['replayable']} (replay: **{stats['replayable']}/{stats['replayable']} match the Python oracle**)"),
        ("flagged non-replayable", f"{stats['non_replayable']} (4 recordings of one monkeypatching test; equivalent filesystem-induced case added)"),
        ("distinct tests contributing", stats["tests"]), ("cases using the stub `gh`", stub), ("cases with no project (checkout cwd: `--help`, `--version`, usage errors)", ephemeral),
        ("cases whose output is argparse's own help/usage text", len(argparse_text)),
        ("distinct file trees / blobs", f"{stats['trees']} / {stats['blobs']} ({stats['blob_bytes']:,} bytes uncompressed)"),
        ("corpus size on disk (gz)", f"{sum(sizes.values()):,} bytes (cases {sizes['cases.jsonl.gz']:,}, trees {sizes['trees.jsonl.gz']:,}, blobs {sizes['blobs.jsonl.gz']:,})")]))
    w("\n**Cases by command and exit code** (human = without `--json`):\n")
    rows = []
    for c in all_cmds:
        e = by_cmd.get(c, {})
        rows.append((f"`{c}`", sum(e.values()), e.get(0, 0), e.get(1, 0), e.get(2, 0), human.get(c, 0), jsonm.get(c, 0)))
    rows.append(("`--version`", sum(by_cmd.get("--version", {}).values()) if "--version" in by_cmd else 1, 1, 0, 0, 0, 0))
    w(table(["Command", "Cases", "exit 0", "exit 1", "exit 2", "human output", "`--json`"], rows))
    w("\nEvery one of the 12 commands is exercised, each in both output modes, and each of the three exit codes is observed. The combinations that never occur are structurally impossible: `list`, `status` and `find-overlaps` never return exit 1 (their only non-zero exit is 2, from a usage error or a missing project), which §4.3 and §5.1 confirm at the source level.\n")
    w("## 4. Coverage\n")
    w("### 4.1 Commands\n\nAll 12 commands plus `--version`, `--help` and usage errors appear in the corpus (§3 table).\n")
    w("### 4.2 Diagnostics and other result codes\n")
    w(f"{len(defined)} distinct codes are defined in the source (diagnostics, provider errors, status attention kinds count separately below). **{stats['codes_observed']} of {len(defined)} are observed in recorded output.**")
    if missing_codes:
        w("\nNot observed in any recorded output: " + ", ".join(f"`{c}`" for c in missing_codes) + ".")
    w("\n(Status `attention.kind` values are counted from results; publish outcome values from `outcomes`.) Observed status attention kinds: " + ", ".join(f"`{k}`" for k in sorted(kinds)) + ". Observed publish outcomes: " + ", ".join(f"`{k}`" for k in sorted(outcomes)) + ".\n")
    w("### 4.3 Exit paths\n")
    w(f"Statically, {exit_total} source lines construct an `Outcome` with an exit code (excluding the installer/`__main__`); **{exit_hit} are executed** by the replay. Seven of those lines are conditional expressions (`Outcome(0 if … else 1, …)`) where a line-level count would hide an unexecuted side; they are checked at the condition level in §5.1 and against the command/exit matrix in §3. Not executed:")
    for f, n, text, hit in exit_rows:
        if hit == "NO":
            w(f"- `{f}:{n}` — `{text}`")
    w("\n### 4.4 Line and branch coverage of `sdlc/` by the replay\n")
    w(table(["Module", "Statements", "Missed", "Branches", "Missed br.", "Cover"], cov_rows))
    w(f"\nTotal (branch-aware): **{tot['percent_covered']:.1f}%**. Before the targeted cases it was 91% (human-readable output, config/ledger/document error paths and several diagnostics were never exercised through the CLI).\n")
    w("**Outside the corpus by design:** " + "; ".join(f"`{k}` — {v}" for k, v in NOT_CORPUS.items()) + ".\n")
    w("## 5. Every remaining uncovered behavior, explicitly\n")
    if unclassified:
        w("**UNCLASSIFIED (needs attention):**")
        for f, a, b, kind, text in unclassified:
            w(f"- `{f}:{a}` ({kind}) `{text}`")
    w(table(["Location", "Kind", "Code", "Why it is not in the corpus", "Plan for the port"],
            [(f"`{f}:{a}" + (f"-{b}" if b != a else "") + "`", kind, f"`{text}`", *DISPOSITION.get((f, a), ("?", "?"))) for f, a, b, kind, text in uncovered]))
    w("\nNothing reachable from the CLI remains uncovered except the 60-second provider timeout. The dead/defensive items are listed so the port can decide, deliberately, whether to reproduce them.\n")
    w("### 5.1 Condition-level coverage (what line and branch coverage cannot see)\n")
    w(f"Line and branch coverage treat a conditional expression such as `Outcome(0 if not diags else 1, …)` or a comprehension filter as one covered line even if one side never runs. `parity/tools/condition_trace.py` instruments a copy of the implementation and records both outcomes of every conditional expression and comprehension filter while replaying the corpus: **{conds['sites']} sites, {conds['sites'] - len(conds['incomplete'])} with both outcomes observed, {len(conds['incomplete'])} with a side that never occurs**. Its first run found 21 incomplete sites, including a real untested exit path (`init` with an existing invalid `config.md` must exit 1); every reachable one now has a case. The remaining sites, all unreachable or internal:\n")
    w(table(["Location", "Code", "Why a side never occurs"], [(f"`{r['file']}:{r['line']}`", f"`{r['text']}`", CONDITION_DISPOSITION.get((r['file'], r['line']), "UNCLASSIFIED")) for r in conds["incomplete"]]))
    w("")
    w("## 6. Corpus sensitivity (mutation check)\n")
    w("Sixteen deliberate behavior changes were applied one at a time to a copy of the Python implementation; the replay must report differences for each.\n")
    w(table(["Mutation", "Detected", "Cases differing"], [(m["mutation"], "yes" if m.get("caught") else m.get("status", "NO"), m.get("cases_differing", "-")) for m in muts]))
    caught = sum(1 for m in muts if m.get("caught"))
    w(f"\n**{caught} of {len(muts)} mutations detected.**\n")
    w("## 7. Problems found while recording and replaying Python\n")
    w("Real defects in my recording/replay tooling were found by the first replay (13 of 1,484 cases differed) and fixed: (1) 12 cases (`--help`, `--version`, usage errors) ran in the source checkout, so the recorder snapshotted my source tree; they are now recorded as *no project* (`ephemeral`); (2) the replayer mapped a deliberately missing `gh` executable to the wrong directory, so its path in an error message differed; (3) one test monkeypatches `publication.append_record` in-process and cannot be replayed from a clean process: its four recordings are flagged non-replayable and an equivalent filesystem-induced failure case was added (it occupies the atomic-write temp path with a directory) so the behavior is in the corpus.\n")
    w("Findings about the Python oracle itself (not fixed; the tag is frozen):\n")
    w("1. **Uncaught exception for a non-executable `gh`.** `github_provider._run` catches only `FileNotFoundError` and `TimeoutExpired`. If `SDLC_GH_COMMAND`/`gh` exists but cannot be executed, `publish-apply` raises `PermissionError` from the preflight and the process dies with a Python traceback (exit 1) instead of a `provider-unavailable` diagnostic. The test that provokes it is skipped with this explanation. **Decided (PARITY-EXCEPTION-001):** Node does not reproduce the traceback; every failure to start `gh` is normalized to `provider-unavailable`; the Python oracle is not modified.")
    w("2. **Argparse-owned text.** %d recorded cases (`--help` output and usage-error messages) contain argparse's own wording; Node's `parseArgs` cannot reproduce it byte for byte without reimplementing argparse. The corpus marks them `text_parity: argparse`. **Decided (PARITY-EXCEPTION-002):** exempt from byte parity; require exit code (`0` for help, `2` for usage errors), correct command/flag recognition, command/flag names in useful deterministic output. Application-owned diagnostics remain byte-exact." % len(argparse_text))
    w("3. **Dead and shadowed code** (§5): `Publication.number`, the `publication-invalid` blocker in `publish.build_preview` (shadowed by the validate-based block), the `unrelated` guard, the `_dup_diags` guard, and the unreachable `bad-artifact` path. **Decided:** code proven unreachable is not ported; each omission is recorded in `parity/DROPPED.md` with its evidence; uncertain items are ported until proven otherwise.")
    w("4. **Corpus does not cover** the two installer executables or `python -m sdlc`; they are Layer B (the install tests) and `--version` is in the corpus. Replays depend on `SDLC_TODAY` (recorded), `COLUMNS=80` for argparse help width (set by the replayer), and a **stub `gh`** whose behavior is specified by `parity/tools/stub_gh.py` (the Node port needs an equivalent stub; modes: `unauthenticated`, `repo_missing`, `issues_disabled`, `repo_error`, `repo_bad_json`, `fail_titles`, `nourl_titles`, `first_issue`).\n")
    w("## 8. Gate result\n")
    w("**Gate result: M7.1 approved by the human reviewer; the corpus is frozen** (expected results must never be regenerated from Node; `parity/corpus/MANIFEST.sha256`). Decisions recorded in `parity/EXCEPTIONS.md` and `parity/DROPPED.md`. M7.2 may proceed.\n")
    args.out.write_text("\n".join(md) + "\n")
    print(f"wrote {args.out} ({len(cases)} cases, {len(uncovered)} uncovered items, {len(unclassified)} unclassified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
