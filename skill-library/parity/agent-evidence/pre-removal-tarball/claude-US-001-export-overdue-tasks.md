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
- Exporting tasks that are past their due date to a CSV file, with each overdue task as one row containing its title and due date.
- Producing a CSV with only the header row when there are no overdue tasks.

### Out of Scope
- Exporting tasks that are not overdue.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export, **then** each overdue task is one CSV row with title and due date.
2. **Given** no overdue tasks, **when** I export, **then** the CSV has only the header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks that are past their due date are included in the export, or excluded because they are completed.

## Edge Cases and Negative Paths

- None decided.

## Open Questions

- Whether completed overdue tasks should be exported — Unknown.
