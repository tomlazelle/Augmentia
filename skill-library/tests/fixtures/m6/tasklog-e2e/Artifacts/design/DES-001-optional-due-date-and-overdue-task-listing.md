---
id: DES-001
title: "Optional due date and overdue task listing"
purpose: Decide the Task due-date representation and caller interface for US-001 overdue filtering and ordering.
status: Draft
created: 2026-10-04
updated: 2026-10-04
---

# DES-001 — Optional due date and overdue task listing

## References

### Derived From
- [US-001 — List overdue tasks](../../Stories/US-001-list-overdue-tasks.md) — serves PR-001-R001, PR-001-R002, PR-001-R003, PR-001-R004.

### Related To
- None identified.

### Supporting Artifacts
- [RES-001 — Python date representation for optional task due dates](../research/RES-001-python-date-representation-for-optional-task-due-dates.md)

## Context and Problem

US-001 needs tasks to optionally carry a calendar due date and needs one listing call to select open tasks earlier than a caller-supplied reference date, defaulting to the system date. Results must order earliest due date first and break ties alphabetically by title. The current `Task` has no due-date field, and the current store has no overdue-listing function.

## Repository Context

### Inspected
- `tasklog/store.py` — `Task` is a dataclass with `title` and `done`; `TaskStore.add(title)` creates and stores a task; `open_tasks()` filters completed tasks.
- `tasklog/__init__.py` — exports `Task` and `TaskStore`.
- `tests/test_store.py` — covers add, complete, and open-task behavior; no date cases exist.
- `Stories/US-001-list-overdue-tasks.md` — source acceptance criteria and malformed-due-date TBD.
- `PR/PR-001-tasklog-overdue-task-listing.md` — date-only behavior, ordering, injection, and runtime constraints.
- Python 3.11.16 — small standard-library comparisons and parsing experiment; observed results are recorded in RES-001.

### Not Inspected or Unavailable
- No uninspected code or test files were identified as relevant to this narrow decision. The SDLC CLI was available through the environment's pipx installation; its `init`, discovery, allocation and overlap commands were run.

## Requirements and Acceptance Traceability

- US-001 AC-1 and AC-3 — represent absent due dates explicitly and exclude them; serves PR-001-R001 and PR-001-R002.
- US-001 AC-2, AC-4 and AC-7 — compare due dates against an injected date or the system date; serves PR-001-R002 and PR-001-R004.
- US-001 AC-5 — order by due date ascending, then title ascending; serves PR-001-R003.
- US-001 AC-6 — expose the reference date as `today`; serves PR-001-R004.

## Options Considered

### Option A — Store a `datetime.date` or `None`
- **Idea:** Add a typed optional date field to `Task`; have callers pass a `date` object through the task creation interface.
- **Advantages:** Matches the Story's explicit type, keeps date-only semantics, permits direct ordering and comparison in the standard library, and represents absence without a sentinel date.
- **Drawbacks:** Callers holding strings or datetimes must convert or choose another value before supplying the due date; runtime behavior for malformed values is not settled.

### Option B — Store ISO date strings
- **Idea:** Store caller-provided ISO strings and parse or compare them when listing.
- **Advantages:** Text representation can be convenient at serialization boundaries.
- **Drawbacks:** Does not match US-001 AC-1. The experiment showed direct ordering comparison between `date` and `str` raises `TypeError`; parsing introduces behavior and malformed-input decisions outside this design.

### Option C — Store `datetime.datetime`
- **Idea:** Store a datetime and derive calendar-date behavior for overdue listing.
- **Advantages:** The standard library provides datetime types.
- **Drawbacks:** Does not match the date-only acceptance criterion. The experiment showed direct `<` comparison between a `date` and `datetime` raises `TypeError`; time-of-day semantics are out of scope.

## Decision

**Proposed, not yet decided:** represent `Task.due_date` as `datetime.date | None`, and have callers provide a `datetime.date` object when setting it. Do not accept or parse ISO strings as the task due-date interface in this design. This follows US-001 AC-1 and the observed comparison behavior documented in RES-001. Add the parameter as optional with a `None` default to task creation so existing `TaskStore.add(title)` calls remain valid.

For listing, expose `overdue_tasks(store, today: date | None = None)`. Resolve `today` inside the call: use the supplied date when present and `date.today()` otherwise. Include only tasks with `done is False`, a non-`None` due date, and `due_date < reference_date`. Sort by `(due_date, title)` ascending.

This decision is proposed for human review and does not resolve malformed due-date behavior from the Story.

## Design

### Components and Responsibilities
- `Task` — add an optional `due_date` dataclass field typed as `date | None`, defaulting to `None`.
- `TaskStore.add` — accept an optional due-date argument and pass it into the created `Task`; keep the existing title-only call working.
- `overdue_tasks` — provide the listing function, reference-date defaulting, overdue filtering, and stable explicit due-date/title ordering. Export the function from the package for callers.

### Interfaces and Data Flow

1. A caller creates a task with `store.add(title, due_date=date(...))`, or omits `due_date` for a task without a due date.
2. The caller invokes `overdue_tasks(store, today=date(...))` for a deterministic reference date, or omits `today` to use `date.today()` at call time.
3. The listing filters completed and undated tasks, retains due dates earlier than the reference date, and returns tasks sorted by due date then title.

### Dependencies

- Python 3.11 standard library only; use `datetime.date`.

## Risks

- Python type annotations do not by themselves establish runtime validation. The observed direct comparisons against a string or datetime raise `TypeError`; how tasklog reports malformed due dates remains the Story's TBD and must be decided separately.
- If the default reference date is evaluated at function definition time instead of call time, it can become stale across days. The design therefore resolves the default inside the function call.

## Assumptions

- The Story's explicit date-only contract governs the business-relevant value type.
- Adding an optional argument to `TaskStore.add` is an appropriate caller path because that is the existing task creation API.

## Open Decisions

- **TBD — malformed due-date behavior:** How should a malformed due date be reported? Owner: Unknown; date: Unknown. This remains open exactly as required by US-001.
- Human decision on the proposed design. Owner: project human; date: Unknown.
