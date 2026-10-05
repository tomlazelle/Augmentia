# M4 Evidence — Technical SDLC (R2)

Review material for the M4 human gate. Nothing here marks M4 complete or approved.

## 1. How the evidence was produced

- **Under test:** the seven R2 Skills (`refine-stories`, `create-design`, `plan-implementation`, `implement-story`, `review-implementation`, `create-test-plan`, `verify-story`), `shared/technical-conventions.md`, the R2 validator rules (`sdlc/technical.py`, `sdlc/validate.py`), and the unchanged R1 CLI contract otherwise.
- **Agent runs:** real headless sessions in throwaway git repositories, Skills installed through the M2 adapters (`install/claude_code.py --scope project`, `install/codex.py --scope project`), `python -m sdlc` from a Python 3.11.16 environment. Claude Code used `claude -p` (`-c` to continue); Codex used `codex exec` / `codex exec resume --last`. The human side of each conversation was scripted by the maintainer; the text under "USER" in each transcript is exactly what was sent.
- **Test subject:** a tiny Python library `textkit` (`truncate` already existed; agents added `slugify` and `word_count`) with a PRD, Stories and existing pytest tests. The code changes, test runs, evidence logs and documents in the fixtures are produced by the agents. Snapshots: `skill-library/tests/fixtures/m4/<scenario>/`; transcripts: `.../m4/transcripts/`.
- **Hand-authored inputs (not agent output):** the initial `textkit` code and tests; PR-001 (`Approved`); US-001 in its deliberately ambiguous starting state; US-002 (standalone, `Ready`). Each run's transcript notes any other setup.
- **Fixture manipulations (disclosed in each transcript):** `us001-failed-verification` — `strip("-")` removed from `slugify` after implementation to simulate a regression; `us001-rework-reverified` — US-001 document `status` set to `Approved` beforehand to show the Approved → In Review reset next to the delivery reset.
- **Hand-corrections to stored agent output (privacy/accuracy, applied after the fact):** the two verification blocks in `us001-chain-verified` and `us001-rework-reverified` originally named the maintainer's personal email in `Performed by`; replaced with `agent (Claude Code, verify-story)`. Their `VR-2` (an import smoke check) originally claimed `AC-1…AC-5`; corrected to `Criteria: none`. Both flaws were found in this run and fixed in the Skill (§8); the fixtures were corrected so they do not misrepresent current rules. `a-design-codex.md` lacks the agent's final message (capture limitation of the time).
- Fixtures are snapshots: re-running an agent produces different wording.

## 2. R2 contract added (needs human approval where marked NEW)

Full text: `docs/SDLC-SKILL-ARCHITECTURE.md` §15 and `skill-library/shared/technical-conventions.md`.

| # | Semantic | Status |
|---|---|---|
| 1 | Document `status` and Story `delivery_status` stay separate | unchanged |
| 2 | **NEW** — transition table: Ready only by the human's explicit declaration; `implement-story` sets In Progress/Implemented (and pause/rework); `verify-story` sets Verified (and demotes to Implemented); unmet prerequisites ⇒ stop and report | **approval needed** |
| 3 | **NEW** — invalidation: material change to a Story after work started ⇒ `Ready`; code rework ⇒ In Progress; existing runs marked `Superseded` additively (never deleted/edited); amends the M3 `create-stories` "never change delivery_status" rule | **approval needed** |
| 4 | **NEW** — evidence records in documents: Story `Implementation Record` (`IR-n`), TEST `Verification Runs` (`VR-n`, result vocabulary `passed`/`failed`/`blocked`/`not-run`, append-only), optional Story `Review Record` (`RV-n`); recording them is non-material | **approval needed** |
| 5 | **NEW** — validator enforcement (justified CLI extension): record schema; `Implemented`/`Verified` need an IR entry; `Verified` needs a current passed run for every numbered criterion (latest non-superseded run per criterion wins; `Criteria: none` proves nothing); TBD on a Verified Story is a warning; `Artifacts/tests/evidence/` ignored by the directory scan | **approval needed** |
| 6 | **NEW** — review gating: reviews are read-only and advisory; only a *latest* `requires-rework`/`blocked` verdict blocks `verify-story` until re-reviewed or explicitly waived (Skill-enforced, not CLI) | **approval needed** |
| 7 | Templates/catalogs for DES, PLAN, TEST (+ optional RES); none is a prerequisite for a Story | new documents |
| 8 | `AGENTS.md`/`CLAUDE.md` templates route technical artifacts and delivery changes to the R2 Skills | small extension |

