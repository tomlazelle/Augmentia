# SDLC Skill Library — Implementation Checklist

Companion to [SDLC-SKILL-ARCHITECTURE.md](SDLC-SKILL-ARCHITECTURE.md). Check an item only when the work has been reviewed (documents) or tested (code). Nothing below is complete unless a human has confirmed it.

**Release mapping:** M2 + M3 = R1 · M4 = R2 · M5 = R3 · M6 = end-to-end validation and release.

## M1 — Architecture & Conventions

- [x] Architecture specification drafted (revision 2)
- [x] Review findings resolved in the specification (§13 table)
- [x] Implementation checklist drafted
- [x] Human review of architecture specification
- [x] Human review of this checklist
- [x] Supporting decisions and deferred items in architecture §14 confirmed
- [x] Conditional-approval corrections incorporated (PyYAML permitted, `covers: []` for standalone Stories, `.sdlc/` exempt from `map.md`)
- [x] **M1 approved by a human** (revision 3, including that coverage notices do not change the validator exit code)

**Exit criterion:** A human has approved the architecture and checklist; no unresolved contradictions remain; open items are recorded.

## M2 — Foundation (CLI / init / explore / validate)

- [x] Codex and Claude Code installation adapters (thin, no forked Skill content), each verified by installing a Skill (symlink adapters; `sdlc-init` invoked end-to-end from both `claude -p` and `codex exec`)
- [x] `pip install -e .` from the repository works and exposes `python -m sdlc`
- [x] `skill-library/` scaffold with `pyproject.toml` (Python ≥ 3.11) and `sdlc/` package
- [x] `shared/document-conventions.md`, `map-conventions.md`, `reference-conventions.md`, `cli-contract.md`
- [x] Front matter parser/validator using PyYAML (required fields, dates, status values, Story fields; `covers: []` accepted)
- [x] Coverage notices reported separately from errors (Stories with `covers: []`; uncovered **PR** requirements in R1); do not change exit code
- [x] `.sdlc/` exempt from map and front matter checks (tested)
- [x] `.sdlc/config.md` minimal schema implemented and validated (project_name, schema_version, directories, optional publishing)
- [x] ID ledger and `allocate-id` (documents and requirements), including tombstones via `retire-id`
- [x] `init` — idempotent, never overwrites documents
- [x] `create-dir` for Artifacts subdirectories on first use
- [x] `update-map` — generated regions only; hand-written sections preserved
- [x] `list`, `references`, `find-overlaps` (deterministic: category, normalized title, purpose, requirement references; scoring documented; ambiguous matches flagged for human confirmation)
- [x] `validate` — structure, front matter, filename/ID agreement, duplicate IDs (including simulated merge), retired IDs, broken links, `covers`, stale maps
- [x] CLI unit tests; `--json` output and exit codes tested per contract
- [x] `sdlc-init` Skill
- [x] `sdlc-explore` Skill
- [x] `sdlc-validate` Skill
- [x] Skills invoke the CLI; no duplicated filesystem algorithms in prompts (reviewed)
- [x] Empty-repo init and repeat init acceptance tested
- [x] Full suite executed under Python 3.11.16 (137 passed, including the editable-install test) and under 3.14
- [x] Correction pass: `requirement-uncovered` restricted to PR requirements; `--covers` hint vs Story `covers` (requirement IDs only) documented
- [x] **M2 approved by a human**

**Status:** Implementation, tests and the correction pass are complete; awaiting final human sign-off. `python -m pytest` in `skill-library/`: 137 passed under Python 3.11.16 with `SDLC_TEST_INSTALL=1`; 136 passed + 1 opt-in skipped otherwise (also green on 3.14).

**Exit criterion:** From an empty repository, `init` produces a valid structure; repeat `init` changes nothing; `validate` passes on it and reports each seeded fault (broken link, duplicate ID, stale map, bad front matter); all CLI tests pass.

## M3 — Business & Product (interview / BRD / PRD / stories)

Evidence: [SDLC-M3-EVIDENCE.md](SDLC-M3-EVIDENCE.md). Fixtures and transcripts: `skill-library/tests/fixtures/m3/`.

