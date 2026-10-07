# M7 evidence — Node.js/TypeScript migration, parity gate and Python removal

Status: **approved by the human reviewer** (M7 sign-off and `@augmentia/sdlc` 2.0.0-rc.1 as the Node release candidate). npm registry publication is a separate action and is **not** authorized yet.

## 1. Final differential gate (Python and Node both present)

| Check | Result |
|---|---|
| Frozen corpus, Python oracle | 1,844 replayable cases: 1,844 matched, 0 differed (4 monkeypatch-only recordings flagged non-replayable) |
| Frozen corpus, Node | 1,844 applicable: **1,831 byte-exact (`--json` as parsed values) + 13 exempt** (12 argparse help/usage prose = EX-002, 1 version string = EX-003); **0 failed** |
| Layer C differential run (`parity/oracle-tools/differential.py`) | Same inputs through Python and Node: fixture projects, 140 corpus project trees, per-document mutations (dropped/emptied/corrupted keys, broken YAML, BOM, CRLF, CR, tabs, NUL, invalid UTF-8, truncation, duplicate keys, broken links, …), 27 Unicode/odd titles, stub-gh publish flow. **Seed 20260929: 19,233 inputs; seed 7: 22,550 inputs; total 41,783.** Every one agrees on exit code, stdout/stderr, complete post-state tree and `gh` call log, apart from the approved exceptions (EX-007 inputs: 539 in the first seed, checked against the EX-007 rule) |
| Defects the differential run found and fixed in Node (no decision needed) | (a) argparse treats an unknown `-…` argument that contains a space as a value (`--title "- dash start"`); (b) a YAML timestamp title/purpose must render as Python's `str(datetime)`, not `repr`. Both have regression tests (`test/differential-regressions.test.ts`) |
| Decision taken at this gate | Non-UTF-8 project files: Python leaks a `UnicodeDecodeError` traceback; Node reports `invalid-encoding` (EX-007, your decision "clear error diagnostic") |
| Digest equality | **100%**: 81 digest-bearing corpus runs / 29 distinct digests identical, every Story item byte-identical; 26/26 digest-matrix scenarios equal to the oracle (14 must-change, 12 must-not-change); every publish-preview in the 41,783-input differential run agreed |
| Python regression (before removal) | default suite 623 passed / 10 skipped; `SDLC_TEST_INSTALL=1` 632 passed / 1 skipped (Python 3.11.16); `skill-library/sdlc/` unchanged vs tag `python-1.0.0rc1` (empty diff). Files: `parity/pre-removal-evidence/python-regression.txt` |
| Node regression (before removal) | 151 tests, 151 pass. `parity/pre-removal-evidence/node-regression.txt` |

Results and logs: `skill-library/parity/pre-removal-evidence/`.

## 2. npm-installed agent validation (`parity/agent-validation.mjs`, transcripts in `parity/agent-evidence/`)

Tarball installed into a clean prefix (`npm install --offline --prefix …`); agent `PATH` = installed `.bin` + Node + system dirs only (no checkout, no pipx). Adapter run from the installed package links 15 Skills into `.claude/skills` / `.agents/skills`, resolving inside the installed package. Seven headless sessions per agent: init → create-stories (standalone) → refine-stories (declared Ready, TBD accepted) → create-test-plan → sdlc-status → sdlc-validate → publish-stories (preview only, **not** confirmed). Stub `gh`; no GitHub Issue created.

| Agent | Version | Result |
|---|---|---|
| Claude Code (`claude -p`) | 2.1.283 | 12/12 checks pass (all turns exit 0; US-001 `Ready` with TBD preserved, status `Draft`; TEST-001 links the Story; `validate` 0 errors; installed-CLI preview returns `sha256:` digest, CREATE for `acme/widgets`; stub call log has no `issue create`; `status` ok) |
| Codex (`codex exec --sandbox workspace-write`) | codex-cli 0.159.3 | 12/12 checks pass (same checks) |

Runs kept: `agent-evidence/` (final tarball, Python-free tree), `agent-evidence/pre-removal-tarball/` (same lifecycle against the pre-removal tarball) and `agent-evidence/attempt-1-superseded/`. In attempt 1 Codex correctly stopped at `refine-stories` to ask whether to accept the unresolved TBD (my prompt had not pre-accepted it); the prompt was clarified for both agents and the whole lifecycle re-run. No Skill text was changed to make it pass.

## 3. Parity exceptions (all in `skill-library/parity/EXCEPTIONS.md`)

| ID | Summary | Status |
|---|---|---|
| EX-001 | Any failure to start `gh` → `provider-unavailable` (Python leaks `PermissionError`) | approved |
| EX-002 | argparse help/usage prose exempt (12 cases); exit codes and names required | approved |
| EX-003 | `sdlc --version` prints `sdlc 2.0.0-rc.1` | approved |
| EX-004 | YAML parser diagnostic prose after `invalid YAML:` | approved |
| EX-005 | ASCII-only numeric IDs | approved |
| EX-006 | Valid JSON with an invalid root from the provider → `provider-failed` (Python `AttributeError`) | approved |
| EX-007 | Non-UTF-8 project file → `invalid-encoding` (Python `UnicodeDecodeError` traceback) | approved (decision at this gate) |

## 4. Mutation sensitivity (final tree)

