# claude — 04-test-plan

### USER

Use the create-test-plan skill for US-001. There is no source code in this repository yet, so record that the repository was inspected and contains none, and plan the tests as proposals. My answers: unit-level tests for both decided criteria; no performance testing; assumption: tests will be written with the project's future test runner. Do not ask me anything. Create the document in Draft, then update the map and validate.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 97 s)

No errors or warnings — only a pre-existing notice (US-001 is standalone with `covers: []`, unrelated to this document).

**Created:** `TEST-001` — Artifacts/tests/TEST-001-export-overdue-tasks.md, status `Draft`.

- **Derived from:** US-001 (standalone Story, no requirement IDs to cite)
- **Scenarios:** TS-1 (AC-1) and TS-2 (AC-2), both proposed as automated unit-level tests, per your decisions
- **Inspected:** confirmed via `git ls-files`/directory listing that the repo contains only SDLC governance docs — no source code, tests, or test runner exist yet
- **Assumption recorded:** tests will use whatever test runner the project adopts in the future
- **Out of scope:** performance testing (per your decision); the Story's TBD item (completed-but-overdue inclusion) stays under *Unresolved Acceptance Behavior*, with no scenario
- **Verification Runs:** left as `None recorded.`
- `update-map` and `validate` both ran clean (0 errors, 0 warnings)

Approval is yours whenever you're ready to move it out of Draft.

