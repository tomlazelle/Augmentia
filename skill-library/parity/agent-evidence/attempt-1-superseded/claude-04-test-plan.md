# claude — 04-test-plan

### USER

Use the create-test-plan skill for US-001. There is no source code in this repository yet, so record that the repository was inspected and contains none, and plan the tests as proposals. My answers: unit-level tests for both decided criteria; no performance testing; assumption: tests will be written with the project's future test runner. Do not ask me anything. Create the document in Draft, then update the map and validate.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 66 s)

Created **TEST-001** at `Artifacts/tests/TEST-001-export-overdue-tasks-as-csv.md`, status `Draft`, derived from US-001.

- **Repository inspection:** confirmed no source code or tests exist — only SDLC scaffolding — recorded in the document's Repository Context section.
- **Scenarios:** TS-1 → AC-1, TS-2 → AC-2, both unit-level/automated, proposed (no runner exists yet).
- **No performance testing**, per your answer.
- **Assumption recorded:** tests will be written against the project's future test runner.
- TBD on completed overdue tasks carried into *Unresolved Acceptance Behavior (TBD)*, no scenario written for it.
- `sdlc update-map` and `sdlc validate` ran clean: 0 errors, 0 warnings, 1 notice (pre-existing: US-001 is a standalone Story with no `covers`, unrelated to this document).

Approval is up to you whenever you're ready.

