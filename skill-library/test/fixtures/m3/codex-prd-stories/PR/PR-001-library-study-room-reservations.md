---
id: PR-001
title: Library Study Room Reservations
purpose: Define the first release of a mobile app for library members to browse, reserve and cancel study rooms at one branch.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# PR-001 — Library Study Room Reservations

## References

### Derived From

- None identified.

### Related To

- None identified.

### Supporting Artifacts

- None identified.

## Product Summary

A mobile app that lets library members browse available study-room slots, reserve a room and cancel a reservation at one branch. Today, members sign a paper sheet at the desk; double bookings and no-shows are the reported problems. This standalone PRD records decisions from the product interview; no BRD is required or planned.

The first release prevents conflicting reservations. How it should address no-shows remains an open question.

## Target Users and Needs

| User | Needs and goals |
|---|---|
| All library members at the initial branch | Find available study-room slots, receive immediate booking confirmation without staff approval, and cancel reservations. |

Staff capabilities and permissions remain TBD.

## User Journeys and Use Cases

1. **Browse and reserve** — A member browses available slots, selects a room, date and time slot, and receives immediate confirmation when the booking meets the reservation rules.
2. **Handle a booking conflict** — If members attempt overlapping bookings for the same room, including simultaneously, both bookings cannot be confirmed. The unsuccessful member sees that the slot is unavailable.
3. **Cancel** — A member cancels a reservation subject to cancellation rules still to be decided. A successful cancellation releases the slot for others and frees the member to make another reservation.

## Behavior and Capabilities

- Bookings are confirmed immediately without staff approval when eligible.
- Each booking lasts no more than two hours.
- A member may have at most one active reservation. An active reservation is a future or in-progress booking; a cancelled reservation no longer counts toward this limit.
- Overlapping reservations for the same room cannot both be confirmed, even when submitted simultaneously.
- Cancellation releases the slot and removes the reservation from the member's active reservation count. Cancellation timing and consequences remain TBD.

## Scope

### MVP (In Scope)

- One branch, serving all library members.
- Browse available slots, book a room and cancel a reservation.
- Immediate confirmation, reservation limits and conflict prevention.

### Out of Scope / Later

- Reminders: later.
- Recurring bookings: later.
- Multi-branch support: outside v1; future scope TBD.

## Product Requirements

- **PR-001-R001** — Members can browse available study-room time slots at the initial branch.
- **PR-001-R002** — Members can book a selected room, date and time slot.
- **PR-001-R003** — Eligible bookings are confirmed immediately without staff approval.
- **PR-001-R004** — The app rejects bookings longer than two hours.
- **PR-001-R005** — The app prevents a member from having more than one active reservation, where active means a future or in-progress booking.
- **PR-001-R006** — Members can cancel reservations, subject to cancellation timing and policy rules that remain TBD.
- **PR-001-R007** — Overlapping reservations for the same room cannot both be confirmed, including when booking attempts are simultaneous.
- **PR-001-R008** — A member whose booking fails because of a conflicting reservation sees that the slot is unavailable.
- **PR-001-R009** — A successful cancellation releases the reserved slot for others to book.
- **PR-001-R010** — A successfully cancelled reservation no longer counts as active, freeing the member to make another reservation subject to the booking rules.

## Acceptance Expectations

- A member can browse, select a room, date and slot, and receive confirmation without staff intervention for an eligible booking.
- A booking longer than two hours is rejected; an otherwise eligible two-hour booking is allowed.
- A member with a future reservation cannot create another active reservation. The same restriction applies while the booking is in progress.
- Two overlapping bookings for one room cannot both be confirmed, including simultaneous attempts. The unsuccessful member sees that the slot is unavailable.
- When a permitted cancellation succeeds, the slot becomes available to others and the cancelled reservation no longer prevents the member from booking again.
- Detailed cancellation acceptance cases remain TBD until timing and policy rules are decided.

## Constraints and Dependencies

- Initial release serves one branch through a mobile app.
- Platform coverage (iOS, Android or both): TBD.
- Member identification and membership verification: TBD.
- Source and maintenance of room details, opening hours and bookable slots: TBD.
- Fixed slot lengths versus member-selected duration: TBD, within the agreed two-hour maximum.
- Transition from the paper sheet, including whether paper bookings remain in use: TBD.

## Assumptions and Open Questions

### Assumptions

- **Unconfirmed assumption:** Members cancel only their own reservations. Cancellation permissions and staff capabilities remain open; this assumption is not a decided requirement.
- No additional product decisions are assumed.

### Open Questions

- Can members cancel at any time before a booking starts? What happens after the start time, and are there cancellation consequences?
- How do members identify themselves and prove membership?
- Will the paper sheet remain in use alongside the app? If so, how will availability reflect paper bookings?
- Who maintains room details, opening hours and bookable slots? Are slot lengths fixed or selected by members?
- Should v1 address no-shows through check-in, automatic release or another policy, or is this deferred?
- What cancellation permissions and staff capabilities are needed?
- Which mobile platforms must v1 support?
- Will multi-branch support be pursued after v1?
- Owners and resolution dates for these questions: Unknown.

### Material Tradeoffs

- Immediate confirmation requires reliable conflict prevention, including simultaneous booking attempts; the observable conflict rule is agreed.
- Reminders are deferred. Browse, book and cancel alone do not establish a no-show policy, which remains open.
- Continuing paper bookings alongside the app would require a shared way to track availability to prevent conflicting reservations; the transition approach remains open.
