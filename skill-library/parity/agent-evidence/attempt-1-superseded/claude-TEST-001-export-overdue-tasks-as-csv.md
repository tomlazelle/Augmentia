---
id: TEST-001
title: Export overdue tasks as CSV
purpose: Verify exporting overdue tasks as CSV produces one row per overdue task and a header-only file when none are overdue.
status: Draft
created: 2026-10-07
updated: 2026-10-07
---

# TEST-001 — Export overdue tasks as CSV

## References

### Derived From
- [US-001 — Export overdue tasks](../../Stories/US-001-export-overdue-tasks.md) (`covers: []` — no requirement IDs identified on the Story)

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Scope

- Covers US-001's decided acceptance criteria AC-1 and AC-2 (CSV export of overdue tasks).
- Does not cover the Story's unresolved TBD (whether completed overdue tasks are included) — see *Unresolved Acceptance Behavior (TBD)*.
- No performance testing (decided).

## Repository Context

### Inspected
- Full repository file tree (`git ls-files`, directory listing) — confirmed there is no source code, no test directories, and no build or test-runner configuration. The repository currently contains only the SDLC documentation scaffolding (`.sdlc/`, `BR/`, `PR/`, `Stories/`, `Artifacts/`, `AGENTS.md`, `CLAUDE.md`, `map.md`).

### Not Inspected or Unavailable
- No code or existing tests exist to inspect.
- No test runner or build tooling is configured; which one will be used is unknown. Scenarios below are proposals, not commands that can be run today.

## Test Scenarios

### TS-1 — Export rows for overdue tasks
- **Criterion:** AC-1 — Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date.
- **Method:** automated (unit-level, proposed)
- **Setup:** A set of tasks including at least one task whose due date is in the past.
- **Steps:** Invoke the export function/unit with the task set and capture the CSV output.
- **Expected result:** The CSV contains one row per overdue task, each with the task's title and due date.
- **Evidence to capture:** Test command, exit code, and the captured CSV output compared against expected rows.

### TS-2 — Header-only CSV when no overdue tasks
- **Criterion:** AC-2 — Given no overdue tasks, when I export, then the CSV has only the header row.
- **Method:** automated (unit-level, proposed)
- **Setup:** A set of tasks with none past their due date (including the case of an empty task set).
- **Steps:** Invoke the export function/unit with that task set and capture the CSV output.
- **Expected result:** The CSV contains only the header row and no data rows.
- **Evidence to capture:** Test command, exit code, and the captured CSV output showing only the header row.

## Failure, Boundary and Regression Cases

- None identified beyond AC-1 and AC-2 — the Story records no additional business rules or edge cases to test.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks that are past their due date are included in the export. (Carried over from US-001; no scenario is written for this until decided.)

## Verification Runs

None recorded.