Only CLI extension: the R2 rows of `validate` (codes and severities in `shared/cli-contract.md`). No new commands. Exit-code semantics unchanged (errors ⇒ 1; warnings and notices ⇒ 0).

## 3. Test results

| Command (in `skill-library/`) | Result |
|---|---|
| `SDLC_TEST_INSTALL=1 <python3.11.16> -m pytest tests -q` | **390 passed** |
| `<python3.11.16> -m pytest tests -q` | 388 passed, 2 skipped (the two opt-in install tests) |
| `python3 -m pytest tests -q` (Python 3.14) | 388 passed, 2 skipped |

The R1 suite (261 passed with `SDLC_TEST_INSTALL=1` at post-M3 hardening) is part of these runs, unchanged and green (scenario 1). The other 129 tests are new: R2 validator rules (`test_technical.py`, 40 cases), technical-Skill static and template checks (`test_skills.py`), CLI-level R2 scenarios and seeded faults (`test_m4_scenarios.py`), and agent-fixture assertions that re-run each recorded pytest in the fixture code (`test_m4_fixtures.py`).

## 4. Acceptance scenarios

| # | Scenario | Evidence |
|---|---|---|
| 1 | R1 regression green on 3.11 incl. install tests | §3 |
| 2 | `refine-stories` improves an ambiguous Story without inventing | `a-refine.md`; fixture `us001-refined-ready` (5 decided Given/When/Then criteria, TBD for accented text in `### Unresolved Acceptance Behavior (TBD)`, `covers` unchanged, no new requirement IDs, agent refused to set `Ready` until the human declared it and accepted the TBD exception); Codex: `v3-codex-refine.md` (stayed Draft/Not Started) |
| 3 | DES/PLAN/TEST allocate unique IDs, link Story + requirement, update maps, validate; RES exercised | fixture `us001-chain-verified` (DES-001, PLAN-001, TEST-001, Derived From → US-001 `— serves PR-001-R001`, Related To chain); RES via `test_technical_templates_instantiate_into_valid_linked_documents` and `test_each_technical_category_has_its_own_monotonic_sequence` (**RES was not produced by a live agent run**: the design run was told to skip it when no real sources exist, and it did) |
| 4 | Story refined/planned/implemented without BRD or mandatory design | `us002-codex-standalone`: `covers: []`, no BR, no Design, no Plan; Codex ran create-test-plan → implement-story → verify-story to `Verified`; also `v4-codex-plan.md` (plan with no design) |
| 5 | Proposals demonstrably inspect the repository | DES/PLAN/TEST list real inspected files; `test_technical_proposals_cite_files_that_were_actually_inspected` checks every cited path exists in the fixture repo and that `Not Inspected` is stated; Codex review cited `textkit/text.py:17` (asserted to be the real `slug = re.sub…` line) |
| 6 | Only `implement-story` sets Implemented; only `verify-story` sets Verified; statuses separate | transcripts show `Implemented` set only by `implement-story` (Ready→In Progress→Implemented) and `Verified` only by `verify-story`; `refine-stories` changed delivery state only for the human's explicit Ready declaration and the invalidation reset; the creating, review and plan Skills never touched it; static checks in `test_only_the_right_skills_may_set_terminal_states` |
| 7 | Ready → In Progress → Implemented → Verified with real code changes and executed verification | §5 timeline; `us001-chain-verified` (`git diff` shows the `slugify` change, pytest `9 passed`, evidence logs, recorded runs); the fixture test re-runs pytest and gets the recorded result |
| 8 | Failed, unrun, unavailable tools and TBD do not produce false Verified | §6 examples; fixtures `us001-failed-verification`, `us001-blocked-not-run`, `us001-tbd-not-accepted`; each fixture test forges `Verified` and shows `validate` rejects it |
| 9 | Rework after verification follows invalidation; prior evidence stays attributable | §7; fixture `us001-rework-reverified` |
| 10 | Review findings reference actual code; review never asserts verification | `a-review-codex.md` (real finding: implementation replaces every non-alphanumeric character while PLAN-001 asked for a narrower rule, cited as `textkit/text.py:17` and `PLAN-001:67`; verdict `complete`; "not verification"); `v1-claude-review.md` (complete, one nit at `textkit/text.py:15-18`); neither edited code |
| 11 | `update-map` no-op; validate zero errors; seeded faults detected | `test_every_fixture_validates_and_maps_are_current` (all 7 fixtures); `test_m4_scenarios.py` seeds a broken link, duplicate TEST ID, stale design map, misplaced PLAN, malformed filename, unknown requirement; the R2 rules are covered in `test_technical.py` (40 cases) |
| 12 | Both adapters discover all new Skills; real-agent executions | §9 matrix: all seven Skills executed by both Claude Code and Codex |

