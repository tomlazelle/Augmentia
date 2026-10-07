---
id: US-001
title: Export overdue tasks
purpose: Let tasklog developers share overdue tasks by exporting them as CSV.
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

As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them.

## Scope

### In Scope
- Export overdue tasks as CSV rows containing each task's title and due date.
- Produce a header-only CSV when there are no overdue tasks.

### Out of Scope
- Behavior not specified in the decided acceptance criteria remains unresolved.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export, **then** each overdue task is one CSV row with title and due date.
2. **Given** no overdue tasks, **when** I export, **then** the CSV has only the header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Are completed tasks exported?

## Edge Cases and Negative Paths

- Empty overdue-task export is covered by acceptance criterion 2.

## Open Questions

- Whether completed tasks are exported.