`node scripts/mutation-check.mjs`: 51 deliberate behavior changes to the compiled Node output; control run passes; **51/51 detected, 0 missed** (corpus replay or the oracle-derived tests: YAML, numeric, overlap ties, ASCII IDs, AC counting, digest matrix, provider matrix, publish semantics).

## 5. Package and environment identity

| | |
|---|---|
| Package | `@augmentia/sdlc` 2.0.0-rc.1, MIT (`LICENSE`: Copyright (c) 2026 Thomas La Zelle), `engines.node >=22`, one runtime dependency (`yaml`) |
| Tarball (validated) | `augmentia-sdlc-2.0.0-rc.1.tgz`, 73 files, 106,194 bytes, SHA-256 `1ca6d4b1a83d7c85bebef8219e16f659a9cd7514446cf8549b832369f50e05b9` (built from the Python-free tree) |
| Contents | `bin/` (3 executables), `dist/src`, `skills/` (15), `shared/` (7), `templates/`, `LICENSE`, `README.md`; no tests, sources, parity data or Python (tested) |
| Toolchain | Node v22.22.1, npm 9.2.0; Claude Code 2.1.283; codex-cli 0.159.3; Python 3.11.16 (oracle runs only) |
| Oracle | git tag `python-1.0.0rc1` → commit `5c63ffc351367a5d2eafb46709b05933b0c4883b` (permanent) |

## 6. Python removal (after §1–§3 passed)

Removed from the tree: `skill-library/sdlc/` (all Python modules), `tests/` (all Python tests, conftest, corpus recorder, stub), `install/`, `pyproject.toml`, `setup.py`, `MANIFEST.in`, build and egg-info directories. Moved, not removed: `sdlc/templates/` → `templates/`; `tests/fixtures/` (M3–M6 fixtures and agent transcripts) → `test/fixtures/`; the Node project from `skill-library/node/` to the package root `skill-library/`; Python parity tools → `parity/oracle-tools/` (historical, need the tag to run). Kept permanently: the frozen corpus and expectation files, `EXCEPTIONS.md`, `DROPPED.md`, all evidence, and the Node corpus replay in `npm test` (the corpus is now the 2.x regression baseline). The M4–M6 fixture projects still contain small Python sample projects (`textkit`, `tasklog`) as evidence of what the agents worked on; they are not part of the product or the package.

## 7. Post-removal release validation (Python-free tree)

| Check | Result |
|---|---|
| Fresh tarball from the Python-free tree, installed into a clean prefix | pass (also in `test/packaging.test.ts`: tarball contents, installed `sdlc`, release smoke sequence, both adapters, conflict/uninstall) |
| Complete Node suite | **151 tests, 151 pass** |
| Frozen corpus replayed against the *installed* package (`SDLC_BIN`) | 1,844 applicable: 1,831 exact + 13 exempt, **0 failed** |
| `sdlc`, `sdlc-install-claude-code`, `sdlc-install-codex` from the installed package | verified (packaging tests and both agent runs) |
| Packaged Skills/templates/shared without the checkout | verified (links resolve inside the installed package; `references/` and `../../shared/` resolve through the links) |
| Documentation scan | `README.md`, `skill-library/README.md`, Skills, shared docs and templates contain no `pipx`, `pip install`, `python -m sdlc`, virtualenv or PyYAML instructions (enforced by `test/readme.test.ts` and `test/packaging.test.ts`). Remaining "Python" mentions are the illustrative `python -m pytest` examples in `shared/technical-conventions.md` (an example of *a user project's* tests) and historical evidence documents |
| Secret scan of evidence | no token-shaped strings in docs, parity data, agent evidence or fixtures (`test/evidence-secrets.test.ts`) |

## 8. Outstanding limitations / TBDs

- Windows unsupported; user-scope (`~/.claude/skills`, `~/.agents/skills`) agent discovery still unverified (project scope is the verified path).
- The malformed-due-date behavior TBD noted at M6 for the release notes is unchanged.
- Documented non-contract limits: `!!binary`/`!!set` YAML tags unsupported; plain scalars folded across U+2028/U+2029.
- Disclosed since M7.1: unreachable `bad-artifact` case, 60-second provider timeout, check-then-act race.
- `npm install` of a published package needs the registry; M7 validated the tarball only (publishing to npm is a release action, not done).
- Copyright holder: confirm legal ownership before registry publication.
- Nothing from M7 is committed to git yet (the tag preserves the oracle).

## 9. Sign-off record

- [x] M7 human gate approved (parity, Python removal, release validation); PARITY-EXCEPTION-007 approved; EX-001 through EX-007 are the defined set of intentional deviations from `python-1.0.0rc1` (commit 5c63ffc).
- [x] `@augmentia/sdlc` 2.0.0-rc.1 approved as the Node release candidate.
- [ ] npm registry publication: **not authorized.** Requires separate explicit authorization after (a) copyright ownership is resolved (if Thomas La Zelle personally owns the work, "Copyright (c) 2026 Thomas La Zelle" is appropriate; if an employer or company owns it, use that legal owner) and (b) npm package and scope availability are confirmed.
- Initial Codex stop at `refine-stories` over the unresolved TBD is not a failure: the Skill respected the human-decision boundary.

Limitations accepted at the gate, unchanged: Windows unsupported; user-scope agent discovery unverified (project scope verified); the existing malformed-due-date TBD remains unresolved; historical fixtures containing Python samples are evidence, not runtime or package content; npm registry publication has not been exercised.
