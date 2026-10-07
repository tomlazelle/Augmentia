---
id: TEST-001
title: Export overdue tasks
purpose: Plan proposed unit tests for exporting overdue tasks as CSV.
status: Draft
created: 2026-10-07
updated: 2026-10-07
---

# TEST-001 — Export overdue tasks

## References

### Derived From
- [US-001 — Export overdue tasks](../../Stories/US-001-export-overdue-tasks.md)

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Scope

- Covers the two decided acceptance criteria in US-001: one CSV row per overdue task with title and due date, and a header-only CSV when there are no overdue tasks.
- Does not decide whether overdue completed tasks are included; that behavior remains unresolved in US-001.
- All scenarios below are proposals for unit tests to be implemented with the project's future test runner.

## Repository Context

### Inspected
- Repository file inventory — confirmed the checkout currently contains SDLC configuration, maps and the US-001 Story, with no source code, test files or test-runner configuration.
- `Stories/US-001-export-overdue-tasks.md` — read the Story, its two decided acceptance criteria, scope, TBD and edge-case notes.
- `map.md`, `Artifacts/map.md`, `Stories/map.md` — inspected project and artifact indexes; no test artifacts were indexed before this plan was created.

### Not Inspected or Unavailable
- Source code and existing tests — none are present in the repository.
- Test-runner configuration and executable test command — none are present; test command and framework are therefore unknown.
- Git history — repository has no commits yet.

## Test Scenarios

### TS-1 — Export one row per overdue task
- **Criterion:** AC-1 — Given tasks past their due date, when I export, then each overdue task is one CSV row with its title and due date.
- **Method:** Automated unit test (proposed).
- **Setup:** Provide multiple tasks whose due dates are in the past, with distinct titles and due dates. Test data and the unit under test will be adapted to the future implementation.
- **Steps:** Call the export behavior using the future project's test runner; parse or inspect the returned CSV using the project's chosen CSV handling approach.
- **Expected result:** The CSV represents every overdue task as one row, and each row contains that task's title and due date.
- **Evidence to capture:** Test command, exit code and runner output identifying this unit test and its result.

### TS-2 — Export header only when no tasks are overdue
- **Criterion:** AC-2 — Given no overdue tasks, when I export, then the CSV has only the header row.
- **Method:** Automated unit test (proposed).
- **Setup:** Provide task data with no overdue tasks (including an empty task collection if supported by the future implementation).
- **Steps:** Call the export behavior using the future project's test runner and inspect the produced CSV rows.
- **Expected result:** The CSV contains only its header row and no task rows.
- **Evidence to capture:** Test command, exit code and runner output identifying this unit test and its result.

## Failure, Boundary and Regression Cases

- TS-2 covers the decided empty-result boundary. No additional failure, invalid-input, or regression outcome was specified in US-001, so this plan proposes no expected behavior for those cases.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — Should completed tasks whose due dates are past be included in the export? This question is carried from US-001; no test outcome is proposed until it is decided.

## Verification Runs

None recorded.
