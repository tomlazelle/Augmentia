---
id: TEST-001
title: "Overdue task listing test plan"
purpose: Map each decided US-001 acceptance criterion for optional due dates and overdue task listing to an automated test scenario.
status: Draft
created: 2026-10-04
updated: 2026-10-05
---

# TEST-001 — Overdue task listing test plan

## References

### Derived From
- [US-001 — List overdue tasks](../../Stories/US-001-list-overdue-tasks.md) — serves PR-001-R001, PR-001-R002, PR-001-R003, PR-001-R004.

### Related To
- [DES-001 — Optional due date and overdue task listing](../design/DES-001-optional-due-date-and-overdue-task-listing.md)
- [PLAN-001 — Implement optional due dates and overdue task listing](../plans/PLAN-001-implement-optional-due-dates-and-overdue-task-listing.md)

### Supporting Artifacts
- None identified.

## Scope

- Tests US-001 AC-1 through AC-7: optional date-only due dates, overdue inclusion, exclusion of undated/completed/today/future tasks, due-date/title ordering, an injectable reference date, and the system-date default.
- Does not test the malformed-due-date TBD (US-001 Unresolved Acceptance Behavior) — no behavior is decided for it.
- Does not test persistence, reminders, recurring tasks, time zone handling, or a per-task overdue check — all out of scope per PR-001.
- Written against the proposed, not-yet-implemented interface from DES-001/PLAN-001: `Task.due_date: date | None`, `TaskStore.add(title, due_date=None)`, and `overdue_tasks(store, today=None)` exported from `tasklog`.

## Repository Context

### Inspected
- `tasklog/store.py` — current `Task` dataclass has only `title` and `done`; `TaskStore.add(title)` has no due-date parameter; no `overdue_tasks` function exists yet.
- `tasklog/__init__.py` — currently exports only `Task, TaskStore`; `overdue_tasks` is not yet exported.
- `tests/test_store.py` — existing tests: `test_add_and_list_open`, `test_complete_removes_from_open`, `test_complete_unknown_raises`. No date-related tests exist.
- `pyproject.toml` — `requires-python = ">=3.11"`; pytest `testpaths = ["tests"]`.
- `Artifacts/design/DES-001-...md` and `Artifacts/plans/PLAN-001-...md` — proposed interface and behavior this plan tests against.

### Not Inspected or Unavailable
- None. US-001 is not yet implemented, so scenarios below describe the test to write once `due_date` and `overdue_tasks` exist; they cannot be run against the current code.

## Test Scenarios

### TS-1 — Due date is stored when supplied, absent otherwise
- **Criterion:** AC-1 — Given a task, when a due date is provided, then it is represented as a `datetime.date`; when no due date is provided, the task has no due date.
- **Method:** automated
- **Setup:** A `TaskStore`. Add one task with `due_date=date(2026, 10, 1)`. Add a second task with no `due_date` argument.
- **Steps:** Create both tasks via `store.add(...)`; inspect the returned `Task` objects' `due_date` attribute.
- **Expected result:** The first task's `due_date == date(2026, 10, 1)`. The second task's `due_date is None`.
- **Evidence to capture:** `python -m pytest -q` exit code and output for the corresponding test function.

### TS-2 — Open task past due is included
- **Criterion:** AC-2 — Given an open task with a due date before the reference date, when overdue tasks are listed, then that task is included.
- **Method:** automated
- **Setup:** A `TaskStore` with one open task, `due_date=date(2026, 10, 1)`.
- **Steps:** Call `overdue_tasks(store, today=date(2026, 10, 5))`.
- **Expected result:** The task is present in the returned list.
- **Evidence to capture:** `python -m pytest -q` exit code and output.

### TS-3 — Undated and completed tasks are excluded
- **Criterion:** AC-3 — Given a task without a due date or a completed task, when overdue tasks are listed, then that task is excluded even if another task property might otherwise suggest it is overdue.
- **Method:** automated
- **Setup:** A `TaskStore` with: (a) an open task with no due date; (b) a task with `due_date=date(2026, 9, 1)` (past relative to the reference date) marked `done` via `store.complete(...)`.
- **Steps:** Call `overdue_tasks(store, today=date(2026, 10, 5))`.
- **Expected result:** Neither task (a) nor task (b) is present in the returned list.
- **Evidence to capture:** `python -m pytest -q` exit code and output.

### TS-4 — Today and future due dates are excluded
- **Criterion:** AC-4 — Given an open task whose due date is today or in the future, when overdue tasks are listed, then that task is excluded.
- **Method:** automated
- **Setup:** A `TaskStore` with: (a) an open task `due_date=date(2026, 10, 5)` (equal to the reference date); (b) an open task `due_date=date(2026, 10, 6)` (after the reference date).
- **Steps:** Call `overdue_tasks(store, today=date(2026, 10, 5))`.
- **Expected result:** Neither task (a) nor task (b) is present in the returned list.
- **Evidence to capture:** `python -m pytest -q` exit code and output.

