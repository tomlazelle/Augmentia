---
id: US-002
title: Manually Enter an Appointment
purpose: Let front-desk staff add a single appointment directly so it can receive a reminder without needing a CSV.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: []
---

# US-002 — Manually Enter an Appointment

## References

### Derived From
- None identified.

### Related To
- [US-001 — Import Appointments via CSV](US-001-import-appointments-via-csv.md)
- [US-003 — Send Automatic Appointment Reminder](US-003-send-automatic-appointment-reminder.md)

### Supporting Artifacts
- None identified.

## Story

As front-desk staff, I want to manually enter a single appointment, so that I can add or correct an appointment without going through a CSV import.

## Scope

### In Scope
- A form/entry point for staff to add one appointment's details.
- Validating the entered appointment before storing it.

### Out of Scope
- Bulk import via CSV (US-001).
- Sending reminders for the entered appointment (US-003).
- Editing or deleting an existing appointment (not addressed by this Story; TBD whether it's in scope of PR-001 at all).

## Business Rules

- A manually entered appointment must include, at minimum, patient name, patient phone or email (at least one contact method), and appointment date-time, consistent with US-001's CSV fields.

## Acceptance Criteria

1. **Given** staff enters a patient name, at least one contact method (phone or email), and an appointment date-time, **when** staff saves the appointment, **then** the system stores it and it becomes eligible for a reminder.
2. **Given** staff omits a required field (patient name, both contact methods, or appointment date-time), **when** staff attempts to save, **then** the system rejects the save and tells staff which field(s) are missing.
3. **Given** an appointment was just saved, **when** staff looks it up, **then** the entered details are shown back correctly.

## Edge Cases and Negative Paths

- **TBD** — Situation: staff enters an appointment date-time in the past; trigger: staff attempts to save. Outcome not yet decided: the system's behavior is TBD (see Open Questions).
- **Given** staff enters an invalid phone number or email format, **when** staff attempts to save, **then** the system rejects the save and indicates the invalid field.

## Open Questions

- Whether editing/deleting an already-entered appointment is in scope of PR-001 — Owner: Unknown.
- Whether appointments with a past date-time are allowed or rejected — Owner: Unknown.
- This Story's originating requirement, PR-001-R002, was retired (manual entry moved out of MVP scope per product decision, 2026-09-29). This Story is kept as standalone/backlog and no longer covers a PR-001 requirement.
