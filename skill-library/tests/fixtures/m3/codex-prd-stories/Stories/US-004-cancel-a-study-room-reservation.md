---
id: US-004
title: Cancel a study-room reservation
purpose: Release a cancelled slot and free the member to book again.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R006, PR-001-R009, PR-001-R010]
---

# US-004 — Cancel a study-room reservation

## References

### Derived From

- [PR-001 — Library Study Room Reservations](../PR/PR-001-library-study-room-reservations.md)

### Related To

- None identified.

### Supporting Artifacts

- None identified.

## Story

As a library member, I want to cancel a reservation when cancellation is permitted, so that the slot is released for others and I can book again.

## Scope

### In Scope

- Permitted cancellation and its effects on slot availability and the member’s active reservation count.

### Out of Scope

- Booking and conflict prevention belong to the other stories. Staff capabilities and cancellation permissions remain TBD.

## Business Rules

- Successful cancellation releases the slot for others and removes the reservation from the member’s active reservation count. Another reservation remains subject to booking rules. Cancellation timing and consequences are TBD.

## Acceptance Criteria

1. Given a reservation and a cancellation permitted by the policy once defined, when a member cancels it successfully, then the reservation is cancelled. (PR-001-R006)

2. Given a successful cancellation, when another member views availability and attempts an otherwise eligible booking of the released slot, then the slot is available for booking. (PR-001-R009)

3. Given a successfully cancelled reservation, when that member attempts another otherwise eligible reservation, then the cancelled reservation does not count as active or prevent the new booking. (PR-001-R010)

4. TBD: observable acceptance cases for cancellation before or after the start time, permission checks and cancellation consequences; policy is not yet defined. (PR-001-R006)

## Edge Cases and Negative Paths

- Cancellation before a reservation starts, while it is in progress, or after it ends: permission and consequences are TBD.
- Attempting to cancel another member’s reservation: permissions and response are TBD.
- Repeated cancellation, cancellation failure and concurrent cancellation/booking: detailed behavior is TBD.

## Open Questions

- TBD: cancellation timing, including after the start time, and any consequences.
- TBD: cancellation permissions and staff capabilities. PR-001’s own-reservations-only statement is explicitly an unconfirmed assumption, not an acceptance rule.
- TBD: duplicate, failed and concurrent cancellation behavior; user-facing confirmation and errors.
- Owners and resolution dates: Unknown.

## Dependencies / Notes

- PR-001 is the source of decided behavior. Unspecified behavior remains TBD; no additional product decisions are assumed.
- Mobile platform coverage remains TBD in PR-001.
