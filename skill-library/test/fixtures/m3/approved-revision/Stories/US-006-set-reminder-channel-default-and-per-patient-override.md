---
id: US-006
title: Set Reminder Channel Default and Per-Patient Override
purpose: Let a clinic pick its default reminder channel and let staff override it for individual patients who need a different channel.
status: Draft
created: 2026-09-29
updated: 2026-09-29
delivery_status: Not Started
covers: []
---

# US-006 — Set Reminder Channel Default and Per-Patient Override

## References

### Derived From
- None identified.

### Related To
- [PR-001 — Appointment Reminders for Clinics](../PR/PR-001-appointment-reminders-for-clinics.md) (Behavior and Scope sections describe this capability, but it is not yet expressed as a numbered Product Requirement)
- [US-003 — Send Automatic Appointment Reminder](US-003-send-automatic-appointment-reminder.md)
- [US-004 — Configure Clinic Reminder Lead Time](US-004-configure-clinic-reminder-lead-time.md)

### Supporting Artifacts
- None identified.

## Story

As a clinic owner/admin, I want to set my clinic's default reminder channel, and as front-desk staff, I want to override that channel for an individual patient, so that each patient gets reminders through the channel that works for them.

## Scope

### In Scope
- Admin setting the clinic-wide default reminder channel (SMS or email).
- Staff overriding the channel for a specific patient/appointment.
- Resolving which channel applies to a given reminder send (clinic default unless a per-patient override exists).

### Out of Scope
- Actually sending the reminder via the resolved channel (US-003).
- Configuring the reminder lead time (US-004).

## Business Rules

- The reminder channel is one of: SMS or email.
- A per-patient override, when set, takes precedence over the clinic's default channel for that patient's reminders.
- Absent an override, the clinic's default channel applies.

## Acceptance Criteria

1. **Given** a clinic with no default channel configured, **when** an admin sets the default channel to SMS or email, **then** the system stores that as the clinic's default.
2. **Given** a clinic's default channel is set, **when** staff has not set a per-patient override for a given patient, **then** that patient's reminders resolve to the clinic's default channel.
3. **Given** staff sets a channel override for a specific patient, **when** a reminder is resolved for that patient's appointment, **then** it resolves to the overridden channel instead of the clinic default.
4. **Given** staff removes a previously set per-patient override, **when** a reminder is resolved for that patient thereafter, **then** it resolves back to the clinic's default channel.

## Edge Cases and Negative Paths

- **TBD** — Situation: an admin has not yet set any default channel; trigger: the system resolves a channel for a reminder. Outcome not yet decided: the fallback behavior (require a default before go-live, or an implicit default) is TBD (see Open Questions).
- **TBD** — Situation: staff sets an override to a channel for which the patient has no valid contact method (e.g., overrides to SMS but no phone on file); trigger: a reminder is resolved. Outcome not yet decided: the system's behavior is TBD (see Open Questions and PR-001's open failure question).

## Open Questions

- Whether this capability should be formalized as a numbered PR-001 requirement — suggest revisiting with `create-prd`. Owner: Unknown.
- Whether a clinic must configure a default channel before going live, or whether there is a system-wide fallback — Owner: Unknown.
- Behavior when an override targets a channel the patient has no valid contact method for — Owner: Unknown.
