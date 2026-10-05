# Technical Conventions (R2)

Shared by `refine-stories`, `create-design`, `plan-implementation`, `implement-story`, `review-implementation`, `create-test-plan` and `verify-story`. Read `document-conventions.md`, `reference-conventions.md` and `interview.md` too; this file adds what technical work needs. The CLI (`cli-contract.md`) stays the authority for IDs, maps, links and structural validation; these Skills add conversation and engineering judgement, never a second implementation of those rules.

## 1. Two separate states

- **Document `status`** (`Draft`, `In Review`, `Approved`, `Superseded`) is about human review of the document. Only a human approves.
- **Story `delivery_status`** (`Not Started`, `Ready`, `In Progress`, `Implemented`, `Verified`) is about delivery of the Story.
- They never substitute for each other. Changing one does not change the other, except through the **invalidation rule** (§3).
- **Evidence entries are non-material.** Appending an Implementation Record, Verification Run or Review Record entry, or changing `delivery_status`, does **not** reset an Approved document to In Review; always bump `updated`. Editing requirements, scope, acceptance criteria, `covers`, references or test scenarios **is** material (In Review, per `document-conventions.md`).

## 2. `delivery_status` transitions

| From → To | Who may set it | Prerequisites |
|---|---|---|
| Not Started → Ready | **the human's explicit declaration**, recorded by `refine-stories` (or any Skill the human asks) | Story has verifiable acceptance criteria; `covers` valid or standalone acknowledged; no unresolved TBD that the human hasn't accepted; `validate` reports no errors |
| Ready → In Progress | `implement-story` | Human authorised code changes for this Story |
| In Progress → Implemented | `implement-story` **only** | Work is complete under the agreed scope; an `Implementation Record` entry exists with what actually changed and any tests actually run; failing tests were reported, not hidden |
| Implemented → Verified | `verify-story` **only** | Every decided acceptance criterion has a current, **passed** verification run (§5); no blocking review verdict (§6); nothing invalidated since |
| In Progress → Ready | `implement-story`, when the human pauses or abandons the work | — |
| Implemented → In Progress | `implement-story` (rework) | Human confirms rework; earlier verification runs are superseded (§3) |
| Verified → In Progress | `implement-story` (code rework) | as above |
| Verified → Implemented | `verify-story` | A re-verification failed or an evidence gap was found; report why |
| any → Ready | invalidation (§3) | material change to the Story |

Nothing skips a step: **only `implement-story` sets `Implemented`; only `verify-story` sets `Verified`.** No Skill infers, assumes or copies a passing result. A Skill that finds a transition's prerequisites unmet **stops, states what is missing, and does not change the state.**

## 3. Rework and invalidation (never a silent stale `Verified`)

- **Story changes.** A *material* change to a Story's acceptance criteria, scope or `covers` while `delivery_status` is `In Progress`, `Implemented` or `Verified` sets it back to `Ready`, and the editing Skill tells the user (in addition to any Approved → In Review reset). This is the one permitted automatic `delivery_status` change. The editing Skill also marks every current verification run for that Story `Superseded` (below): the Story it tested no longer exists.
- **Code changes after `Verified` or `Implemented`, or any new implementation pass.** `implement-story` performs the rework transition (§2) and, before changing code, marks every still-current verification run for that Story `Superseded` (below) — including runs left current when the Story was earlier returned to `Ready` — because the code they tested is about to change.
- **Superseding is additive.** Add `- **Superseded:** yes — <reason>, <date>` to each affected `### VR-n` block. Never delete or edit the recorded result, command, timestamp or evidence: old evidence stays attributable to what it actually tested and is simply no longer *current*. The validator ignores superseded runs when deciding whether `Verified` is supported.
- Verifying again means **new** `VR-n` runs (never editing old ones).

## 4. Technical artifacts

| Artifact | ID | Directory | Purpose |
|---|---|---|---|
| Design | `DES-NNN` | `Artifacts/design/` | How to build it; options and trade-offs |
| Implementation Plan | `PLAN-NNN` | `Artifacts/plans/` | Ordered, actionable steps |
| Test Plan (and verification log) | `TEST-NNN` | `Artifacts/tests/` | Scenarios per acceptance criterion; the append-only *Verification Runs* |
| Research (optional) | `RES-NNN` | `Artifacts/research/` | Evidence behind a decision |

