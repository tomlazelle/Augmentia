---
id: RES-001
title: "Python date representation for optional task due dates"
purpose: Record repository and Python 3.11 observations for choosing an optional due-date representation and caller interface for US-001.
status: Draft
created: 2026-10-04
updated: 2026-10-04
---

# RES-001 — Python date representation for optional task due dates

## References

### Derived From
- [US-001 — List overdue tasks](../../Stories/US-001-list-overdue-tasks.md) — serves PR-001-R001, PR-001-R002, PR-001-R003, PR-001-R004.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Question

How should `Task` represent an optional due date and how should callers supply it, given Python 3.11 and standard-library-only constraints, so overdue comparison, ordering, caller-injected `today`, and never-overdue tasks without a due date work?

## Sources

- `Stories/US-001-list-overdue-tasks.md` — acceptance criteria specify `datetime.date` when a due date is supplied, allow no due date, require `overdue_tasks(store, today=...)`, default to the system date, and leave malformed-date reporting unresolved.
- `PR/PR-001-tasklog-overdue-task-listing.md` — requires a date-only due date, earlier-than-today overdue semantics, no-date exclusion, earliest due date first, alphabetical title tie-break, injectable today, and Python 3.11 with no third-party dependencies.
- `tasklog/store.py` — current `Task` is a dataclass with `title` and `done`; `TaskStore.add` takes a title and constructs a task; there is no due-date field or overdue-listing function.
- `tests/test_store.py` — existing tests cover adding, completing, and listing open tasks; none exercise dates.
- Python 3.11.16 standard-library experiment executed in this repository on 2026-10-04 using `datetime.date` and `datetime.datetime`.

## Findings

- The Story explicitly calls for a `datetime.date` value when the due date is present, and no due date otherwise.
- In Python 3.11.16, sorting two `datetime.date` values placed 2026-10-01 before 2026-10-03. Subtracting 2026-10-01 from 2026-10-04 produced `3 days, 0:00:00`.
- In the experiment, `date.today()` returned `2026-10-04` with runtime type `date`.
- Comparing a `date` and an ISO date string with `<` raised `TypeError: '<' not supported between instances of 'datetime.date' and 'str'`.
- Comparing a `date` and a `datetime` with `<` raised `TypeError: can't compare datetime.datetime to datetime.date`.
- `date.fromisoformat('2026-10-01')` returned a `date`. `date.fromisoformat('not-a-date')` raised `ValueError: Invalid isoformat string: 'not-a-date'`.
- These experiments establish observed library behavior only. They do not decide how tasklog should report malformed input.

## Conclusion

The observed standard-library behavior and US-001 support storing a supplied due date as `datetime.date | None` and having callers supply a `date` object. Dates can be ordered directly, and the system default can be obtained as a `date`. ISO strings and datetimes do not compare directly with dates in the observed runtime. Whether tasklog should parse strings, reject malformed values, or handle them another way remains unresolved by this research and remains the Story's TBD.
