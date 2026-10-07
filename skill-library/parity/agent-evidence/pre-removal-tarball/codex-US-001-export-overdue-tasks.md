---
id: US-001
title: Export overdue tasks
purpose: Let tasklog developers share overdue tasks as a CSV.
status: Draft
created: 2026-10-07
updated: 2026-10-07
delivery_status: Ready
covers: []
---

# US-001 — Export overdue tasks

## References

### Derived From
- None identified. This is a standalone Story.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Story

As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them.

## Scope

### In Scope
- Export overdue tasks as CSV, with each task represented as a row containing its title and due date.
- Produce a header-only CSV when there are no overdue tasks.

### Out of Scope
- No other export behavior is specified.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export overdue tasks as CSV, **then** the CSV contains one row per overdue task, and each row contains that task's title and due date.
2. **Given** there are no overdue tasks, **when** I export overdue tasks as CSV, **then** the CSV contains only its header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks are exported.

## Edge Cases and Negative Paths

- No additional decided edge cases.

## Open Questions

- Whether completed tasks are exported.