- Create the subdirectory on first use with `sdlc create-dir --artifact design|plans|tests|research`. IDs come from `allocate-id`; run the R1 overlap workflow (CLI `find-overlaps`, then the contextual review, then the human's revise/relate/create-new decision) **before** allocating.
- Every technical artifact lists its source Story (or Stories) under `### Derived From` with a valid relative link, and cites the covered requirement IDs (e.g. `— serves PR-001-R003`) so `validate` can check them. Designs and plans link the related artifacts under `### Related To`; a Design or Research doc used as background goes under `### Supporting Artifacts`.
- **Optional means optional.** A Story is actionable without a BRD, PRD, Design, Plan or Research; a Design or Plan is never a prerequisite unless the human or the project says so. A Test Plan is what `verify-story` needs for evidence; if none exists, create one first (`create-test-plan`).

## 5. Evidence formats (parsed by `validate`)

### Implementation Record (in the Story, `implement-story`)

```markdown
## Implementation Record

### IR-1 — 2026-09-29
- **Summary:** what was actually implemented
- **Files changed:** `app/text.py`, `tests/test_text.py`
- **Ref:** commit 3f2a9c1 | working tree (uncommitted) | not a git repository
- **Tests run:** `python -m pytest -q` → exit 0 — 14 passed   (or: None run — <reason>)
```
Append a new `IR-n` per implementation pass; never rewrite an earlier one. `Summary` and `Files changed` are required.

### Verification Runs (in a TEST document, `verify-story`; append-only)

```markdown
## Verification Runs

### VR-1 — 2026-09-29T15:04:05Z
- **Story:** US-001
- **Kind:** automated
- **Result:** passed
- **Criteria:** AC-1, AC-2
- **Command:** `python -m pytest tests/test_text.py -q`
- **Exit code:** 0
- **Environment:** Python 3.11.16, Linux
- **Performed by:** agent (Claude Code)
- **Observed:** 5 passed in 0.03s
- **Evidence:** [log](evidence/US-001-20260929T150405Z.log)
```
- Heading timestamp is ISO UTC from the shell (`date -u +%Y-%m-%dT%H:%M:%SZ`), never invented.
- **`Result` is exactly one of:** `passed`, `failed`, `blocked` (could not run: tool/environment/access missing), `not-run` (deliberately not executed). These are never interchangeable, and only `passed` supports `Verified`.
- `Performed by` is `agent (<tool name>)` for runs the agent executed; a person's name only when that person did a manual check. Do not put personal email addresses in documents.
- `Kind` is `automated` or `manual`. Automated `passed`/`failed` runs need `Command` and an integer `Exit code` (`passed` ⇒ 0, `failed` ⇒ non-zero). Manual runs name who performed them in `Performed by` (a person by the name they gave, or `agent (<tool name>)` if the agent actually did the check; never insert a personal email address) and what was `Observed`. `blocked` and `not-run` runs state the reason in `Observed`.
- `Criteria` lists `AC-n` where *n* is the position of a decided acceptance criterion in the Story's numbered `## Acceptance Criteria` list, and lists **only the criteria that run actually demonstrates**. A supporting or smoke check (for example an import check) demonstrates none: write `Criteria: none`. Criteria in `### Unresolved Acceptance Behavior (TBD)` are never testable and never listed.
- Long output goes to a log under `Artifacts/tests/evidence/` (the CLI ignores that folder); link it relatively.
- Runs are only ever **appended**; corrections are new runs. The latest current (non-superseded) run for each criterion decides.

### Review Record (in the Story, `review-implementation`, only if the human wants it kept)

```markdown
## Review Record

### RV-1 — 2026-09-29
- **Verdict:** complete | requires-rework | blocked
- **Scope:** diff of `app/text.py` vs `HEAD~1`; Story US-001; PLAN-001
- **Findings:** …one bullet per finding (see §6)
```

## 6. Reviews

`review-implementation` is **read-only**: it never edits code, never sets or implies `Verified`, and states plainly "this review is not verification". Findings carry: **severity** (`blocker`, `major`, `minor`, `nit`), **location** (`path:line`), **basis** (*verified observation*: read in the diff or reproduced, versus *potential concern*: inference), the **acceptance criterion or requirement** it relates to, rationale and a suggested next step. Also list missing test coverage and divergences from acceptance criteria, and unresolved questions. Verdict: `complete` (no blocking findings), `requires-rework` (blocker/major findings), or `blocked` (could not review: missing diff, code, or context — say what).

A review is **advisory but gating in one way**: if the *latest* Review Record verdict is `requires-rework` or `blocked`, `verify-story` will not set `Verified` until a newer `complete` review exists or the human explicitly waives the finding (recorded in the Review Record). No review at all never blocks. Human approval remains the human's.

## 7. Working in the repository

- **Inspect before proposing.** Read the actual code, tests, configuration and existing conventions relevant to the Story (search, open files, `git status`/`git log` when a repository exists). Cite paths you actually opened. Technical documents include a *Repository Context* section that lists **Inspected** files/areas and **Not inspected / unavailable** ones.
- **When code or an environment is unavailable** (no repository, missing tool, no access), say so, label every consequence as an assumption, and do not describe files or test results you have not seen.
- **Proposed versus verified.** Anything about code you have not opened is a *proposal*. Say "proposed: likely `app/x.py`" not "`app/x.py` contains…".
- **Focused clarification** follows `interview.md`: recap between rounds, explicit `TBD`, no invented facts, 3–5 questions.
- **Stay in scope.** Implement only what the Story, its plan and the human authorised. Report side findings instead of acting on them.
- **Do not overstate.** Generated code is not "done"; commands you did not run did not pass.
