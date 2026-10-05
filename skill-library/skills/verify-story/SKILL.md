---
name: verify-story
description: Verify an Implemented Story against its acceptance criteria by running the real tests and checks, recording each run (command, environment, timestamp, exit code, observed result, evidence log; manual checks with who performed them) in the Story's Test Plan Verification Runs, and setting delivery_status Verified only when every decided criterion has a current passed run. The only Skill that sets Verified. Use when the user asks to verify, validate or sign off a Story implementation with evidence.
---

# verify-story

Decides from **actual results** whether an `Implemented` Story is `Verified`. Audience: the human who will rely on the result.

Method and rules: `../../shared/technical-conventions.md` (read it, especially §2, §3, §5, §6). CLI: `sdlc` (`../../shared/cli-contract.md`); if it fails with `command not found: sdlc`, tell the user to install the library and stop. Commands run from the project root.

## Workflow

1. **Select and check prerequisites; stop if unmet.** Read the Story **in full** (number its decided acceptance criteria `AC-1…`; note any `### Unresolved Acceptance Behavior (TBD)`), its Implementation Record, and the Test Plan(s) (`sdlc references <US-ID>`; open them).
   - `delivery_status` must be `Implemented` (or `Verified`, for re-verification). Otherwise report what is missing (implementation not done → `implement-story`) and stop without changing state.
   - There must be a Test Plan for the Story. If none exists, offer `create-test-plan` first (or create one in this session with that Skill's rules); do not verify against nothing.
   - If the Story's latest `## Review Record` verdict is `requires-rework` or `blocked`, do not set `Verified` unless a newer `complete` review exists or the user explicitly waives it (record the waiver in the Review Record).
2. **Inspect the current implementation** (repository state, files in the Implementation Record, `git status`/`git diff`). If it changed since the recorded `Ref`, or acceptance criteria changed, say so: earlier evidence may be stale.
3. **Run the checks for real, when authorised and possible.** Confirm the user authorises running the test commands. Execute each scenario's command from the Test Plan (and any others needed for uncovered criteria). For each run capture: the exact command, environment (versions, OS), UTC timestamp (`date -u +%Y-%m-%dT%H:%M:%SZ`), **exit code**, and what was observed. Save long output to a log under `Artifacts/tests/evidence/` and link it relatively. **Manual checks** are recorded only if a person (or you, if you truly did it) performed them: name who and what was observed; if nobody has, record them `not-run`.
4. **Record every run, honestly.** Append `### VR-n — <timestamp>` blocks to the Test Plan's `## Verification Runs` (format in `technical-conventions.md` §5; replace `None recorded.` on the first run; continue numbering; never edit or delete earlier runs). Use exactly `passed`, `failed`, `blocked` (could not run: tool/environment/access missing) or `not-run` (not executed), and list the `AC-n` each run actually demonstrates (a supporting or smoke check that demonstrates none gets `Criteria: none`; never claim criteria a command does not exercise). `Performed by` is `agent (<tool name>)` for runs you executed, never a personal email address. Never write `passed` without an observed zero exit code (automated) or a stated manual observation.
5. **Decide.**
   - Set `delivery_status: Verified` (and `updated` = today) **only if** every numbered decided criterion has a current, `passed` run that is its latest non-superseded result, and no blocking review verdict stands. Otherwise leave it `Implemented`. Never infer success from a plan, code, a review, or an earlier run that is no longer current.
   - If `Verified` and a re-verification fails or an evidence gap appears, demote to `Implemented` and say why.
   - Unresolved TBD behavior is **not** verified and is never marked passed: report it, and set `Verified` for the decided criteria only if the user explicitly accepts that residual (state it in the report).
   - Failures mean rework: report them and suggest `implement-story`. Do not fix code here.
6. **Validate.** Run `sdlc update-map`, then `sdlc validate`. `validate` errors when `Verified` lacks current passed evidence for every criterion; if you set `Verified`, it must report no such error. Report **errors, warnings and coverage notices separately**; fix record-format errors you caused.
7. **Report.** For every criterion: its latest result and the run (`VR-n`) that supports it; list failed, blocked, not-run and unresolved items and the residual risk; state the delivery transition you made (or that none was made) and the validate summary.

## Rules

- **Only this Skill sets `Verified`, and only from recorded actual results.** No agent infers test success.
- Never claim an unrun command passed; never turn `blocked` or `not-run` into `passed`.
- Superseded runs stay in the record but never count as current.
- Never change acceptance criteria to make something pass; never set `status: Approved`; never edit `.sdlc/ledger.md` or a `map.md` generated region by hand.
