---
id: US-003
title: Handle conflicting room bookings
purpose: Prevent overlapping confirmations and tell unsuccessful members the slot is unavailable.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R007, PR-001-R008]
---

# US-003 — Handle conflicting room bookings

## References

### Derived From

- [PR-001 — Library Study Room Reservations](../PR/PR-001-library-study-room-reservations.md)

### Related To

- None identified.

### Supporting Artifacts

- None identified.

## Story

As a library member, I want conflicting bookings to be prevented and an unavailable slot to be identified, so that I know whether I can reserve the room.

## Scope

### In Scope

- Overlapping booking attempts for the same room, including simultaneous attempts, and the unsuccessful member’s unavailable-slot feedback.

### Out of Scope

- General booking eligibility and confirmation are covered by the booking story; browsing and cancellation belong to their respective stories.

## Business Rules

- Overlapping reservations for the same room cannot both be confirmed, including simultaneous attempts. A member whose booking fails due to a reservation conflict sees that the slot is unavailable.

## Acceptance Criteria

1. Given a confirmed reservation for a room, when another member attempts an overlapping reservation for that room, then both reservations cannot be confirmed and the unsuccessful member sees that the slot is unavailable. (PR-001-R007, PR-001-R008)

2. Given two otherwise eligible members attempting overlapping reservations for the same room simultaneously, when their attempts are processed, then both bookings cannot be confirmed and the member whose booking fails due to the conflict sees that the slot is unavailable. (PR-001-R007, PR-001-R008)

## Edge Cases and Negative Paths

- Simultaneous attempts must preserve the same no-overlapping-confirmations rule as sequential attempts.
- Partial overlap is still overlap and is covered by the conflict rule.
- Bookings whose end and start times meet exactly: boundary rules are TBD.
- Selection followed by a conflicting reservation before submission is subject to the same conflict rule; automatic refresh and alternative-slot suggestions are TBD.

## Open Questions

- TBD: exact time-boundary conventions for adjacent bookings.
- TBD: selection of the successful attempt during simultaneous conflicts.
- TBD: unavailable-slot wording, refresh and recovery behavior.
- TBD: integration with paper bookings if paper remains in use.
- Owners and resolution dates: Unknown.

## Dependencies / Notes

- PR-001 is the source of decided behavior. Unspecified behavior remains TBD; no additional product decisions are assumed.
- Mobile platform coverage remains TBD in PR-001.
