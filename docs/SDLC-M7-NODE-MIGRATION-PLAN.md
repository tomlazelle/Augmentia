# M7 — Node.js / TypeScript Migration Plan (for human review)

**Status:** **Approved** (decisions in §1a). M7.0 and M7.1 are complete and the M7.1 corpus is **approved and frozen**; M7.2 → M7.5 proceed incrementally with **no further human gate until the M7.6 parity/removal gate**, unless the port exposes a genuine contract question (then stop and ask). The Python implementation (`sdlc-skill-library` 1.0.0rc1, M1–M6 approved) is the behavioral oracle, tagged `python-1.0.0rc1` (commit `5c63ffc`).
**Authority:** `docs/SDLC-SKILL-ARCHITECTURE.md`, then `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`. This plan amends the architecture (§4); the amendments are approved (§1a).

## 1. Objective and decisions already made

Move the whole product (CLI, installers, packaging, tests, documentation) from Python to Node.js so it installs and runs as a standard npm package, with **no change to any approved M1–M6 behavior**. The 15 Skills are agent-agnostic Markdown and stay as they are, except for text that names Python, `pipx` or `pip`.

| Decision | Choice (from your answers) |
|---|---|
| Language | **TypeScript**, compiled to JavaScript for the published package |
| Runtime baseline | **Node.js 22 LTS and newer** (`engines: ">=22"`), the single baseline as Python 3.11 was |
| Python implementation | **Kept as the reference oracle until parity is proven, then removed** (preserved in git history by tag) |
| Order of work | **This plan is reviewed first; no code until you approve it** |

## 1a. Approved decisions (human review of this plan)