## 5. State-transition evidence (US-001, Claude Code + Codex; `us001-chain-verified`)

| Step | Skill (agent) | `delivery_status` after | Note |
|---|---|---|---|
| 0 | hand-authored | Not Started | one vague criterion, two open questions |
| 1 | refine-stories (Claude) | Not Started | criteria rewritten; agent said "only you can declare it Ready" |
| 2 | refine-stories (Claude) | **Ready** | recorded only after "I now explicitly declare US-001 Ready…" |
| 3 | create-design (Codex), plan-implementation (Claude), create-test-plan (Claude) | Ready | artifacts only; Story state untouched |
| 4 | implement-story (Claude) | In Progress → **Implemented** | code + 6 tests; IR-1: files changed, `pytest` exit 0, `9 passed` |
| 5 | review-implementation (Codex) | Implemented | read-only; verdict `complete`, one minor plan divergence |
| 6 | verify-story (Claude) | **Verified** | VR-1 (`python -m pytest -q -v`, exit 0, `9 passed`, log linked, AC-1…AC-5) + VR-2 (import smoke check) |

Independent entry (Codex, `us002-codex-standalone`): Ready (hand-authored) → create-test-plan → implement-story (In Progress → Implemented; `12 passed`) → verify-story (VR-1 passed, exit 0, `Performed by: agent (Codex exec_command)`) → **Verified**. `covers: []` throughout; validate exits 0 with the `story-no-coverage` notice.

## 6. Actual pass / fail / blocked / not-run verification examples

- **Passed:** `us001-chain-verified` VR-1 and `us002-codex-standalone` VR-1 (real command, exit code 0, observed output, evidence log).
- **Failed:** `us001-failed-verification` (fixture manipulation as noted). Recorded VR-1: `python -m pytest -q`, **exit 1**, `6 passed, 3 failed`, with the exact wrong outputs (`"hello-world-"`, `"-multiple-spaces-"`, `"-"`). The agent kept `delivery_status: Implemented`, stated "Not Verified", noticed that IR-1's claimed "9 passed" no longer matched the working tree, and recommended `implement-story` rework. Re-running pytest on the fixture reproduces `3 failed`.
- **Blocked / not-run:** `us001-blocked-not-run`, under a stated project policy that AC-2 counts only if `frobnicate --check …` passes and AC-4 only if a person confirms it. VR-2: `frobnicate` → **exit 127**, `command not found`, recorded `blocked`; VR-3: manual blog-preview check recorded `not-run` because nobody performed it. Story stayed `Implemented` although pytest passed AC-2 and AC-4 too, because the policy excluded that evidence; the validator agrees (a forged `Verified` yields `verified-criteria-unproven` naming AC-2 and AC-4).
- **TBD not accepted:** `us001-tbd-not-accepted`. After VR-1 passed for AC-1…AC-5, the user said the accented/non-Latin question must not be left open; the agent recorded VR-3 `blocked`, kept `Implemented`, and suggested `refine-stories`. (The prompt for this run stated the non-acceptance; the agent did not choose it.)
- **Tool unavailable:** first attempt of the chain's verification (`a-verify-attempt1-bash-denied.md`): the harness denied Bash entirely; the agent refused to run or infer anything, changed nothing, and asked for permission or pasted output. (No blocked run was recorded because no command could be attempted.)
- **Accepted residual:** in `us001-rework-reverified` the user explicitly accepted the open question; `Verified` was set for the decided criteria only, and `validate` reports `verified-with-unresolved-tbd` as a warning (exit 0).

## 7. Rework after verification (`us001-rework-reverified`)

1. Start: US-001 `Approved` (setup) and `Verified`, VR-1/VR-2 recorded.
2. `refine-stories` adds decided AC-6 (`"C++ Tips"` → `"c-tips"`): document `status` → **In Review**, `delivery_status` → **Ready**, VR-1 and VR-2 marked `- **Superseded:** yes — Story changed 2026-09-29 (added AC-6).` Results, commands and evidence untouched.
3. `implement-story` (rework): Ready → In Progress → **Implemented**, IR-2 (added test only; `10 passed`).
4. `create-test-plan` revises TEST-001 with TS-6 without touching the Verification Runs.
5. `verify-story`: VR-3 (exit 0, `10 passed`, AC-1…AC-6) and VR-4 (`Criteria: none`) → **Verified**. The validator (and the fixture test) accepts it only because VR-3 is current and passed for every criterion; blanking VR-3's AC-6 makes `validate` error with `AC-6 (no current run)`.

