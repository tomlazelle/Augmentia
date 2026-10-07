---
id: US-005
title: View Reminder Delivery Status
purpose: Let front-desk staff confirm whether a patient's reminder actually went out, so they can follow up if it didn't.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R006]
---

# US-005 — View Reminder Delivery Status

## References

### Derived From
- [PR-001 — Appointment Reminders for Clinics](../PR/PR-001-appointment-reminders-for-clinics.md)

### Related To
- [US-003 — Send Automatic Appointment Reminder](US-003-send-automatic-appointment-reminder.md)

### Supporting Artifacts
- None identified.

## Story

As front-desk staff, I want to see whether a reminder for an appointment was delivered, so that I can follow up with the patient if it wasn't.

## Scope

### In Scope
- Displaying a reminder's delivery status when staff looks up an appointment or patient.
- Supporting the statuses: sent, delivered, failed.

### Out of Scope
- Sending the reminder (US-003).
- Retrying a failed reminder or alerting staff proactively (not requested; PR-001 leaves failure/retry behavior open).

## Business Rules

- A reminder's status is one of: sent, delivered, failed.

## Acceptance Criteria

1. **Given** a reminder has been sent for an appointment, **when** staff looks up that appointment, **then** staff sees a status of "sent".
2. **Given** a reminder is confirmed delivered by the provider, **when** staff looks up that appointment, **then** staff sees a status of "delivered".
3. **Given** a reminder failed to send, **when** staff looks up that appointment, **then** staff sees a status of "failed".
4. **Given** an appointment has no reminder yet sent (e.g., lead time not yet reached), **when** staff looks up that appointment, **then** staff sees that no reminder has been sent yet (not one of sent/delivered/failed).

## Edge Cases and Negative Paths

- **Given** the SMS/email provider has not yet reported a delivered/failed outcome for a "sent" reminder, **when** staff looks it up, **then** the status remains "sent" until an outcome is known.
- **Given** staff searches for an appointment that does not exist, **when** they search, **then** the system indicates no matching appointment was found.

## Open Questions

- Whether an "opened" or read-receipt status is needed beyond sent/delivered/failed — Owner: Unknown (open in PR-001, resolved here to sent/delivered/failed for MVP per stakeholder direction).
- How staff search/look up an appointment (by patient name, phone, date) — Owner: Unknown.