- **Architecture:** TypeScript compiled to JavaScript; Node.js ≥ 22; one YAML runtime dependency; npm replaces pip/pipx distribution; `node:test` is the test runner; target version `2.0.0-rc.1`; `python -m sdlc` is removed together with the Python implementation (the public command is `sdlc`).
- **Oracle:** Python remains the behavioral oracle until parity is approved.
- **Package identity:** proposed `@augmentia/sdlc`, subject to scope/name availability; the executable stays `sdlc`. M7 validates installation from the **generated tarball**; publishing to the public npm registry is a final release action, **not** a prerequisite for parity.
- **Windows:** out of scope for M7 (its own future milestone); M7 preserves the validated Linux behavior.
- **`--json` parity:** semantic/value parity (§6.5). **Human-readable CLI output, diagnostics and generated filesystem content:** byte parity unless explicitly documented otherwise.
- **Live GitHub:** no second live Issue; M7 proves the same preview/digest/provider invocation against the oracle and the stub.
- **Licence:** MIT, assuming broad adoption including commercial use; `LICENSE` at the repository root and `"license": "MIT"` in `package.json`, to be added before npm publication (M7.5). A different licence is a separate decision before M7.5.
- **M7.1 gate (approved):** the corpus is accepted as the executable compatibility specification and is now a **frozen M7 asset**: expected results originate from `python-1.0.0rc1` and are never regenerated from Node (`parity/corpus/MANIFEST.sha256` + a test lock the files). The unreachable `bad-artifact`, the 60-second provider timeout and the race condition are accepted, disclosed limitations.
- **Decision 1 — spawn-failing `gh`:** Node does **not** reproduce Python's uncaught `PermissionError`/traceback; any inability to start the GitHub CLI is normalized to the existing `provider-unavailable` failure. Approved parity exception **PARITY-EXCEPTION-001**; Node regression test required; the tagged Python oracle is not modified.
- **Decision 2 — argparse-owned text:** the 12 argparse-generated cases are exempt from byte parity of prose (**PARITY-EXCEPTION-002**, a platform-runtime presentation exception, not a behavioral discrepancy). Required: exit code 2, correct command/flag recognition, command/flag names in useful deterministic output, documented behavior. Application-owned diagnostics stay byte-exact.
- **Decision 3 — dead code:** the Python code is a behavioral oracle, not a source oracle. Code proven to have no reachable behavior is not ported; each omission is recorded with symbol, reason and evidence in `parity/DROPPED.md`. Uncertain reachability => port. No redesign of reachable internals.
- **Layout adjustment (recorded):** until Python is removed in M7.6 the Node project lives in `skill-library/node/` (the oracle's paths stay untouched); it moves to the package root with the Python removal. Oracle changes must remain **zero**.
- **Further gates:** none between M7.2 and M7.6 unless the port exposes a genuine contract question.

## 2. Scope

**In scope:** the `sdlc` CLI (all 12 commands: `init`, `allocate-id`, `retire-id`, `create-dir`, `update-map`, `list`, `references`, `find-overlaps`, `status`, `publish-preview`, `publish-apply`, `validate`; `--root`, `--json`, `--version`, exit codes and JSON envelope per `shared/cli-contract.md`), the two installers (`sdlc-install-claude-code`, `sdlc-install-codex`), the packaged Skill library and templates, npm packaging, the test suite, the README/user guide, and the Skill/doc text that names Python.

**Size of the port:** 2,739 lines of Python in 19 modules; 532 tests in 21 files; 2.9 MB of fixtures in 31 directories; 15 Skills (479 lines of `SKILL.md` plus references). PyYAML is the only runtime dependency today.

**Non-goals (unchanged from M6, plus):** no new features, no contract changes, no Jira, no sync, no UI; no Windows support work unless you decide otherwise (§10); no rewrite of the Skills' behavior.

## 3. Invariants

- Every approved contract holds: CLI contract, validator codes/severities/exit codes, ID and ledger rules, map generation, overlap scoring, R2 evidence formats, R3 preview/digest/confirmation gate, Publication records, create-if-missing instruction files, local Markdown authority.
- Behavior is judged against the **Python oracle**, not against the Node author's reading of the spec (§5).
- Tests must distinguish stubbed from live external behavior (as in M5/M6).
- Human approval remains required at the gates in §7. Nothing is self-approved.

## 4. Architecture amendments requiring your approval

1. **§9 / §14 runtime:** "Python ≥ 3.11 and PyYAML" becomes "Node.js ≥ 22 and one YAML library"; "initially installed from the repository (`pip install -e .`), `pipx` in M6" becomes "installed as an npm package (`npm install -g`, `npx`)".
2. **Dependency policy:** exactly one third-party runtime dependency (a YAML parser, §6.1). Everything else from the Node standard library (`node:fs`, `node:path`, `node:crypto`, `node:child_process`, `node:util` `parseArgs`). Dev-only: `typescript` and a type package; tests use the built-in `node:test` runner (no test framework dependency).
3. **Distribution:** the `skills/` and `shared/` trees are bundled into the npm tarball (`library/`) at build time, as today's wheel does; the three commands become `bin` entries.
4. **Versioning:** `2.0.0-rc.1`, since the runtime and install method change (behavior does not).
5. **`python -m sdlc`** disappears with the Python implementation; the Skills already say `sdlc`, so Skill invocations do not change.

## 5. Proving parity: the oracle and the corpus

The risk in a rewrite is silent drift. The plan is to make the Python implementation prove the Node one wrong or right, mechanically.

**Layer A — recorded corpus (primary).** Instrument the existing Python test harness (`Sandbox.run` in `tests/conftest.py`) so every CLI invocation made anywhere in the 532-test suite is recorded with: argv, environment overrides (`SDLC_TODAY`, stub `gh`), the complete pre-state file tree, exit code, stdout, stderr, and the complete post-state tree. This yields thousands of independent, self-contained cases (no hand-written scenarios) that include the M3–M6 fixtures and agent-produced projects. The corpus is committed, so it outlives Python. The Node CLI replays each case from its pre-state and must match, under the parity definition in §6.5: exit code, stdout, stderr and the post-state tree. Stdout/stderr and files are byte-exact; `--json` stdout is compared as parsed JSON values.

**Layer B — ported tests.** Tests that are not CLI replays are ported by hand to `node:test`: the Skill static tests (text and structure of all 15 Skills), README/documentation tests, packaging tests (build the tarball, install into an isolated prefix, run the entry points, adapters resolve packaged Skills), the stub-`gh` provider tests (the stub becomes a Node script), unit tests for parsers where a replay is not meaningful.

**Layer C — side-by-side differential run (before removal).** With both implementations present, a script runs the corpus plus extra generated inputs (every fixture project, mutated front matter, malformed documents, odd Unicode in titles) through both and diffs the results. Any disagreement is a defect in Node, or a decision for you if the Python behavior was itself accidental.

**Layer D — real agents.** From the npm-installed package, a reduced re-run of the M6 walkthrough with **both** Claude Code and Codex (init → a Story → a technical artifact → status → publish preview with the stub), plus Skill discovery. No new live GitHub Issue is planned; the digest and `gh` call arguments are compared against the oracle and the stub tests (confirm in §10).

## 6. Known porting hazards (each gets an explicit test)

1. **YAML semantics.** PyYAML `safe_load` is YAML 1.1 (`yes`/`no`/`on`/`off` are booleans, dates become date objects that `frontmatter._normalise` turns into ISO strings, `covers: []` and quoted values). JS parsers default to YAML 1.2. Choose a parser with a 1.1 mode (the `yaml` package supports `version: '1.1'`), keep the ISO-date normalisation, and assert identical parse results over every front matter in the corpus. Error messages for invalid YAML must keep the `invalid YAML: …` shape.
2. **Dates.** `SDLC_TODAY` and "today" are the **local** date; `Date#toISOString()` is UTC and would be a subtle bug near midnight.
3. **Sorting and comparison.** Python sorts strings by code point; JS default sort uses UTF-16 code units and `localeCompare` is locale-dependent. Use an explicit code-point comparator everywhere IDs, titles, paths or JSON keys are ordered, and for the digest's canonical JSON.
4. **Number formatting.** `find-overlaps` prints scores with `.2f` and returns floats; Python emits `1.0` where JS emits `1`, and `toFixed` rounds some edge cases differently. Implement the 2-decimal rounding exactly; compare JSON numbers by value (§6.5).
5. **JSON canonical form for the confirmation digest.** `publish`'s digest is SHA-256 over `json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"))`. Reproduce byte-identical canonicalization (key order by code point, no escaping of non-ASCII, same string escapes). **Success test: the Node digest equals the Python digest for every Story in the corpus.**
6. **Regular expressions.** Port each pattern deliberately (`\b`, `\w`, case folding, `re.MULTILINE`, Unicode flags); Markdown scanning is line-based and ports directly, but fences, headings and list-declaration patterns each get corpus coverage.
7. **File-system semantics.** Exclusive create for `init`'s instruction files (`wx`), `lstat`-based "exists even if it is a dangling symlink", atomic write-by-rename for ledger/maps/Story edits, symlink creation for adapters, and the "never remove a real directory or a foreign link" rule.
8. **Process and subprocess behavior.** `gh` via `spawnSync` with stdin, timeout and no shell; the same error classification (`provider-auth`, `repository-not-found`, `issues-disabled`, `provider-ambiguous`, …) and token redaction; the `SDLC_GH_COMMAND` override.
9. **Argument parsing and help text.** `argparse` usage errors exit `2` with its own wording; Node's `parseArgs` differs. Requirement: same commands, flags, exit codes (`2` for usage errors) and the documented behaviors; exact `--help` prose is not a contract, but the README/tests that name commands and flags must still pass.
10. **Line endings and encodings.** UTF-8 in, UTF-8 out; CRLF handling as in `render_issue`; no BOM surprises.
11. **Diagnostics text.** Messages are asserted by tests and read by agents; port them verbatim.

### 6.5 Parity definition (approved)
- **Byte parity (unless a deviation is specifically documented and approved):** human-readable CLI output (stdout and stderr), diagnostics text, exit codes, and all files the CLI writes (Markdown, maps, ledger, instruction files, Publication records).
- **Semantic JSON parity:** for `--json` output, the parsed values must be equal: strings, booleans, nulls, arrays, object members, and numeric values. Serialization whitespace, object-key order, and numerically equivalent representations such as `1` versus `1.0` are **not** parity failures. (This is the only stdout relaxation.)

## 7. Milestones and gates

| Step | Work | Exit criterion | Gate |
|---|---|---|---|
| **M7.0** Prerequisites | Commit M1–M6 and tag it `python-1.0.0rc1` (nothing since the baseline commit is committed yet); record Node/npm versions; approve this plan and §4 | Tag exists; plan approved | **You approve plan + amendments** |
| **M7.1** Oracle and corpus | Add recording to the Python harness; generate and commit the corpus; coverage report of commands/validator codes/diagnostics hit by the corpus; add targeted Python-side cases for any validator code or branch the suite never exercises | Corpus replays green against Python itself; every validator code, command and exit path is covered or explicitly listed as uncovered | **You review corpus coverage** |
| **M7.2** Node core | Scaffold (`tsconfig`, build, `node:test`), `model`, `frontmatter`, `markdown`, `ledger`, `ids`, `project`, `init`, `allocate-id`, `retire-id`, `create-dir`, CLI skeleton, `--json` envelope, exit codes | Corpus cases for these commands pass byte-for-byte | — |
| **M7.3** Maps, query, validate | `maps`, `list`, `references`, `find-overlaps`, `validate` including R1/R2/R3 rules | Corpus cases for these commands pass; scoring and diagnostics identical | — |
| **M7.4** Technical, status, publishing | `technical`, `status`, `publication`, `publish` (digest!), GitHub provider, redaction, stub `gh` in Node | All corpus cases pass; digests equal Python's for every Story; stub-`gh` scenarios pass | — |
| **M7.5** Packaging, installers, docs, Skills | `bin` entries, bundled `library/`, `npm pack`, isolated install tests, `sdlc-install-*` adapters, README/user guide rewrite, Skill/doc text edits (Python/`pipx`/`pip` mentions), `AGENTS.md`/`CLAUDE.md` templates | Install from the tarball in a clean prefix; adapters link packaged Skills; all Skill/README tests pass | — |
| **M7.6** Parity gate and release | Layer C differential run, Layer D agent run (both agents), full Node suite, remove Python (code, tests, `pyproject`, venv docs), M7 evidence document, checklist | Zero unexplained differences; both agents work from the npm install; evidence complete | **You approve parity result, then final sign-off** |

Python removal happens only in M7.6, after you approve the differential result. Any difference that is a *bug in Python* or an *accidental behavior* is listed for your decision (keep Python's behavior for parity, or change it deliberately); nothing is "improved" silently.

## 8. Target layout (proposal)

```text
skill-library/                  # package root (name unchanged during migration)
  package.json  tsconfig.json
  src/                          # TypeScript: cli.ts, model.ts, project.ts, ids.ts, ledger.ts, markdown.ts,
                                #   frontmatter.ts, maps.ts, query.ts, validate.ts, technical.ts, status.ts,
                                #   publication.ts, publish.ts, github.ts, adapters.ts, init.ts, resources.ts
  bin/                          # sdlc, sdlc-install-claude-code, sdlc-install-codex (thin launchers)
  skills/  shared/  templates/  # canonical, unchanged; copied into the tarball as library/ at build time
  test/                         # node:test suites; test/corpus/ (recorded cases); test/fixtures/ (existing m3–m6)
  python/                       # existing implementation, retained only until M7.6 (then removed; tag keeps it)
```

## 9. Risks

| Risk | Mitigation |
|---|---|
| Silent behavior drift in a large port | Recorded corpus + differential run + digest equality; Python stays until parity is approved |
| YAML 1.1 vs 1.2 differences change how documents parse | Dedicated parser choice and tests over every corpus front matter (§6.1) |
| Corpus misses a code path | Coverage report at the M7.1 gate; add targeted cases before porting |
| TypeScript build adds friction for contributors | `npm run build`/`npm test` documented; `node:test` needs no extra framework |
| Agents' Skill behavior depends on CLI wording | Diagnostics ported verbatim; Layer D re-runs both agents |
| Scope creep ("while we're porting…") | M6 non-goals still apply; any improvement is a numbered decision for you |

## 10. Open questions for you

1. **(Decided — §1a)** **Package name and registry.** Publish to npm (name or scope?), or distribute as a tarball/Git install for now? (`npm install -g ./skill-library` works regardless; I have not assumed a registry.)
2. **(Decided — §1a)** **Windows.** Node makes it feasible, but symlink adapters need privileges or junctions. Out of scope for M7 unless you want it (a separate, smaller milestone).
3. **(Decided — §6.5)** **JSON byte-identity**: value-equal (recommended) or byte-identical?
4. **(Decided — §1a)** **Live GitHub in the final gate.** Recommended: no second live Issue; the provider boundary is compared against the oracle and stub tests. Do you want one live re-run?
5. **(Decided — §1a)** **Licence:** MIT; package metadata to be completed in M7.5.

## 11. Progress

- **M7.0 — done.** M1–M6 were already committed (`5c63ffc`, "Complete M6 live publication evidence and approve 1.0.0rc1"); annotated tag **`python-1.0.0rc1`** created on that exact commit. An export of the tag (`git archive`) passes the approved release state: `SDLC_TEST_INSTALL=1`, Python 3.11.16, **532 passed**. Toolchain recorded: Node.js v22.22.1, npm 9.2.0, Python 3.11.16.
- **M7.1 — done; stopped at its human gate.** Corpus, tools and report: `skill-library/parity/` and `docs/SDLC-M7-1-CORPUS-REPORT.md`. The corpus replays 100% against the Python oracle; 16/16 mutations are detected. Awaiting your approval of the corpus and decisions on three open points (report §7–§8).
- **M7.2 — done** (Node core): 24 Node tests pass; 1,351 applicable corpus cases: 1,342 byte-exact + 9 under approved exemptions, 0 failed; Python oracle changes zero. Report: `docs/SDLC-M7-2-REPORT.md`.
- **M7.3 — done** (maps, list, references, find-overlaps, validate): 34 Node tests; 1,629 applicable corpus cases: 1,616 exact + 13 under approved exceptions, 0 failed; 54/54 validator codes implemented and observed with contracted severities; overlap-score parity (15,020 formatting + 4,000 score cases); 26/26 mutations detected; oracle changes zero. Report: `docs/SDLC-M7-3-REPORT.md`. PARITY-EXCEPTION-004 and -005 approved.
- **M7.4 — done** (technical, status, publish-preview/apply, GitHub provider, digest): 91 Node tests; 1,844 applicable corpus cases (1,831 exact + 13 exempt), 0 failed; digest equality 100%; sensitivity matrix matches oracle; provider failure matrix incl. EX-001 mechanisms; EX-006 proposed. Report: `docs/SDLC-M7-4-REPORT.md`.
- **M7.5 — done** (packaging, adapters, docs, Skill text, MIT): 146 Node tests; tarball installs and runs from a clean prefix; adapters link packaged Skills; corpus unchanged (1,831 exact + 13 exempt, 0 failed). Report: `docs/SDLC-M7-5-REPORT.md`. Next: M7.6 (needs your approval of the parity result).
- **M7.6 — done, awaiting final sign-off**: Layer C differential (41,783 inputs), Layer D (Claude Code and Codex from the npm tarball), EX-006 and EX-007 approved, Python removed after the evidence passed (tag `python-1.0.0rc1` is the permanent oracle), Node project moved to the package root. Evidence: `docs/SDLC-M7-EVIDENCE.md`.
- M7.4 (status, publish-preview/apply, provider, digest) onward proceeds without a gate until M7.6.
