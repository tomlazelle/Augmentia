---
id: US-001
title: Export overdue tasks
purpose: Let tasklog developers share overdue tasks in CSV form.
status: Draft
created: 2026-10-07
updated: 2026-10-07
delivery_status: Not Started
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
- Export overdue tasks to CSV, with each overdue task represented as a row containing its title and due date.
- Produce a header-only CSV when there are no overdue tasks.

### Out of Scope
- No additional export behavior has been specified.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export, **then** each overdue task is one CSV row with its title and due date.
2. **Given** no overdue tasks, **when** I export, **then** the CSV has only the header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Should completed tasks whose due dates are past be included in the export?

## Edge Cases and Negative Paths

- No additional decided edge-case outcomes were provided.

## Open Questions

- Should completed tasks whose due dates are past be included in the export? (TBD)
