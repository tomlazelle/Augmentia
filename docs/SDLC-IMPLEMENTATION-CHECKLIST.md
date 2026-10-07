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
- [x] **Human approval of the NEW R2 semantics** (transition table, invalidation rule incl. amendment of the M3 delivery rule, evidence records, validator enforcement, review gating — evidence doc §2)
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
- [x] `docs/SDLC-M4-EVIDENCE.md` reviewed by a human
- [x] **M4 approved by a human**

**Accepted M4 limitations (human-approved; no mechanisms to be added during M4):**
1. RES artifacts have CLI/template coverage but have not been exercised by a live agent. A live RES scenario is carried into M6.
2. Validation verifies evidence structure and currency but does not semantically prove that an executed test exercises the acceptance criterion it references. This is an intentional architectural boundary.
3. Implementer/verifier agent separation is not required. Verification requires actual execution evidence, not a separate agent identity.

Deviations and observed issues: evidence §8 and §11.

**M4 is human-approved. M1 through M4 are approved.**

**Exit criterion:** A story can go from Ready to Verified through the R2 Skills on a fixture project with accurate `delivery_status`, valid links and passing `validate`; verification results are traceable to real executions.

## M5 — Delivery & Reporting (R3)

Evidence: [SDLC-M5-EVIDENCE.md](SDLC-M5-EVIDENCE.md). Handoff: [SDLC-M5-DELIVERY-REPORTING-IMPLEMENTATION.md](SDLC-M5-DELIVERY-REPORTING-IMPLEMENTATION.md). Fixtures and transcripts: `skill-library/tests/fixtures/m5/`. R3 contract: architecture §16 and `skill-library/shared/publishing-conventions.md`.

- [x] R3 contract drafted: `status` command, preview digest / confirmation gate, Publication record, non-material publication, failure table (architecture §16, `publishing-conventions.md`, `cli-contract.md`)
- [x] **Human approval of the NEW R3 semantics** (architecture §16 items marked NEW; evidence doc §2) — approved in review, conditional on the identity correction below
- [x] **Review correction:** publication identity and duplicate prevention scoped by Story + provider + repository (same-repository duplicate blocked; other repository allowed with a full preview and confirmation); regression tests added
- [x] `status` CLI command: read-only; health, inventory (BR/PR/US/DES/PLAN/RES/TEST), five delivery states, traceability, ordered needs-attention list
- [x] `sdlc-status` Skill: derives state from current files, read-only, coverage notices informational, missing optional artifacts not a defect
- [x] Minimal publishing config contract (`publishing: {provider: github, repository: owner/name}`); credential-looking keys rejected by `validate`
- [x] Publication identity documented and implemented as an append-only Markdown `## Publication` section (`PUB-n`); `validate` checks it (`publication-invalid`); non-material (Approved stays Approved)
- [x] `publish-preview`: offline, zero mutation, faithful title/body/labels/known publication/warnings, content `digest`
- [x] `publish-apply`: refuses unless the digest matches a fresh preview of current files; read-only provider preflight; creates exactly the previewed content; records only after provider success; per-Story outcomes
- [x] Narrow GitHub provider boundary (`gh` CLI; no labels/projects/milestones/branches/PRs; credentials never read, stored or printed)
- [x] `publish-stories` Skill: explicit selection, preview shown verbatim, explicit-confirmation rules, no external mutation otherwise, no sync, no Issue updates
- [x] Duplicate prevention scoped by Story + provider + repository: a known publication in the configured repository is shown in preview and skipped, a publication elsewhere does not block; Issues never matched by title; unreadable record blocks
- [x] Failure handling: missing/invalid config, unsupported provider, missing tooling/auth, repository not found, Issues disabled, per-Story failure, partial success, ambiguous provider result, recording failure after success
- [x] Status acceptance tests (§12 of the handoff, 9 items) and publish acceptance tests (§13, 15 items) pass against the stub GitHub boundary (evidence §4)
- [x] Claude Code and Codex adapters discover both Skills (`test_r3_skills_are_discoverable_through_each_adapter`); both executed in real sessions (evidence §5)
- [x] `sdlc-status` run through Claude Code and Codex with an explicit "fix anything stale" bait: report only, repository fingerprint unchanged
- [x] `publish-stories` through Claude Code (preview; ambiguous reply does not publish; explicit confirmation publishes; duplicate skipped; stale confirmation re-previews) and Codex (preview; ambiguous reply does not publish; explicit confirmation publishes), all against a stub `gh`
- [x] `AGENTS.md`/`CLAUDE.md` templates route publishing through `publish-stories` (still create-if-missing on `init`)
- [x] Preserved M1–M4: existing 390 tests unchanged and green
- [x] Full suite under Python 3.11.16: **493 passed** with `SDLC_TEST_INSTALL=1` (491 passed + 2 opt-in skipped by default; also green on 3.14)
- [x] GitHub adapter specification reviewed by a human
- [x] `docs/SDLC-M5-EVIDENCE.md` reviewed by a human
- [x] **M5 approved by a human**

