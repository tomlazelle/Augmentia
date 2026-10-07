---
id: PR-001
title: "tasklog: Overdue Task Listing"
purpose: Let a developer embedding tasklog retrieve open tasks whose due date has passed, ordered most overdue first.
status: Draft
created: 2026-10-04
updated: 2026-10-04
---

# PR-001 — tasklog: Overdue Task Listing

## References

### Derived From
- [BR-001 — tasklog: Surface Past-Due Tasks](../BR/BR-001-tasklog-surface-past-due-tasks.md)

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Product Summary

tasklog is a Python library, for developers who embed it in their own tools, that lets a caller retrieve the set of currently overdue tasks with a single call — so an open task that has passed its due date is never missed.

## Target Users and Needs

| User | Needs and goals |
|---|---|
| Developer embedding tasklog | Retrieve, with one call, the open tasks that are currently past due, in an order that surfaces the most overdue first. |

## User Journeys and Use Cases

1. **List overdue tasks** — A developer holds a collection of tasks, some with a due date and some without, some completed and some open. They call the library's overdue-listing function. It returns only the open tasks whose due date is before today, sorted most overdue first (ties broken alphabetically by title), so the developer can act on the most urgent ones first.

## Behavior and Capabilities

- A task may optionally carry a due date; when present it is a calendar date (no time-of-day component).
- A task is **overdue** when it is open (not completed) and its due date is earlier than today.
- A task with no due date is never overdue.
- A completed task is never overdue, regardless of its due date.
- The library returns the list of currently overdue tasks ordered most overdue first; tasks tied on due date are ordered alphabetically by title.
- "Today" is a reference date the caller can inject; when not supplied it defaults to the system's current date. This makes the overdue determination deterministic and testable.
- Completion is represented by the task's existing `done` flag (`tasklog.store.Task.done`); this PRD does not change how completion is set.

## Scope

### MVP (In Scope)
- Retrieving the list of currently overdue tasks in a single call, ordered most overdue first (ties alphabetical by title).
- An optional, date-only due date on a task.
- An injectable "today" reference date, defaulting to the system date.

### Out of Scope / Later
- Persistence (storage of tasks between runs).
- Reminders or notifications.
- Recurring tasks.
- Time zone handling.
- A per-task "is this task overdue" check as a separate capability (not required for this release; the listing call is the only required capability).

## Product Requirements

- **PR-001-R001** — A task may optionally have a due date, which is a calendar date with no time-of-day component.
- **PR-001-R002** — A task is overdue when it is open (`done` is false) and its due date is earlier than the reference "today" date; a task with no due date, or a completed task, is never overdue.
- **PR-001-R003** — The library provides a single call that returns the currently overdue tasks, ordered most overdue first, with ties on due date broken alphabetically by task title.
- **PR-001-R004** — The reference "today" date used to determine overdue status is injectable by the caller; when not supplied, it defaults to the system's current date.

## Acceptance Expectations

- A developer can call one library function and get back the overdue tasks correctly ordered (most overdue first, ties alphabetical by title), with the result verified by tests covering: a task with no due date, a completed task with a past due date, an open task with a past due date, an open task with a future or today's due date, and tied due dates.
- **TBD** — How should a malformed due date be reported (for example, raised as an exception, and if so which type, versus some other handling)?

## Constraints and Dependencies

- Must run on Python 3.11 using only the standard library (no third-party dependencies).

## Assumptions and Open Questions

- **Open question:** How a malformed due date should be reported. Owner: Unknown, by: Unknown.