- [x] `shared/interview.md` shared interrogation guidance
- [x] `create-brd` Skill with section catalog, discovery questions, template
- [x] `create-prd` Skill with section catalog, discovery questions, template (works with or without a BRD)
- [x] `create-stories` Skill with `covers` IDs and source links
- [x] Overlap detection surfaced to the user before allocation in each creating Skill (workflow order tested; shown live for BRD in agent run `s6-overlap`; PRD/Stories order tested statically)
- [x] Material-edit rule (Approved → In Review) implemented in revision flows and tested (agent-run fixture `approved-revision`; holds only when a creating Skill is invoked, see evidence)
- [x] Sparse-idea → substantive BRD scenario acceptance tested
- [x] PRD without BRD scenario acceptance tested
- [x] Stories with working links and existing `covers` IDs acceptance tested
- [x] Standalone Story (`covers: []`) → `story-no-coverage` notice, exit 0
- [x] Removed requirement → tombstone, no recycling, Stories reconciled; requirement move reconciliation (CLI-level test)
- [x] Unknown/TBD answers handled without fabrication (reviewed in generated BRD/PRD/Stories fixtures; see observed issues)
- [x] Maps accurate after each creation scenario (every fixture validates; `update-map` is a no-op on each)
- [x] Both adapters install all Skills; Skills invoked end-to-end from Claude Code and Codex
- [x] Correction pass after review: mandatory recap; verbatim overlap presentation; `AGENTS.md`/`CLAUDE.md` guidance; standalone PRD fixture repaired; unresolved acceptance kept TBD (see evidence doc)
- [x] Full suite under Python 3.11.16 after corrections: 242 passed with `SDLC_TEST_INSTALL=1`
- [x] **Human review of generated BRD, PRD and Story content** (conditionally accepted; corrections above applied)
- [x] **M3 approved by a human**

**Exit criterion:** All R1 acceptance criteria in architecture §11 pass on fixture projects, and a human has reviewed a BRD, PRD and story set produced by the Skills. R1 is complete.

## Post-M3 Hardening (approved follow-ups to R1)

Both items were decided after M3 review. They change `sdlc init` (an authorised extension of the M2 CLI contract, documented in `shared/cli-contract.md`) and the three creating Skills. Evidence: [SDLC-M3-EVIDENCE.md](SDLC-M3-EVIDENCE.md) → "Post-M3 hardening".

- [x] `sdlc init` installs the centrally maintained `AGENTS.md` and `CLAUDE.md` into the project root, create-if-missing
  - [x] Canonical templates packaged with the CLI (`sdlc/templates/`, setuptools package data); `install/project-instructions/` now only documents them
  - [x] Existing files, symlinks and dangling symlinks are never read, appended to or overwritten (exclusive-create, `lexists` check)
  - [x] Repeat `init` is idempotent (bytes and mtimes unchanged); a deleted file is recreated without touching the other
  - [x] Instruction files are outside maps and `validate` rules; contract, architecture layout and `sdlc-init` Skill updated
  - [x] Regression tests in `tests/unit/test_init.py`; non-editable install ships the templates (`SDLC_TEST_INSTALL=1`)
- [x] Contextual overlap review in `create-brd`, `create-prd`, `create-stories`
  - [x] Runs after the deterministic CLI check and before `allocate-id`, even when the CLI returns no candidates
  - [x] Inspects existing titles, purposes and map summaries (`list --category`, `<dir>/map.md`; Stories also existing coverage)
  - [x] Presented separately as "Conceptual overlaps (my judgement, not CLI-scored)", never with a score, percentage or level
  - [x] Human chooses revise / relate (new document + `Related To` link) / create new before any ID is allocated
  - [x] Static regression tests for all three Skills; fixture tests pin that the CLI misses these same-topic requests; agent runs on Claude Code (BRD, PRD, Story; BRD "relate" branch written and validated)
- [x] Full suite under Python 3.11.16 with `SDLC_TEST_INSTALL=1`: see status line
- [x] **Human review of post-M3 hardening**

**Status:** Complete and human-approved. Final result under Python 3.11.16: **261 passed** with `SDLC_TEST_INSTALL=1` (259 passed + 2 opt-in skipped by default; also green on 3.14).

**R1 (M2 + M3 + post-M3 hardening) is complete and approved.** Carried forward: one M6 acceptance item (real Codex session for contextual overlap handling).

## M4 — Technical SDLC (R2)

Evidence: [SDLC-M4-EVIDENCE.md](SDLC-M4-EVIDENCE.md). Fixtures and transcripts: `skill-library/tests/fixtures/m4/`. R2 contract: architecture §15 and `skill-library/shared/technical-conventions.md`.

