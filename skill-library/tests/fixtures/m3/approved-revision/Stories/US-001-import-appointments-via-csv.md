---
id: US-001
title: Import Appointments via CSV
purpose: Let front-desk staff bulk-load appointments so reminders can be scheduled without manual re-entry.
status: Approved
created: 2026-09-01
updated: 2026-09-01
delivery_status: Not Started
covers: [PR-001-R001]
---

# US-001 — Import Appointments via CSV

## References

### Derived From
- [PR-001 — Appointment Reminders for Clinics](../PR/PR-001-appointment-reminders-for-clinics.md)

### Related To
- [US-002 — Manually Enter an Appointment](US-002-manually-enter-an-appointment.md)
- [US-003 — Send Automatic Appointment Reminder](US-003-send-automatic-appointment-reminder.md)

### Supporting Artifacts
- None identified.

## Story

As front-desk staff, I want to import a CSV of appointments, so that I can load a clinic's appointments in bulk without entering each one by hand.

## Scope

### In Scope
- Uploading a CSV file containing one or more appointments.
- Validating each row and storing valid appointments.
- Reporting which rows succeeded and which failed validation.

### Out of Scope
- Manually entering a single appointment (US-002).
- Sending reminders for imported appointments (US-003).
- Configuring the clinic's reminder lead time or channel (US-004, US-006).

## Business Rules

- A CSV row must include, at minimum: patient name, patient phone or email (at least one contact method), and appointment date-time. Additional required fields are TBD (see Open Questions).

## Acceptance Criteria

1. **Given** a CSV file with valid rows (patient name, phone or email, and appointment date-time present), **when** staff uploads it, **then** the system stores an appointment for each valid row.
2. **Given** a CSV file containing some invalid rows (missing patient name, missing both phone and email, or missing/invalid appointment date-time), **when** staff uploads it, **then** the system stores the valid rows and reports which rows failed and why.
3. **Given** a successful import, **when** staff views the import result, **then** staff can see a count of appointments imported and a count of rows rejected.

## Edge Cases and Negative Paths

- **Given** an empty CSV file, **when** staff uploads it, **then** the system reports that no appointments were imported (no error, no rows).
- **Given** a CSV file with an unsupported format or unreadable encoding, **when** staff uploads it, **then** the system rejects the upload and tells staff it could not be read.
- **TBD** — Situation: a row that duplicates an existing appointment (same patient and appointment date-time); trigger: staff uploads it. Outcome not yet decided: the system's behavior is TBD (see Open Questions).

## Open Questions

- Full required/optional CSV field list beyond patient name, phone-or-email, and appointment date-time — Owner: Unknown.
- Exact CSV format (delimiter, header row requirements, date-time format) — Owner: Unknown.
- Duplicate-row handling on import (reject, skip, overwrite) — Owner: Unknown.
