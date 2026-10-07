---
id: US-001
title: Export overdue tasks
purpose: Let a developer export overdue tasks as CSV so they can share them.
status: Draft
created: 2026-10-07
updated: 2026-10-07
delivery_status: Ready
covers: []
---

# US-001 — Export overdue tasks

## References

### Derived From
- None identified.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Story

As a developer using tasklog, I want to export the overdue tasks as CSV, so that I can share them.

## Scope

### In Scope
- Exporting tasks that are past their due date to a CSV file, one row per overdue task, with title and due date.
- Producing a header-only CSV when there are no overdue tasks.

### Out of Scope
- Whether completed tasks are included in the export (see Unresolved Acceptance Behavior).
- Export of non-overdue, non-completed tasks.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export, **then** each overdue task is one CSV row with title and due date.
2. **Given** no overdue tasks, **when** I export, **then** the CSV has only the header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks that are past their due date are included in the export or excluded.

## Edge Cases and Negative Paths

- None identified.

## Open Questions

- Should completed tasks past their due date be included in the overdue export? — Unknown.
