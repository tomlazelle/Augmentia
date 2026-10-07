---
id: TEST-001
title: Export overdue tasks
purpose: Map US-001's decided acceptance criteria for CSV export of overdue tasks to proposed unit-level test scenarios.
status: Draft
created: 2026-10-07
updated: 2026-10-07
---

# TEST-001 — Export overdue tasks

## References

### Derived From
- [US-001 — Export overdue tasks](../../Stories/US-001-export-overdue-tasks.md) — standalone Story (`covers: []`, no requirement IDs)

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Scope

- Tests AC-1 and AC-2 of US-001 (both decided): the CSV export producing one row per overdue task, and the header-only CSV when there are no overdue tasks.
- Does not test the Story's `Unresolved Acceptance Behavior (TBD)` item (whether completed-but-overdue tasks are included) — undecided, so not testable.
- No performance testing is in scope (decision).

## Repository Context

### Inspected
- Repository root (`/tmp/sdlc-agents-EXLvIO/project-claude`) — `git ls-files` and a directory listing confirm only SDLC governance content exists (`BR/`, `PR/`, `Stories/`, `Artifacts/`, `.sdlc/`, `AGENTS.md`, `CLAUDE.md`, `map.md`); there is no application source code, no test suite and no chosen test runner or framework.

### Not Inspected or Unavailable
- No source code, export implementation or test tooling exists yet to inspect — the scenarios below are proposals only, not verifications of existing behavior.
- No test runner is chosen for this project yet. **Assumption:** these scenarios will be written using whatever test runner the project adopts in the future; the scenarios describe intent and expected results, not a concrete test command.

## Test Scenarios

### TS-1 — Overdue tasks produce one CSV row each
- **Criterion:** AC-1 — Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date.
- **Method:** automated (unit-level)
- **Setup:** Construct an in-memory set of tasks including at least one task whose due date is in the past (overdue).
- **Steps:** Invoke the export function/unit under test with this task set and capture its CSV output.
- **Expected result:** The output CSV contains one row per overdue task, each with that task's title and due date; no row is omitted or duplicated.
- **Evidence to capture:** The test command, its exit code, and the assertion output (e.g. the generated CSV content compared against the expected rows).

### TS-2 — No overdue tasks yields header-only CSV
- **Criterion:** AC-2 — Given no overdue tasks, when I export, then the CSV has only the header row.
- **Method:** automated (unit-level)
- **Setup:** Construct an in-memory task set with no overdue tasks (empty set, or only tasks not past their due date).
- **Steps:** Invoke the export function/unit under test with this task set and capture its CSV output.
- **Expected result:** The output CSV contains only the header row and no data rows.
- **Evidence to capture:** The test command, its exit code, and the assertion output (e.g. the generated CSV content compared against the expected header-only output).

## Failure, Boundary and Regression Cases

- None proposed beyond TS-1/TS-2: the Story identifies no other decided edge cases or regression risks (its `Edge Cases and Negative Paths` section states "None identified"), and there is no existing behavior yet that a change could regress.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks that are past their due date are included in or excluded from the overdue export (per the Story's open question); no scenario is proposed for this until it is decided.

## Verification Runs

None recorded.
