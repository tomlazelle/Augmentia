> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-list-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.

**Purpose:** Let a developer retrieve open tasks past their due date, ordered by overdue duration.
**Covers:** `PR-001-R001`, `PR-001-R002`, `PR-001-R003`, `PR-001-R004`
**Derived From:** PR-001

## Story

As a developer embedding tasklog, I want to list overdue tasks, so that I can act on the most overdue open tasks first.

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