**Not exercised live:** a real GitHub mutation (no safe test repository was designated; all publication used a stub `gh`). Real `gh` 2.46 was used only to confirm the flag and `--json` field names. Codex was not run for the stale-confirmation and duplicate scenarios. Limitations and observed issues: evidence §6–§8.

**Final M5 regression result:** `SDLC_TEST_INSTALL=1` on Python 3.11.16: **493 passed**. The Story + provider + repository publication identity correction is accepted.

**M5 is human-approved. M1 through M5 are approved.** M6 has not begun; it waits for review of the M6 implementation/release handoff. M6 carry-forwards (including one live GitHub publication to a designated test repository) are preserved below.

**Exit criterion:** `sdlc-status` accurately reports a fixture project without mutation; `publish-stories` produces a faithful GitHub preview; external mutation cannot occur without explicit confirmation; confirmed publication uses the confirmed content and reports accurately; duplicates are prevented; local Markdown stays authoritative; the full 3.11 suite passes; both Skills are discoverable; evidence and checklist are current; limitations are recorded.

## M6 — End-to-End Validation & Release

Evidence: [SDLC-M6-EVIDENCE.md](SDLC-M6-EVIDENCE.md). Handoff: [SDLC-M6-RELEASE-VALIDATION-IMPLEMENTATION.md](SDLC-M6-RELEASE-VALIDATION-IMPLEMENTATION.md). Release candidate: `sdlc-skill-library 1.0.0rc1`. **M5 is human-approved; the approved baseline is `SDLC_TEST_INSTALL=1`, Python 3.11.16: 493 passed.**

- [x] M5 human approval recorded
- [x] Package builds successfully (sdist + wheel)
- [x] `pipx` clean installation succeeds
- [x] `sdlc` console entry point works (`sdlc-install-claude-code`, `sdlc-install-codex` too)
- [x] Runtime package data is complete (Skills, shared references, templates, metadata)
- [x] User installation documentation validated from a clean environment (`skill-library/README.md`)
- [x] Claude Code installation/discovery validated from the packaged release
- [x] Codex installation/discovery validated from the packaged release
- [x] Fresh repository initialized successfully; init idempotent; existing project instructions preserved
- [x] BRD → PRD → Story chain exercised by agents
- [x] **Deferred:** real Codex contextual-overlap scenario completed before ID allocation
- [x] Technical artifact flow exercised (refine, design, plan, test plan)
- [x] **Deferred:** live-agent RES scenario completed
- [x] Real implementation produced
- [x] Implementation review completed
- [x] Real verification evidence produced; Story reaches Verified correctly
- [x] `sdlc validate` passes
- [x] `sdlc-status` accurately reports the final state and is read-only
- [x] **Deferred:** live GitHub preview shown, exact explicit human authorization obtained for that preview, one real Issue created: `US-001` → https://github.com/tomlazelle/UsedForPractice/issues/1
- [x] Publication record validated (`PUB-1`, live); same-repository duplicate prevention demonstrated without a second Issue (repo still holds exactly one Issue; `validate` 0 errors)
- [x] Cross-agent release matrix complete (every row new or reused-and-labelled)
- [x] Python 3.11 full suite passes with installation tests enabled — `SDLC_TEST_INSTALL=1`, Python 3.11.16: **532 passed** final (530 before the live-publication evidence tests; M5 baseline 493); default run 524 passed + 8 opt-in skipped; Python 3.14.4: 524 passed + 8 skipped
- [x] Validation after a simulated branch merge with duplicate IDs (original M6 item)
- [x] Confirm no third-party Skill dependency and no UI requirement (original M6 item; PyYAML is the only runtime dependency)
- [x] Documentation walkthrough passes
- [x] `docs/SDLC-M6-EVIDENCE.md` complete; remaining limitations documented
- [x] Release candidate presented for human sign-off (evidence complete; see `SDLC-M6-EVIDENCE.md` §10)
- [x] **Human release sign-off** — M6 approved by the human reviewer; `sdlc-skill-library 1.0.0rc1` approved for release

**Exit criterion:** The full walk-through completes on each supported agent with a clean `validate`, documentation is reviewed, and a human signs off the release.

