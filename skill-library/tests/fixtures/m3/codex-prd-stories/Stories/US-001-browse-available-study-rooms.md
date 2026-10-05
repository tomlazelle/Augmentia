---
id: US-001
title: Browse available study rooms
purpose: Find available study-room time slots at the initial branch.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R001]
---

# US-001 — Browse available study rooms

## References

### Derived From

- [PR-001 — Library Study Room Reservations](../PR/PR-001-library-study-room-reservations.md)

### Related To

- None identified.

### Supporting Artifacts

- None identified.

## Story

As a library member, I want to browse available study-room time slots at my branch, so that I can find a slot to reserve.

## Scope

### In Scope

- Browsing available study-room time slots at the initial branch in the mobile app.

### Out of Scope

- Booking, conflict handling and cancellation belong to the other stories. Multi-branch support is outside v1.

## Business Rules

- The initial release serves all library members at one branch.

## Acceptance Criteria

1. Given available study-room slots at the initial branch, when a member browses availability, then the member can see available study-room time slots at that branch. (PR-001-R001)

## Edge Cases and Negative Paths

- No available slots: display and next steps are TBD.
- Availability cannot be loaded: error and retry behavior are TBD.

## Open Questions

- TBD: source and maintenance of room details, opening hours and bookable slots.
- TBD: fixed slots versus member-selected duration, within the two-hour maximum.
- TBD: continued use of paper bookings and how availability would reflect them.
- TBD: empty-state and loading-failure behavior; mobile platform coverage.
- Owners and resolution dates: Unknown.

## Dependencies / Notes

- PR-001 is the source of decided behavior. Unspecified behavior remains TBD; no additional product decisions are assumed.
- Mobile platform coverage remains TBD in PR-001.
