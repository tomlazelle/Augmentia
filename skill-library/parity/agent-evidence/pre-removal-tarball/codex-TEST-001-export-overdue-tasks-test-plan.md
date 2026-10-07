---
id: TEST-001
title: Export overdue tasks test plan
purpose: Propose unit-level tests for exporting overdue tasks as CSV.
status: Draft
created: 2026-10-07
updated: 2026-10-07
---

# TEST-001 — Export overdue tasks test plan

## References

### Derived From
- [US-001 — Export overdue tasks](../../Stories/US-001-export-overdue-tasks.md) — serves the Story's acceptance criteria; no requirement IDs are identified because the Story is standalone.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Scope

- Covers US-001's two decided acceptance criteria: CSV rows for overdue tasks and a header-only CSV when there are no overdue tasks.
- Does not decide whether completed tasks are included; that behavior remains TBD.

## Repository Context

### Inspected
- Repository file inventory — inspected the repository; it contains no application source code or test files, only project/SDLC configuration and Markdown documents.
- `Stories/US-001-export-overdue-tasks.md` — read the complete Story, including criteria, unresolved behavior, and edge cases.
- `map.md`, `Artifacts/map.md`, and `Artifacts/tests/map.md` — inspected the project maps; no existing Test Plans are listed.

### Not Inspected or Unavailable
- Application implementation and existing tests — none are present in the repository.
- Project test-runner configuration and test conventions — none are present; the future test runner is unknown.

## Test Scenarios

### TS-1 — Export rows for overdue tasks
- **Criterion:** AC-1 — Given tasks past their due date, when I export overdue tasks as CSV, then the CSV contains one row per overdue task, and each row contains that task's title and due date.
- **Method:** Automated unit test (proposal)
- **Setup:** Arrange multiple tasks whose due dates are past due. Use distinct titles and due dates so each output row can be associated with its task.
- **Steps:** Invoke the overdue-task CSV export unit under test using the future project test runner. Compare the produced CSV data with the expected header and one row per supplied overdue task.
- **Expected result:** The CSV contains one row per overdue task, and each row contains that task's title and due date.
- **Evidence to capture:** Future test-runner command, exit code, and test output/log showing the assertion result.

### TS-2 — Export header only when no tasks are overdue
- **Criterion:** AC-2 — Given there are no overdue tasks, when I export overdue tasks as CSV, then the CSV contains only its header row.
- **Method:** Automated unit test (proposal)
- **Setup:** Arrange input data with no overdue tasks.
- **Steps:** Invoke the overdue-task CSV export unit under test using the future project test runner. Inspect the produced CSV rows.
- **Expected result:** The CSV contains only its header row.
- **Evidence to capture:** Future test-runner command, exit code, and test output/log showing the assertion result.

## Failure, Boundary and Regression Cases

- No additional decided failure, boundary, or regression expectations are specified by US-001. The empty overdue-task boundary is covered by TS-2.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — Should completed tasks whose due dates are past be included in the export? No expected result is assigned until this is decided.

## Assumptions and Tradeoffs

- These scenarios are proposals and are not verified against an implementation.
- Tests will be written and run with the project's future test runner; its command and conventions are not yet available.
- Unit-level tests are used for both decided criteria as requested. No performance testing is planned.

## Verification Runs

None recorded.