The first attempt (`r1-rework-attempt1-runs-left-current.md`) exposed a contract gap: after `refine-stories` reset the Story to Ready, the old runs were still current. The contract now makes the Skill that invalidates (refine-stories, create-stories revision) or starts a new pass (implement-story) mark them superseded; the second attempt shows the fix.

## 8. Defects found by real runs and fixed in this milestone

| Found in | Defect | Fix |
|---|---|---|
| unit tests | YAML `description:` containing `": "` broke front matter parsing in three new Skills | rephrased; `test_frontmatter_is_valid` guards it |
| `a-implement` | Implementation Record said criteria were "verified passing" | rule: "verified" is reserved for `verify-story` |
| `a-verify` | run claimed AC-1…AC-5 for an import smoke check; `Performed by` used a personal email | `Criteria: none` (validator accepts it, proves nothing); `Performed by` = `agent (<tool>)`; never an email; fixture test forbids emails |
| `r1` attempt 1 | old runs stayed current after invalidation | supersede rule in `technical-conventions.md` §3, `refine-stories`, `implement-story` |
| review of test-plan template | no place to record inspected tests | `## Repository Context` added to the TEST template |
| test collection | `pytest` collected the fixtures' own tests | `norecursedirs = ["fixtures", …]` |

## 9. Agent × Skill matrix (every cell is a real session; transcripts in `tests/fixtures/m4/transcripts/`)

| Skill | Claude Code | Codex |
|---|---|---|
| refine-stories | `a-refine` | `v3-codex-refine` |
| create-design | `v2-claude-design` | `a-design-codex` |
| plan-implementation | `a-plan` | `v4-codex-plan` |
| implement-story | `a-implement` (+ `r1-rework`) | `c-us2-codex` |
| review-implementation | `v1-claude-review` | `a-review-codex` |
| create-test-plan | `a-testplan` (+ `r1-rework`) | `c-us2-codex` |
| verify-story | `a-verify`, `f1`, `f2`, `f3`, `r1-rework` | `c-us2-codex` |

`test_each_r2_skill_has_a_real_transcript_for_both_agents` pins this matrix; adapter installation of all 13 Skills is in `test_install.py` for both adapters.

## 10. Representative generated artifacts

- Design: `tests/fixtures/m4/us001-chain-verified/Artifacts/design/DES-001-standard-library-slugify.md` (Codex); Claude variant not kept as a fixture (`v2-claude-design.md`).
- Plan: `…/us001-chain-verified/Artifacts/plans/PLAN-001-implement-slugify-for-us-001.md`
- Test plan and verification log: `…/us001-chain-verified/Artifacts/tests/TEST-001-….md`, logs in `…/tests/evidence/`
- Implementation record and delivered code: `…/us001-chain-verified/Stories/US-001-….md`, `textkit/text.py`, `tests/test_text.py`
- Failed / blocked / superseded evidence: `us001-failed-verification`, `us001-blocked-not-run`, `us001-rework-reverified`
- Standalone Codex chain: `us002-codex-standalone`

## 11. Deviations, limitations and observed issues

- **Contract additions need approval** (§2 items marked NEW), including the validator extension and the amendment to the M3 `create-stories` delivery rule.
- **Live RES not produced** (the agent correctly declined without sources); covered by template and CLI tests only.
- **Prompt steering:** some prompts were scripted to force a behavior to be observable (TBD non-acceptance, the `frobnicate` policy, back-dated approvals); the transcripts show the exact prompts. Single-turn runs skipped the multi-round interview where noted ("no further questions"); adaptive interrogation was demonstrated in M3 and in `a-refine`.
- **Review wording:** the Claude review's table used a "Verified?" column heading while stating "this review is not verification"; Codex's review found a plan divergence the Claude review did not. Reviews are single-agent samples, not calibrated.
- **Verification independence:** the same agent family implemented and verified US-001 in the chain; independence between implementer and verifier is not enforced by the contract.
- **Validator limits:** it cannot know whether a run *really* exercised the listed criteria (a run can over-claim); it checks schema, exit-code consistency and per-criterion currency, not truth. Not detected: code changes after `Verified` when nobody records rework (git ref comparison is a Skill instruction, not a CLI check).
- **Environment:** Python 3.11.16 for the CLI and both agents' shell runs; Docker/Node unused. Two Codex transcripts (`a-design-codex`, `a-review-codex`) were reconstructed from the run output after a capture-script fix; the review's content is unaltered.
