---
id: BR-001
title: Appointment Reminders for Small Clinics
purpose: Enable small, independent clinics to automatically send patients appointment reminders, reducing no-shows and the front-desk staff time currently spent phoning patients by hand.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# BR-001 — Appointment Reminders for Small Clinics

## References

### Derived From
- None identified.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Business Context and Problem

Small, independent clinics (mostly single-location) currently rely on front-desk staff manually phoning patients to remind them of upcoming appointments. This is labor-intensive, and the current no-show rate is around 15%. A small company intends to sell a reminder solution to these clinics; clinic owners and front-desk staff are the direct stakeholders, with patients affected as recipients of the reminders.

## Objectives and Desired Outcomes

- Reduce the appointment no-show rate.
- Reduce front-desk staff time spent on manual reminder phone calls.

## Stakeholders

| Stakeholder | Interest or role |
|---|---|
| Clinic owners | Purchase and adopt the solution; care about cost and reduced no-shows |
| Front-desk staff | Use the tool day-to-day to enter/import appointments and send reminders |
| Patients | Receive reminders; not direct purchasers or users of the tool |

## Scope

### In Scope
- Sending appointment reminders to patients via SMS
- Sending appointment reminders to patients via email
- Clinic staff entering or importing appointment data into the system
- Clinic-configurable reminder timing (e.g., lead time before appointment) per clinic

### Out of Scope
- Appointment scheduling itself
- Billing reminders

## Business Requirements

- **BR-001-R001** — The business shall provide a way for clinic staff to send patients appointment reminders via SMS.
- **BR-001-R002** — The business shall provide a way for clinic staff to send patients appointment reminders via email.
- **BR-001-R003** — The business shall provide a way for clinic staff to enter or import appointment data into the system.
- **BR-001-R004** — The business shall ensure patient reminder communications comply with applicable privacy/consent regulations (specific regulations not yet determined).
- **BR-001-R005** — The business shall support a patient consent/opt-out process for receiving reminders, owned by the clinic.
- **BR-001-R006** — The business shall allow clinic staff to configure reminder timing (lead time before the appointment) on a per-clinic basis.
- **BR-001-R007** — The business shall provide patients with a mechanism to opt out of receiving reminders.

## Constraints and Dependencies

- Budget: TBD.
- Timeline: TBD.
- Applicable privacy/data regulations: unknown; must be determined before implementation.
- Source appointment systems vary by clinic (some may have existing scheduling/EHR systems, others may not); specific integrations, if any, are TBD.

## Success Measures

- No-show rate reduction — Target: TBD.
- Front-desk staff time saved on manual reminder calls — Target: TBD.

## Assumptions and Risks

- **Assumption:** Target clinics are mostly single-location, independent practices, not multi-location or enterprise clinic groups.
- **Assumption:** This is a product to be sold to clinics, not an internal tool built for a single clinic.
- **Risk:** Without a determined regulatory scope (e.g., which privacy rules apply), the solution could be built non-compliantly.
- **Risk:** Without a defined patient consent/opt-out process, clinics may send reminders without proper consent. (Partially addressed by BR-001-R005 and BR-001-R007.)

## Open Questions

- What is the target no-show reduction and staff-time-saved metric? Owner: Unknown.
- What is the expected scale (number of target clinics, appointments/day per clinic)? Owner: Unknown.
- Should reminders be one-way notifications only, or support two-way patient actions (confirm/cancel/reschedule)? Owner: Unknown.
- Which specific privacy/data regulations apply, and what do they require? Owner: Unknown.
- How is patient consent/opt-out established, and by whom at the clinic? Owner: Unknown.
- What is the budget and timeline? Owner: Unknown.
- Is integration with existing clinic scheduling/EHR systems required, and if so, which systems? Owner: Unknown.