### TS-5 — Ordering: earliest due date first, title breaks ties
- **Criterion:** AC-5 — Given multiple overdue open tasks, when `overdue_tasks(store, today=...)` is called, then it returns tasks ordered by earliest due date first, with tasks sharing a due date ordered alphabetically by title.
- **Method:** automated
- **Setup:** A `TaskStore` with open tasks, all due before the reference date: `("Beta", date(2026, 9, 10))`, `("Alpha", date(2026, 9, 10))` (same date, different title), `("Gamma", date(2026, 9, 1))` (earliest date).
- **Steps:** Call `overdue_tasks(store, today=date(2026, 10, 5))`.
- **Expected result:** Returned order is `["Gamma", "Alpha", "Beta"]` — earliest due date first, then alphabetical by title for the tied pair.
- **Evidence to capture:** `python -m pytest -q` exit code and output.

### TS-6 — Caller-injected reference date governs overdue status
- **Criterion:** AC-6 — Given a reference date, when a caller passes it as `today` to `overdue_tasks(store, today=...)`, then overdue status is determined relative to that date.
- **Method:** automated
- **Setup:** A `TaskStore` with one open task, `due_date=date(2026, 10, 10)`.
- **Steps:** Call `overdue_tasks(store, today=date(2026, 10, 5))` (task not yet due); then call `overdue_tasks(store, today=date(2026, 10, 15))` (task now past due) against the same store.
- **Expected result:** The task is absent from the first call's result and present in the second call's result, showing selection follows the injected `today` rather than any fixed value.
- **Evidence to capture:** `python -m pytest -q` exit code and output.

### TS-7 — Default reference date is the system date
- **Criterion:** AC-7 — Given no `today` argument, when `overdue_tasks(store)` is called, then overdue status is determined using the system date.
- **Method:** automated
- **Setup:** A `TaskStore` with one open task due the day before a controlled "current" date, and one open task due the day after it. Use `monkeypatch` to replace the date source `overdue_tasks` resolves internally (e.g. `tasklog.store.date`) with a fixed `date`, so the test is deterministic and not tied to the real calendar day.
- **Steps:** Call `overdue_tasks(store)` with no `today` argument while the date source is patched to the controlled date.
- **Expected result:** The task due the day before the controlled date is included; the task due the day after is excluded — confirming the omitted-argument path resolves to the (patched) system date rather than a stale or fixed default.
- **Evidence to capture:** `python -m pytest -q` exit code and output.

## Failure, Boundary and Regression Cases

- **Boundary — due date exactly one day before the reference date is included.** Setup: open task `due_date = today - 1 day`. Steps: call `overdue_tasks(store, today=...)`. Expected result: task is included (confirms the AC-2/AC-4 boundary is inclusive on the past side and exclusive at `today` itself, consistent with TS-2 and TS-4). Automated.
- **Boundary — empty store returns an empty list.** Setup: a `TaskStore` with no tasks added. Steps: call `overdue_tasks(store, today=...)`. Expected result: returns `[]`. Automated.
- **Regression — existing task-management behavior is unaffected.** Setup: none beyond current fixtures. Steps: run the existing `test_add_and_list_open`, `test_complete_removes_from_open`, and `test_complete_unknown_raises` tests after the `due_date` field and `overdue_tasks` function are added. Expected result: all three continue to pass unchanged, confirming the additive change does not alter title normalization, completion, or `open_tasks` behavior. Automated, via `python -m pytest -q`.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — How should a malformed due date be reported (for example, raised as an exception, and if so which type, versus some other handling)? No test scenario is written for this until the Story decides it.

## Verification Runs

### VR-1 — 2026-10-05T02:37:26Z
- **Story:** US-001
- **Kind:** automated
- **Command:** `python3 -m pytest -v`
- **Exit code:** 0
- **Result:** passed
- **Environment:** Linux-7.0.0-38-generic-x86_64-with-glibc2.43, Python 3.11.16, pytest 9.1.1
- **Observed:** All 12 tests passed: `test_add_and_list_open`, `test_complete_removes_from_open`, `test_complete_unknown_raises` (regression), `test_due_date_stored_when_supplied_absent_otherwise` (TS-1), `test_open_task_past_due_is_included` (TS-2), `test_undated_and_completed_tasks_are_excluded` (TS-3), `test_today_and_future_due_dates_are_excluded` (TS-4), `test_ordering_earliest_due_date_first_title_breaks_ties` (TS-5), `test_injected_reference_date_governs_overdue_status` (TS-6), `test_default_reference_date_is_system_date` (TS-7), `test_due_date_exactly_one_day_before_reference_is_included` (boundary), `test_empty_store_returns_empty_list` (boundary).
- **Criteria:** AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7
- **Performed by:** agent (pytest via Bash)
- **Evidence:** [VR-1-pytest.log](evidence/VR-1-pytest.log)
