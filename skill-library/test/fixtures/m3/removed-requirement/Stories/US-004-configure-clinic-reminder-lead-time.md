---
id: US-004
title: Configure Clinic Reminder Lead Time
purpose: Let a clinic admin control how far ahead of an appointment reminders go out, so timing fits their patients.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R005]
---

# US-004 — Configure Clinic Reminder Lead Time

## References

### Derived From
- [PR-001 — Appointment Reminders for Clinics](../PR/PR-001-appointment-reminders-for-clinics.md)

### Related To
- [US-003 — Send Automatic Appointment Reminder](US-003-send-automatic-appointment-reminder.md)
- [US-006 — Set Reminder Channel Default and Per-Patient Override](US-006-set-reminder-channel-default-and-per-patient-override.md)

### Supporting Artifacts
- None identified.

## Story

As a clinic owner/admin, I want to set how far ahead of an appointment reminders are sent, so that the timing matches my clinic's needs.

## Scope

### In Scope
- Setting the clinic-wide reminder lead time.
- Defaulting the lead time to 24 hours when not otherwise configured.

### Out of Scope
- Sending the reminder itself (US-003).
- Configuring the reminder channel (US-006).
- Per-patient or per-appointment lead-time overrides (not requested; PR-001 describes lead time as clinic-wide only).

## Business Rules

- The default lead time is 24 hours before the appointment when the clinic has not configured a different value.
- The configured lead time applies clinic-wide, to all appointments for that clinic.

## Acceptance Criteria

1. **Given** a clinic that has not configured a lead time, **when** an admin views the reminder settings, **then** the lead time shown is 24 hours.
2. **Given** an admin sets a new lead time value, **when** the admin saves it, **then** subsequent reminder sends for that clinic use the new lead time.
3. **Given** a clinic has a configured lead time, **when** an admin views the reminder settings, **then** the currently configured value is displayed accurately.

## Edge Cases and Negative Paths

- **Given** an admin enters an invalid lead time (e.g., zero, negative, or non-numeric), **when** the admin attempts to save, **then** the system rejects the value and indicates it is invalid.
- **TBD** — Situation: an admin changes the lead time while reminders are already scheduled under the old value; trigger: the change is saved. Outcome not yet decided: whether already-scheduled reminders are recalculated or left as-is is TBD (see Open Questions).

## Open Questions

- Valid range/bounds for the lead time (minimum/maximum hours) — Owner: Unknown.
- Whether changing the lead time affects reminders already scheduled under the previous value — Owner: Unknown.
