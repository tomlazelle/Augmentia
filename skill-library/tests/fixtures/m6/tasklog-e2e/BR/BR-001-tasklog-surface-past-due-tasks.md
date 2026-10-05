---
id: BR-001
title: "tasklog: Surface Past-Due Tasks"
purpose: Let developers embedding tasklog identify which tasks are past due so none go unnoticed.
status: Draft
created: 2026-10-04
updated: 2026-10-04
---

# BR-001 — tasklog: Surface Past-Due Tasks

## References

### Derived From
- None identified.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Business Context and Problem

The owner currently tracks tasks for personal projects in ad-hoc Python scripts and notebooks. Tasks silently pass their due date without anyone noticing, and the owner typically discovers a task is overdue days after the fact. This happens roughly weekly. The cost is not financial: it is missed commitments and rework caused by acting on a task later than intended.

tasklog is intended as a small, reusable library so this problem does not have to be solved from scratch in every personal script or tool — including tools built by other developers who embed it.

## Objectives and Desired Outcomes

- A developer embedding tasklog can determine which tasks are currently past due, so that no open task stays overdue without being noticed.

## Stakeholders

| Stakeholder | Interest or role |
|---|---|
| Owner (tasklog maintainer) | Decides scope and approves requirements; primary current user of the problem this solves. |
| Developers embedding tasklog | Want a simple, reliable way to find overdue tasks in their own tools. |

## Scope

### In Scope
- Determining and retrieving which tasks are currently overdue.

### Out of Scope
- Reminders or notifications.
- Persistence (storage of tasks between runs).
- Recurring tasks.
- A user interface.

## Business Requirements

- **BR-001-R001** — A developer embedding tasklog can retrieve the set of currently overdue tasks in a single call.

## Constraints and Dependencies

- Must run on Python 3.11 using only the standard library (no third-party dependencies).

## Success Measures

- A developer can obtain the list of overdue tasks via one library call. Target: TBD (no quantitative target given).

## Assumptions and Risks

- **Assumption:** A task is "overdue" when it has a due date earlier than the current time and has not been marked complete.
- **Risk:** If "overdue" is determined inconsistently (e.g., timezone handling), developers may distrust or misuse the result.

## Open Questions

- What shape "due date" and "complete" take for a task (e.g., date vs. datetime, how completion is marked) is not yet decided. This is product/design detail for a future PRD, not this BRD. Owner: Unknown, by: Unknown.
