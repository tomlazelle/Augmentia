# Behavioral corpus (M7)

An executable compatibility specification for the `sdlc` CLI, recorded from the Python reference implementation (tag `python-1.0.0rc1`). The Node/TypeScript implementation reproduces every case. The corpus outlives the Python code: it is plain data, and the Node replayer needs no Python.

```text
parity/
  corpus/             the frozen corpus (MANIFEST.sha256 locks it)
    cases.jsonl.gz    one recorded CLI invocation per line
    trees.jsonl.gz    {"id", "entries"}  content-addressed project file trees
    blobs.jsonl.gz    {"id", "enc": "utf8"|"base64", "data"}  content-addressed file contents
    skipped.json      invocations the recorder could not represent (empty)
  EXPECTATIONS.sha256, yaml-expectations.json, numeric-expectations.json, digest-matrix.json
                      oracle-derived expectation files (frozen; never regenerated from Node)
  EXCEPTIONS.md       approved parity exceptions EX-001 .. EX-007
  DROPPED.md          register of Python code that was proven unreachable and not ported
  pre-removal-evidence/  final Python/Node regression results and the Layer C differential run (≈ 42,000 inputs)
  agent-evidence/     Layer D: Claude Code and Codex lifecycle transcripts from the npm-installed package
  oracle-tools/       Python tools that need the Python oracle (check out tag python-1.0.0rc1 to run them):
                      recorder-side generators, report/coverage/mutation tools, differential.py, stub_gh.py
```

**The corpus is a permanent regression suite.** It records the externally observable behavior of the 1.0 implementation (1,848 CLI invocations). The Node implementation replays it in `npm test` (`test/corpus.test.ts`; `node dist/test/corpus-report.js` prints a per-command report). A change to the corpus or the expectation files requires an explicit, reviewed decision; they are never regenerated from the Node implementation.

## Case format (`cases.jsonl.gz`)

```jsonc
{
  "id": "tests/unit/test_x.py::test_name#2",   // test node id + call sequence within the test
  "argv": ["publish-apply", "US-001", "--confirm-digest", "sha256:…", "--json"],
  "env": {"SDLC_TODAY": "2026-09-29", "SDLC_GH_COMMAND": "<STUB_GH>", "FAKE_GH_STATE": "<GH_STATE>", "GH_TOKEN": "<TOKEN>"},
  "cwd": "BR",                  // working directory relative to the project tree root ("." if the root)
  "ephemeral": false,           // true: no project (e.g. --help/--version/usage errors); pre/post are the empty tree
  "pre": "<tree id>",           // project tree before the call
  "gh_pre": {"mode.json": "…"}, // stub-gh state directory contents before (null if no stub)
  "replayable": true,           // false: recorded under in-process monkeypatching; skip (reason in not_replayable_reason)
  "text_parity": "exact",       // "argparse": output is argparse help/usage prose (see Exemptions)
  "expected": {
    "exit": 0, "stdout": "…", "stderr": "…",
    "post": "<tree id>",        // project tree after the call
    "gh_post": {"calls.jsonl": "…"}   // stub-gh state after (null if no stub)
  }
}
```

**Trees.** `entries` maps a relative path to `["f", <blob id>]` (file; sha-256 of the bytes), `["l", <target>]` (symlink) or `["d"]` (directory); the tree root itself is not listed. Empty directories matter (`unexpected-directory`, `init`). File modes and mtimes are not part of the contract.

**Normalization.** The absolute project root appears in recorded stdout/stderr/argv as the literal `<ROOT>` (replace with the real temp directory when replaying, and normalize the actual output the same way before comparing). `argv` entries may contain `<ROOT>/relative` (the `--root` option). Environment placeholders: `<STUB_GH>` = path of an executable named `gh` implementing `tools/stub_gh.py`; `<MISSING_GH:name>` = a path `<ROOT>/name` that does not exist; `<GH_STATE>` = a writable directory holding the stub's state files; `<TOKEN>` = any placeholder token. The replayer must clear every other `SDLC_*`, `GH_*`, `GITHUB_*` variable and set `COLUMNS=80`.

## Replay procedure (what any implementation must do)

1. Materialize `pre` into a fresh temp directory; create the stub-gh state directory from `gh_pre`; install the stub.
2. Run `sdlc <argv>` (with `<ROOT>` substituted) in `cwd`, with the case environment and nothing else inherited that matters.
3. Compare under the **approved parity rules** (`docs/SDLC-M7-NODE-MIGRATION-PLAN.md` §6.5):
   - exit code: equal;
   - stdout / stderr: **byte-equal**, except that when `argv` contains `--json` and expected stdout is non-empty, the two stdout documents are compared as **parsed JSON values** (key order, whitespace, `1` vs `1.0` are not differences);
   - the complete post-state project tree: same paths, types and file bytes;
   - the stub-gh `gh_post` state (the provider call log: argv and stdin bodies): equal.

## Exemptions (decided at the M7.1 gate)

- `replayable: false` cases are skipped (4 recordings of one monkeypatching test; an equivalent filesystem-induced case is in the corpus).
- `text_parity: "argparse"` cases (help output and usage errors) contain argparse's own prose; the proposal is exit-code parity plus command/flag names, not byte parity. Pending your decision (report §7).

## Replaying and extending

```bash
cd skill-library && npm test                       # includes the corpus replay and the frozen-file checksums
node dist/test/corpus-report.js [--commands a,b]   # per-command results
node scripts/mutation-check.mjs                    # corpus sensitivity: deliberate behavior changes must all be detected
```

Regenerating oracle-derived data (corpus, expectations) needs the Python implementation: `git checkout python-1.0.0rc1`, then see the tools in `oracle-tools/`. Any new regression case for 2.x should be added as a Node test; extending the frozen corpus is a separate, reviewed decision.
