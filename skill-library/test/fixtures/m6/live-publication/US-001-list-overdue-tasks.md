---
id: US-001
title: "List overdue tasks"
purpose: "Let a developer retrieve open tasks past their due date, ordered by overdue duration."
status: Approved
delivery_status: Verified
created: 2026-10-04
updated: 2026-10-05
covers:
  - PR-001-R001
  - PR-001-R002
  - PR-001-R003
  - PR-001-R004
---

# US-001 — List overdue tasks

## Story

As a developer embedding tasklog, I want to list overdue tasks, so that I can act on the most overdue open tasks first.

## References

### Derived From
- [PR-001 — tasklog: Overdue Task Listing](../PR/PR-001-tasklog-overdue-task-listing.md)

### Related To
- None identified.

## Acceptance Criteria

1. **Optional due date** — Given a task, when a due date is provided, then it is represented as a `datetime.date`; when no due date is provided, the task has no due date.
2. **Open past due tasks are overdue** — Given an open task with a due date before the reference date, when overdue tasks are listed, then that task is included.
3. **No due date and completed tasks are excluded** — Given a task without a due date or a completed task, when overdue tasks are listed, then that task is excluded even if another task property might otherwise suggest it is overdue.
4. **Today and future dates are excluded** — Given an open task whose due date is today or in the future, when overdue tasks are listed, then that task is excluded.
5. **Most overdue first, title breaks ties** — Given multiple overdue open tasks, when `overdue_tasks(store, today=...)` is called, then it returns tasks ordered by earliest due date first, with tasks sharing a due date ordered alphabetically by title.
6. **Injectable reference date** — Given a reference date, when a caller passes it as `today` to `overdue_tasks(store, today=...)`, then overdue status is determined relative to that date.
7. **Default reference date** — Given no `today` argument, when `overdue_tasks(store)` is called, then overdue status is determined using the system date.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — How a malformed due date should be reported.

## Open Questions

- How should a malformed due date be reported?

## Implementation Record

### IR-1 — 2026-10-04
- **Summary:** Implemented AC-1 through AC-7 following DES-001/PLAN-001: added `Task.due_date: date | None = None`; `TaskStore.add` accepts an optional `due_date` (title-only calls unchanged); added `overdue_tasks(store, today=None)` resolving the default with `date.today()` at call time, filtering to open tasks with a due date earlier than the reference date, sorted by `(due_date, title)`; exported `overdue_tasks` from `tasklog`. Added tests covering TEST-001's TS-1 through TS-7 plus its boundary (one-day-before, empty store) and regression cases. Malformed-due-date behavior (US-001 TBD) was not implemented, per scope.
- **Files changed:** `tasklog/store.py`, `tasklog/__init__.py`, `tests/test_store.py`
- **Ref:** working tree (uncommitted)
- **Tests run:** `python -m pytest -q` → exit 0 — 12 passed

## Review Record

### RR-1 — 2026-10-04
- **Verdict:** complete
- **Scope:** Reviewed the uncommitted working-tree changes against US-001 AC-1 through AC-7, DES-001, PLAN-001, and TEST-001.
- **Findings:** None. The implementation matches the designed optional `date | None` field and add interface, overdue filtering and date/title ordering, call-time system-date default, and package export. The changed tests cover every decided acceptance criterion and include the plan's boundary and regression cases.
- **Unresolved behavior:** Malformed due-date handling remains the Story's TBD and is not treated as a finding because DES-001/PLAN-001 leave it undecided.
- **Basis:** Verified observation from reading the uncommitted diff and current source/tests; no checks were run as part of this review.
- **Review is not verification:** `delivery_status` remains unchanged by this review. Only `verify-story`, using actual recorded test runs, can set `Verified`.

## Publication

### PUB-1 — 2026-10-05
- **Provider:** github
- **Repository:** tomlazelle/UsedForPractice
- **Issue:** #1
- **URL:** https://github.com/tomlazelle/UsedForPractice/issues/1
- **Recorded by:** `sdlc publish-apply` (publication is non-material; local Markdown stays authoritative)
