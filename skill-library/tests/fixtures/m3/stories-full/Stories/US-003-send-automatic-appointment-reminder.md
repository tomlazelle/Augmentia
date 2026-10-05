---
id: US-003
title: Send Automatic Appointment Reminder
purpose: Let patients receive a timely reminder via SMS or email so they are less likely to miss their appointment.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: [PR-001-R003, PR-001-R004]
---

# US-003 — Send Automatic Appointment Reminder

## References

### Derived From
- [PR-001 — Appointment Reminders for Clinics](../PR/PR-001-appointment-reminders-for-clinics.md)

### Related To
- [US-001 — Import Appointments via CSV](US-001-import-appointments-via-csv.md)
- [US-002 — Manually Enter an Appointment](US-002-manually-enter-an-appointment.md)
- [US-004 — Configure Clinic Reminder Lead Time](US-004-configure-clinic-reminder-lead-time.md)
- [US-006 — Set Reminder Channel Default and Per-Patient Override](US-006-set-reminder-channel-default-and-per-patient-override.md)

### Supporting Artifacts
- None identified.

## Story

As a patient, I want to receive a one-way reminder by SMS or email before my appointment, so that I don't forget to attend.

## Scope

### In Scope
- Sending exactly one reminder per appointment, via SMS or email, at the clinic's configured lead time.
- Choosing SMS or email as the send channel for a given appointment, per the clinic's default channel or per-patient override (channel selection logic itself is owned by US-006).

### Out of Scope
- Two-way patient actions (confirm/cancel/reschedule via reply) — out of scope for the whole product (see PR-001).
- Configuring the lead time (US-004).
- Configuring/overriding which channel is used (US-006) — this Story only sends via whichever channel is selected.
- Tracking/reporting delivery status (US-005).

## Business Rules

- Exactly one reminder is sent per appointment; no patient reply, confirmation, or cancellation handling in MVP.
- The reminder is sent at the clinic's configured lead time before the appointment (default 24 hours; see US-004).

## Acceptance Criteria

1. **Given** an appointment stored in the system with a valid contact method and a resolved channel of SMS, **when** the clinic's configured lead time before the appointment is reached, **then** the system sends exactly one SMS reminder to the patient.
2. **Given** an appointment stored in the system with a valid contact method and a resolved channel of email, **when** the clinic's configured lead time before the appointment is reached, **then** the system sends exactly one email reminder to the patient.
3. **Given** a reminder has already been sent for an appointment, **when** the lead time trigger is evaluated again for that appointment, **then** the system does not send a second reminder.

## Edge Cases and Negative Paths

- **TBD** — Situation: an appointment whose resolved channel is SMS but the patient has no valid phone number; trigger: the lead time is reached. Outcome not yet decided: the system's behavior (skip, alert staff, fall back to email) is TBD (see Open Questions and PR-001's open failure/retry question).
- **TBD** — Situation: an appointment whose resolved channel is email but the patient has no valid email address; trigger: the lead time is reached. Outcome not yet decided: the system's behavior is TBD (same as above).
- **TBD** — Situation: a reminder send attempt fails (e.g., provider error); trigger: this occurs. Outcome not yet decided: retry/alerting behavior is TBD — carried forward from PR-001's open question.
- **TBD** — Situation: an appointment is created or imported after its own reminder lead time has already passed; trigger: the system evaluates it. Outcome not yet decided: the send behavior (send immediately, skip, alert) is TBD.

## Open Questions

- Failure/retry behavior when a send fails or a contact method is missing/invalid — Owner: Unknown (open in PR-001).
- Behavior when an appointment is imported/entered after its reminder lead time has already elapsed — Owner: Unknown.
