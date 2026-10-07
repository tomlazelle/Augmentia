---
id: TEST-001
title: Export overdue tasks test plan
purpose: Map the decided acceptance criteria of US-001 to test scenarios for exporting overdue tasks as CSV.
status: Draft
created: 2026-10-07
updated: 2026-10-07
---

# TEST-001 — Export overdue tasks test plan

## References

### Derived From
- [US-001 — Export overdue tasks](../../Stories/US-001-export-overdue-tasks.md) — AC-1, AC-2

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Scope

- Covers US-001's two decided acceptance criteria: exporting overdue tasks as CSV rows (AC-1) and producing a header-only CSV when there are no overdue tasks (AC-2).
- Does not cover the unresolved behavior for completed overdue tasks (see Unresolved Acceptance Behavior below) or performance characteristics of the export, which is explicitly out of scope per the user's decision.

## Repository Context

### Inspected
- Repository root — inspected directly; no application code, test files, build configuration or test runner exist anywhere in the repository outside the SDLC documentation folders (`BR/`, `PR/`, `Stories/`, `Artifacts/`, `.sdlc/`).

### Not Inspected or Unavailable
- No source code, export logic, task model or test runner exist yet to inspect. The scenarios below are proposals written against the Story's acceptance criteria, not against observed code or an existing test framework. Which test runner/framework will be used is unknown; by the user's stated assumption, tests will be written with whatever test runner the project adopts in the future.

## Test Scenarios

### TS-1 — Export rows overdue tasks as CSV
- **Criterion:** AC-1 — Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date.
- **Method:** automated (unit-level)
- **Setup:** A set of task records including at least one task whose due date is before the current date (overdue).
- **Steps:** Invoke the export function/unit under test with the overdue task(s) as input.
- **Expected result:** The resulting CSV contains one row per overdue task, each row containing that task's title and due date.
- **Evidence to capture:** Unit test command, exit code, and test output showing the generated CSV content (or parsed row data) matches the expected title/due-date pairs.

### TS-2 — Export produces header-only CSV when no overdue tasks
- **Criterion:** AC-2 — Given no overdue tasks, when I export, then the CSV has only the header row.
- **Method:** automated (unit-level)
- **Setup:** A set of task records containing no tasks past their due date (empty or none overdue).
- **Steps:** Invoke the export function/unit under test with no overdue tasks as input.
- **Expected result:** The resulting CSV contains only the header row, with no data rows.
- **Evidence to capture:** Unit test command, exit code, and test output showing the generated CSV contains exactly the header row and no additional rows.

## Failure, Boundary and Regression Cases

- None decided — the Story defines no decided failure or boundary behavior beyond AC-1 and AC-2.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks that are past their due date are included in the export, or excluded because they are completed (tracked as an open question on US-001).

## Verification Runs

None recorded.
