---
id: PLAN-001
title: "Implement optional due dates and overdue task listing"
purpose: "Provide a checkable implementation sequence for US-001 using the accepted DES-001 interfaces and behavior."
status: Draft
created: 2026-10-04
updated: 2026-10-04
---

# PLAN-001 — Implement optional due dates and overdue task listing

## References

### Derived From
- [US-001 — List overdue tasks](../../Stories/US-001-list-overdue-tasks.md) — serves PR-001-R001, PR-001-R002, PR-001-R003, PR-001-R004.

### Related To
- [DES-001 — Optional due date and overdue task listing](../design/DES-001-optional-due-date-and-overdue-task-listing.md)

### Supporting Artifacts
- [RES-001 — Python date representation for optional task due dates](../research/RES-001-python-date-representation-for-optional-task-due-dates.md)

## Scope

- Deliver US-001 acceptance criteria AC-1 through AC-7: optional date-only due dates, overdue filtering, exclusions, ordering, injectable reference date, and system-date default.
- Malformed due-date reporting remains unresolved as stated in US-001; this Plan does not prescribe behavior for that TBD.
- No persistence, reminders, recurring tasks, time zone handling, or separate per-task overdue query is included.

## Repository Context

### Inspected
- `Stories/US-001-list-overdue-tasks.md` — acceptance criteria and malformed-due-date TBD.
- `PR/PR-001-tasklog-overdue-task-listing.md` — product requirements, Python 3.11 and standard-library constraint.
- `Artifacts/design/DES-001-optional-due-date-and-overdue-task-listing.md` — accepted interface and filtering/sorting design.
- `Artifacts/research/RES-001-python-date-representation-for-optional-task-due-dates.md` — Python date behavior and limits of the malformed-input evidence.
- `tasklog/store.py` — `Task` currently has `title` and `done`; `TaskStore.add(title)` creates tasks, and `open_tasks()` filters completed tasks.
- `tasklog/__init__.py` — currently exports `Task` and `TaskStore`.
- `tests/test_store.py` — existing tests cover add, completion, and open-task behavior; no date tests exist.
- `pyproject.toml` — package requires Python 3.11 or later and configures pytest to use `tests/`.

### Not Inspected or Unavailable
- No additional source or test files were found in the repository inventory. Tests and validation commands listed below are proposed and have not been run as part of planning.

## Approach

Follow DES-001. Add `due_date: datetime.date | None = None` to `Task`; allow `TaskStore.add` to receive an optional `due_date` while preserving title-only calls. Implement `overdue_tasks(store, today=None)` in `tasklog/store.py`, resolve the default with `date.today()` at call time, retain only not-done tasks with a due date earlier than the reference date, and sort by `(due_date, title)`. Export the function from `tasklog` in `tasklog/__init__.py`. Add focused tests in the existing test module for the decided behavior.

## Steps

1. **Add overdue behavior tests** — Files: `tests/test_store.py` (verified: opened). Cover due-date storage and omission, overdue inclusion, exclusion of undated/completed/today/future tasks, due-date/title ordering, an injected `today`, and the default-date path with a controlled date source. Depends on: none. Check: `python -m pytest tests/test_store.py -q` (proposed; run after implementation).
2. **Add the optional due-date model and creation argument** — Files: `tasklog/store.py` (verified: opened). Import `date`, add `Task.due_date: date | None = None`, and pass an optional `due_date` from `TaskStore.add` into the new task without changing existing title normalization or title-only calls. Depends on: step 1. Check: `python -m pytest tests/test_store.py -q` (proposed).
3. **Implement overdue selection and ordering** — Files: `tasklog/store.py` (verified: opened). Add `overdue_tasks(store, today=None)`; resolve omitted `today` at call time; filter to tasks where `done` is false and `due_date` exists and is earlier than the reference date; return tasks ordered by due date ascending, then title ascending. Depends on: step 2. Check: `python -m pytest tests/test_store.py -q` (proposed).
4. **Export the public function and validate the package behavior** — Files: `tasklog/__init__.py` (verified: opened), `tests/test_store.py` (verified: opened). Export `overdue_tasks` from `tasklog` and ensure tests import/call it through the package surface. Depends on: step 3. Check: `python -m pytest -q` (proposed).

## Acceptance-to-Test Mapping

| Acceptance criterion | Test or check | Command |
|---|---|---|
| AC-1: optional `datetime.date` due date | Assert a supplied date is retained and omission yields `None`. | `python -m pytest tests/test_store.py -q` (proposed) |
| AC-2: open task due before reference date is included | Use a fixed reference date and assert an earlier-dated open task appears. | `python -m pytest tests/test_store.py -q` (proposed) |
| AC-3: undated and completed tasks are excluded | Include an undated task and a completed past-due task; assert neither appears. | `python -m pytest tests/test_store.py -q` (proposed) |
| AC-4: today and future dates are excluded | Include tasks due on the reference date and after it; assert neither appears. | `python -m pytest tests/test_store.py -q` (proposed) |
| AC-5: earliest due date first; title breaks ties | Assert ascending due-date order and alphabetical title order for equal dates. | `python -m pytest tests/test_store.py -q` (proposed) |
| AC-6: caller-injected reference date | Call `overdue_tasks(store, today=...)` with a fixed date and assert selection uses it. | `python -m pytest tests/test_store.py -q` (proposed) |
| AC-7: default reference date is the system date | Control or replace the date source in a focused test and assert omitted `today` uses the current system date at call time. | `python -m pytest tests/test_store.py -q` (proposed) |

## Validation Commands

- `python -m pytest -q` — proposed full test suite run after implementation; not run during planning.
- `sdlc update-map` — refresh generated SDLC indexes after authored document changes.
- `sdlc validate` — check document structure, references, generated maps, and traceability after the map update.

## Risks

- The `today` default must be resolved inside the function call so it does not become stale across days; cover the omitted-argument path with a controlled date source.
- Python annotations do not enforce runtime value types. The Story's malformed due-date reporting behavior is unresolved, so do not add parsing, coercion, or new error semantics without a separate decision.

## Open Questions

- **TBD — malformed due-date behavior:** How should a malformed due date be reported? This remains open in US-001; owner and date are Unknown.