- [x] R2 contract drafted: `delivery_status` transitions, invalidation, artifact templates, evidence formats, review gating (architecture §15, `technical-conventions.md`)
- [ ] **Human approval of the NEW R2 semantics** (transition table, invalidation rule incl. amendment of the M3 delivery rule, evidence records, validator enforcement, review gating — evidence doc §2)
- [x] Shared technical conventions and templates (DES, PLAN, TEST, optional RES) with section catalogs and discovery questions
- [x] `refine-stories`
- [x] `create-design` (`DES-NNN`, optional `RES-NNN`)
- [x] `plan-implementation` (`PLAN-NNN`)
- [x] `implement-story` (sets `Implemented` only; records what changed and tests actually run)
- [x] `review-implementation` (read-only; not verification)
- [x] `create-test-plan` (`TEST-NNN`; TBD kept out of executable scenarios)
- [x] `verify-story` reports actual results only; sets `Verified` only from real results
- [x] Uniqueness, filename, front matter and link validation covers DES, PLAN, RES, TEST (seeded faults detected)
- [x] R2 validator rules: Implementation Record, Verification Runs, `Verified` evidence, criteria/TBD warnings (+ `Artifacts/tests/evidence/` allowed) — documented in `shared/cli-contract.md`
- [x] Technical Skills inspect repository code and related requirements before proposing (Repository Context sections; cited paths checked against the fixture repo)
- [x] R1 overlap workflow (CLI check, contextual review, human decision) preserved in the three artifact-creating Skills
- [x] `AGENTS.md`/`CLAUDE.md` templates route technical artifacts and delivery changes (still create-if-missing on `init`)
- [x] Both adapters install all Skills; every R2 Skill executed in a real session by both Claude Code and Codex (evidence §9)
- [x] End-to-end Ready → In Progress → Implemented → Verified with real code changes and executed tests (`us001-chain-verified`, `us002-codex-standalone`)
- [x] Failed, blocked, not-run and TBD cases do not produce Verified (fixtures + forged-Verified tests)
- [x] Rework after verification supersedes prior evidence without misrepresenting it (`us001-rework-reverified`)
- [x] Independent entry: Story implemented and verified without BRD, requirement or Design (Codex, `us002-codex-standalone`)
- [x] Full suite under Python 3.11.16: **390 passed** with `SDLC_TEST_INSTALL=1` (388 passed + 2 opt-in skipped by default; also green on 3.14)
- [ ] `docs/SDLC-M4-EVIDENCE.md` reviewed by a human
- [ ] **M4 approved by a human**

**Not exercised live:** RES by a live agent (template/CLI tests only). Deviations and observed issues: evidence §8 and §11.

**Exit criterion:** A story can go from Ready to Verified through the R2 Skills on a fixture project with accurate `delivery_status`, valid links and passing `validate`; verification results are traceable to real executions.

## M5 — Publishing & Status (R3)

- [ ] `sdlc-status` structured report (counts, uncovered requirements, outstanding work, validation problems)
- [ ] GitHub adapter specification reviewed
- [ ] `publish-stories` with mandatory preview and explicit confirmation
- [ ] Local Markdown remains authoritative; no automatic sync (verified)
- [ ] Publication tested against a non-production target only

**Exit criterion:** Publication cannot occur without a shown preview and explicit human confirmation; `sdlc-status` output matches the state of a fixture project.

## M6 — End-to-End Validation & Release

- [ ] Full lifecycle walk-through on a fresh repository (init → BRD → PRD → stories → design → plan → implement → test → verify → publish)
- [ ] Multi-agent install/link verified for each supported agent
- [ ] Validation after simulated branch merge with duplicate IDs
- [ ] Confirm no third-party Skill dependency and no UI requirement
- [ ] `pipx` packaging added and verified
- [ ] User documentation and install guide
- [ ] Verify contextual overlap handling through a real Codex session (carried forward from post-M3 hardening): the contextual review is presented separately and unscored after the CLI check, and the revise / relate / create-new decision is put to the human **before** any ID is allocated (ledger unchanged at that point)
- [ ] Human release sign-off

**Exit criterion:** The full walk-through completes on each supported agent with a clean `validate`, documentation is reviewed, and a human signs off the release.
