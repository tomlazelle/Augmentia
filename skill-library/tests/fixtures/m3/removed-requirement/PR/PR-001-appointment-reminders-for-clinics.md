---
id: PR-001
title: Appointment Reminders for Clinics
purpose: Let clinic front-desk staff import appointments and automatically send patients SMS/email reminders, reducing no-shows and manual reminder calls.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---


# PR-001 — Appointment Reminders for Clinics

## References

### Derived From
- [BR-001 — Appointment Reminders for Small Clinics](../BR/BR-001-appointment-reminders-for-small-clinics.md)

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Product Summary

A reminder tool that lets clinic front-desk staff import appointments and automatically send patients SMS/email reminders ahead of their appointment, reducing no-shows and eliminating manual reminder calls.

## Target Users and Needs

| User | Needs and goals |
|---|---|
| Front-desk staff (primary) | Import appointments quickly; trust that reminders go out automatically; see whether each reminder was delivered; override the reminder channel for an individual patient when needed |
| Clinic owner (admin/buyer) | Configure clinic-wide settings (reminder lead time, default channel); oversee adoption and value (no-show reduction) |
| Patient (recipient, not a system user) | Receive a clear, timely reminder via SMS or email |

## User Journeys and Use Cases

1. **Import appointments** — Staff uploads a CSV of appointments; the system validates and stores them.
2. **Automatic reminder send** — At the clinic's configured lead time (default 24h before), the system sends each patient a one-way reminder via the clinic's default channel (SMS or email), unless staff overrode the channel for that patient.
3. **Delivery check** — Staff looks up an appointment/patient and sees the reminder's delivery status (e.g., sent, delivered, failed).
4. **Clinic configuration** — Owner/admin sets the reminder lead time and default reminder channel for the clinic.

## Behavior and Capabilities

- Staff can import appointments via CSV.
- System sends one reminder per appointment via SMS or email (no patient reply/confirm/cancel in MVP).
- Reminder timing is configurable per clinic; defaults to 24 hours before the appointment.
- Reminder channel defaults per clinic (SMS or email); staff can override the channel for an individual patient.
- Staff can view delivery status per reminder (sent/delivered/failed, at minimum).
- Failure/retry behavior (e.g., invalid phone/email, send failure) — TBD, see Open Questions.

## Scope

### MVP (In Scope)
- CSV import of appointments
- One-way SMS and email reminders
- Configurable lead time per clinic (default 24h)
- Per-clinic default reminder channel, with per-patient staff override
- Delivery status visibility for staff
- Pilot rollout to 3 clinics

### Out of Scope / Later
- Manual entry of appointments
- Two-way patient actions (confirm/cancel/reschedule via reply)
- EHR/scheduling system integration
- Appointment scheduling itself
- Billing reminders

## Product Requirements

- **PR-001-R001** — Staff shall be able to import appointments via CSV.
- **PR-001-R003** — The system shall send patients a one-way SMS reminder before their appointment.
- **PR-001-R004** — The system shall send patients a one-way email reminder before their appointment.
- **PR-001-R005** — Clinic admins shall be able to configure the reminder lead time for their clinic, with a default of 24 hours.
- **PR-001-R006** — Staff shall be able to view the delivery status of a reminder sent for an appointment.

## Acceptance Expectations

- A pilot clinic can import a CSV of appointments and have reminders go out automatically at the configured lead time, via the clinic's default channel.
- Front-desk staff can find any appointment and see whether its reminder was delivered.
- Staff can override the reminder channel for an individual patient and see that override take effect.
- What exact stakeholder check confirms "acceptable" (e.g., a target delivery success rate) — TBD.

## Constraints and Dependencies

- Pilot scope: 3 clinics; launch dates TBD.
- CSV format/required fields: TBD.
- SMS/email provider(s): TBD.
- EHR/scheduling integration: deferred, not MVP.
- Privacy/consent regulations and patient opt-out mechanics: TBD (also open in BR-001).

## Assumptions and Open Questions

- **Assumption:** Front-desk staff is the primary day-to-day user; clinic owner is an admin/buyer role, not a daily operator.
- **Open question:** How does patient consent/opt-out work in the product (e.g., opt-out link in SMS/email, staff-managed flag)? Owner: Unknown (also open in BR-001).
- **Open question:** What delivery statuses matter to staff (sent/delivered/opened/failed)? Owner: Unknown.
- **Open question:** What happens when a reminder fails to send — retry, staff alert, or both? Owner: Unknown.
- **Open question:** CSV format and required fields? Owner: Unknown.
- **Open question:** Pilot launch dates? Owner: Unknown.
