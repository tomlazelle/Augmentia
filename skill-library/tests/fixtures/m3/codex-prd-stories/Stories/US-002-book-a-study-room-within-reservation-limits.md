---
id: US-002
title: Book a study room within reservation limits
purpose: Receive immediate confirmation for an eligible study-room booking.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R002, PR-001-R003, PR-001-R004, PR-001-R005]
---

# US-002 — Book a study room within reservation limits

## References

### Derived From

- [PR-001 — Library Study Room Reservations](../PR/PR-001-library-study-room-reservations.md)

### Related To

- None identified.

### Supporting Artifacts

- None identified.

## Story

As a library member, I want to book a selected room, date and time slot and receive immediate confirmation when eligible, so that I can arrange my study session without staff approval.

## Scope

### In Scope

- Room, date and slot selection; immediate confirmation; the two-hour maximum and one-active-reservation limit.

### Out of Scope

- Availability browsing, room-conflict handling and cancellation are covered by the other stories. Reminders and recurring bookings are deferred.

## Business Rules

- Bookings last no more than two hours. A member may have at most one active reservation; future and in-progress bookings are active. Eligible bookings are confirmed immediately without staff approval.

## Acceptance Criteria

1. Given an eligible member and available slot, when the member selects a room, date and time slot and books it, then the selected booking is confirmed immediately without staff approval. (PR-001-R002, PR-001-R003)

2. Given a requested booking longer than two hours, when the member submits it, then the app rejects the booking. (PR-001-R004)

3. Given an otherwise eligible booking lasting exactly two hours, when the member submits it, then the app permits and immediately confirms it. (PR-001-R003, PR-001-R004)

4. Given a member with a future reservation, when the member attempts another active reservation, then the app prevents the additional active reservation. (PR-001-R005)

5. Given a member with an in-progress reservation, when the member attempts another active reservation, then the app prevents the additional active reservation. (PR-001-R005)

## Edge Cases and Negative Paths

- Exactly two hours is allowed when otherwise eligible; longer than two hours is rejected.
- Both future and in-progress reservations prevent another active reservation.
- Missing or invalid selections, failed requests and repeated submissions: detailed behavior is TBD.

## Open Questions

- TBD: member identification and membership verification.
- TBD: slot lengths, selectable dates and times, and validation beyond the stated duration and active-reservation limits.
- TBD: error messages and recovery for invalid selections, request failures and repeated submissions.
- TBD: no-show policy, including whether v1 has check-in or automatic release.
- Owners and resolution dates: Unknown.

## Dependencies / Notes

- PR-001 is the source of decided behavior. Unspecified behavior remains TBD; no additional product decisions are assumed.
- Mobile platform coverage remains TBD in PR-001.