**M6 is human-approved. M1 through M6 are complete.**

**Release-note item (from the reviewer):** the verified walkthrough Story (`US-001`) still carries one explicitly unresolved acceptance item (how a malformed due date should be reported). It is not a release blocker: the system surfaces it (`status`, `validate` warning `verified-with-unresolved-tbd`, and the published Issue) instead of hiding it, which demonstrates the distinction between structural/verifiable completion and unresolved product behavior.

## M7 — Node.js / TypeScript Migration (post-release)

Plan: [SDLC-M7-NODE-MIGRATION-PLAN.md](SDLC-M7-NODE-MIGRATION-PLAN.md) (approved; decisions in §1a). M1–M6 (Python `sdlc-skill-library` 1.0.0rc1) are the behavioral oracle, tagged `python-1.0.0rc1`.

- [x] Plan approved by the human reviewer (TypeScript, Node ≥ 22, one YAML dependency, npm distribution, `node:test`, version `2.0.0-rc.1`, `@augmentia/sdlc` proposed, MIT licence, Windows out of scope, semantic JSON parity / byte parity elsewhere, no second live Issue)
- [x] **M7.0** — Python baseline tagged `python-1.0.0rc1` on commit `5c63ffc`; the tag's export passes `SDLC_TEST_INSTALL=1` on Python 3.11.16: 532 passed; toolchain recorded (Node v22.22.1, npm 9.2.0)
- [x] **M7.1** — behavioral corpus recorded from the Python test suite (opt-in recorder), replayed 100% against the Python oracle, coverage and condition-level coverage measured, 16/16 sensitivity mutations detected, every uncovered behavior classified, targeted Python-side cases added; report: [SDLC-M7-1-CORPUS-REPORT.md](SDLC-M7-1-CORPUS-REPORT.md)
- [x] **Human gate: M7.1 corpus approved and frozen**; decisions recorded: non-executable `gh` normalized to `provider-unavailable` in Node (PARITY-EXCEPTION-001), argparse-owned text exempt (PARITY-EXCEPTION-002), dead code not ported with a register (`parity/DROPPED.md`); see `skill-library/parity/EXCEPTIONS.md`
- [x] M7.2 Node core (model, frontmatter, markdown, ledger, ids, project, maps, init, allocate-id, retire-id, create-dir, update-map, CLI skeleton): 24 Node tests; 1,351 applicable corpus cases (1,342 exact + 9 exempt) 0 failed; oracle changes 0; report: [SDLC-M7-2-REPORT.md](SDLC-M7-2-REPORT.md)
- [x] M7.3 Maps, query, validate: 34 Node tests; 1,629 applicable corpus cases (1,616 exact + 13 exempt) 0 failed; 54/54 validator codes with contracted severities; overlap-score parity; 26/26 mutations detected; oracle changes 0; report: [SDLC-M7-3-REPORT.md](SDLC-M7-3-REPORT.md)
- [x] M7.4 Technical, status, publishing (digest parity): 91 Node tests; 1,844 applicable corpus cases (1,831 exact + 13 exempt) 0 failed; 100% digest equality (81 corpus runs/29 digests + 26/26 matrix); 14/12 sensitivity matches oracle; provider failure matrix; oracle changes 0; EX-006 proposed; report: [SDLC-M7-4-REPORT.md](SDLC-M7-4-REPORT.md)
- [x] M7.5 Packaging (`npm pack` tarball), installers, docs, Skill text, MIT licence: 146 Node tests; clean-prefix tarball install; adapters; README/Skill text for npm; MIT; report: [SDLC-M7-5-REPORT.md](SDLC-M7-5-REPORT.md)
- [x] M7.6 Parity gate (differential run, both agents), Python removed, evidence: [SDLC-M7-EVIDENCE.md](SDLC-M7-EVIDENCE.md) — 41,783 differential inputs, 100% digest equality, EX-001..007, Claude Code 12/12 and Codex 12/12 from the npm tarball, 151 Node tests, corpus 1,844 (1,831 exact + 13 exempt) 0 failed, 51/51 mutations
- [x] **Human gate: M7 final sign-off (parity, Python removal, release validation)** — approved; PARITY-EXCEPTION-007 approved; EX-001..007 are the approved intentional deviations from `python-1.0.0rc1` (5c63ffc)
- [x] **Human gate: `@augmentia/sdlc` 2.0.0-rc.1 approved as the Node release candidate.** npm registry publication is **not** authorized: it needs separate explicit authorization after copyright ownership and npm package/scope availability are confirmed

