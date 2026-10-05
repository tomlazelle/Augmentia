---
name: implement-story
description: Implement a selected Ready Story in the repository — re-read the Story, its covered requirements and any plan or design, inspect the code and tests, get the human's go-ahead, make scoped code changes, run the project's tests, record what was actually changed and observed in an Implementation Record, and move delivery_status Ready → In Progress → Implemented. The only Skill that sets Implemented. Never sets Verified. Use when the user asks to implement, build, code or work on a Story.
---

# implement-story

Turns a `Ready` Story into working code, with an honest record. Audience: the human who owns the Story, and reviewers.

Method and rules: `../../shared/technical-conventions.md` (read it, especially §2 transitions, §3 rework, §5 Implementation Record, §7 repository work). CLI: `sdlc` (`../../shared/cli-contract.md`); if it fails with `command not found: sdlc`, tell the user to install the library and stop. Commands run from the project root.

## Workflow

1. **Select and re-read.** Run `sdlc list --category US`; agree with the user which Story to implement. Read the Story **in full** (acceptance criteria, edge cases, `### Unresolved Acceptance Behavior (TBD)`), the requirement documents in its `covers`, and any Plan/Design/Test Plan linked to it (`sdlc references <US-ID>`; read the artifacts you find).
2. **Check prerequisites; stop if unmet.**
   - `delivery_status` must be `Ready` (start), `In Progress` (resume) or `Implemented`/`Verified` (**rework**, see step 8). If it is `Not Started`, do **not** start and do **not** set `Ready` yourself: explain what is missing (`refine-stories` and the human's declaration) and stop.
   - If decided acceptance criteria are missing, or unresolved TBD behavior would change the code, ask the user rather than guess.
3. **Inspect the repository** before touching it: current state (`git status`, recent `git log` if a repository exists), the files and tests involved, conventions, and how the project runs its tests (README, `pyproject.toml`, `package.json`, `Makefile`, CI config). Note what you cannot inspect.
4. **Get authorization.** State the intended scope (the files you expect to change, the approach, the test command) and ask the user for an explicit go-ahead to modify code. An explicit authorization already given in the conversation counts; do not assume one. Follow the Plan/Design if present; deviations are reported, not silent.
5. **Start.** Set `delivery_status: In Progress` in the Story's front matter and update `updated` (today, `date +%F`). This is not a material change and does not reset an Approved Story to In Review. Before changing code, look for existing `### VR-n` runs of this Story (`sdlc references <US-ID>`, then the TEST documents): add `- **Superseded:** yes — new implementation pass <date>` to each one that is still current (never edit or delete their results or evidence), because the code they tested is about to change.
6. **Implement, scoped.** Change only what the Story, plan and authorization cover; follow the repository's conventions; add or update tests for the decided acceptance criteria. Report side issues instead of fixing them. Do not modify the Story's acceptance criteria.
7. **Run the tests for real.** Execute the project's relevant test command(s). Capture the actual command, exit code and outcome. Never claim a test passed that you did not run, never paraphrase a failure into a pass, and if tests cannot run (missing tool, environment), say so explicitly. If tests fail, keep `In Progress`, report the failure, and fix or ask.
8. **Record and finish.** Append a new entry to the Story's `## Implementation Record` (create the section if absent; never rewrite earlier entries; format in `technical-conventions.md` §5): `Summary`, `Files changed` (from `git diff --name-only`/status or your actual edits — not from memory), `Ref` (commit, or `working tree (uncommitted)`), `Tests run` with observed results (or `None run — <reason>`).
   - Set `delivery_status: Implemented` **only** when the agreed scope is complete, the record is written, and any failing tests were reported honestly. `Implemented` is a claim about implementation, not verification: never set `Verified`, and say that `verify-story` is the next step.
   - **Rework** (the Story was `Implemented` or `Verified` and code must change): after the user confirms, set `delivery_status: In Progress`, and add `- **Superseded:** yes — reworked <date> (IR-n)` to every existing `### VR-n` block for this Story in the TEST documents (find them with `sdlc references <US-ID>`); never delete or edit their results or evidence. Then continue from step 6 and add a new IR entry.
   - If the human pauses or abandons the work, set `Ready` again and say so.
9. **Index and validate.** Run `sdlc update-map`, then `sdlc validate`. Report **errors, warnings and coverage notices separately**; fix errors you caused (a missing or malformed Implementation Record is an error) and re-run.
10. **Report.** State the Story ID and the delivery transition you made; list the files actually changed, the tests actually run with their exact results, deviations from the plan, open TBDs and the validate summary.

## Rules

- **Only this Skill sets `Implemented`; you never set `Verified`, and you never set `Ready`** (that is the human's declaration, recorded by `refine-stories`).
- Never claim completion from generated code alone; never invent a pass; never hide a failing or unrun test.
- Describe your own test runs as *tests run* with the observed result. The word "verified" is reserved for `verify-story`: do not write that acceptance criteria are "verified" or "proven" in the Implementation Record or your report.
- Never set `status: Approved`; document approval is the human's.
- Never edit `.sdlc/ledger.md` or a `map.md` generated region by hand.
- Ask before modifying code; stay within the authorised scope.
