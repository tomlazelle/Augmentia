### USER

Use the create-prd skill. I want a PRD for the appointment reminder product. Ask me questions before drafting; don't write anything yet.

### AGENT (claude -p, project skills via install/claude_code.py)

I found an existing BRD, **BR-001 — Appointment Reminders for Small Clinics** (Draft), covering this exact product idea: clinics manually phoning patients about appointments, ~15% no-show rate, wanting automated SMS/email reminders with staff-entered/imported appointment data.

It already establishes: primary users are clinic owners and front-desk staff, patients are recipients, and business requirements around SMS reminders, email reminders, appointment data entry/import, privacy/consent compliance, and opt-out.

**First question: should this PRD be derived from BR-001?** If yes, I'll skip re-asking about the underlying business problem/stakeholders and focus on product-level decisions the BRD left open. If no, we can build the PRD independently.

Assuming yes, here's my first round of questions (product-level, building on what BR-001 already left open):

1. **Primary user for MVP** — BR-001 names both clinic owners and front-desk staff. Is front-desk staff the primary day-to-day user we're designing for first, with clinic owners more of a buyer/admin role?
2. **Two-way vs. one-way reminders** — BR-001 left this open: should reminders just notify, or let patients confirm/cancel/reschedule via reply (SMS reply, email link, etc.)?
3. **Reminder timing** — Fixed lead time (e.g., always 24h before) or configurable per clinic/appointment type?
4. **Appointment data entry** — Is manual entry into this product sufficient for MVP, or is import (CSV, existing scheduling/EHR system) required from day one?
5. **Release posture** — Pilot with one clinic, MVP for a small set of clinics, or full launch?

### USER

Yes, derive it from BR-001. 1. Front-desk staff are the primary users; owners are admins/buyers. 2. MVP is one-way only; patient replies come later. 3. Configurable per clinic, default 24 hours before. 4. CSV import plus manual entry; EHR integration is later. 5. MVP for a few pilot clinics. Also: staff must be able to see whether a reminder was delivered. Consent handling: TBD, still unknown. Show me the draft with assumptions and open questions; don't write yet.

### AGENT (claude -p, project skills via install/claude_code.py)

Here's a draft based on what we've covered so far. I haven't run `allocate-id` yet — IDs shown as placeholders (`PR-001-Rxx`) until you confirm and I write the file.

---

## PR-001 — Appointment Reminders for Clinics (Front Desk)

**Derived From:** BR-001 — Appointment Reminders for Small Clinics

### Product Summary
A reminder tool that lets clinic front-desk staff import or enter appointments and automatically send patients SMS/email reminders ahead of their appointment, reducing no-shows and eliminating manual reminder calls.

### Target Users and Needs
| User | Needs and goals |
|---|---|
| Front-desk staff (primary) | Import/enter appointments quickly; trust that reminders go out automatically; see whether each reminder was delivered |
| Clinic owner (admin/buyer) | Configure clinic-wide settings (e.g., reminder lead time); oversee adoption and value (no-show reduction) |
| Patient (recipient, not a system user) | Receive a clear, timely reminder via SMS or email |

### User Journeys and Use Cases
1. **Import appointments** — Staff uploads a CSV of appointments (or enters one manually); the system validates and stores them.
2. **Automatic reminder send** — At the clinic's configured lead time (default 24h before), the system sends each patient a one-way SMS or email reminder.
3. **Delivery check** — Staff looks up an appointment/patient and sees the reminder's delivery status (e.g., sent, delivered, failed).
4. **Clinic configuration** — Owner/admin sets the reminder lead time (and channel?) for the clinic.

### Behavior and Capabilities
- Staff can import appointments via CSV or enter them manually.
- System sends one reminder per appointment via SMS or email (no patient reply/confirm/cancel in MVP).
- Reminder timing is configurable per clinic; defaults to 24 hours before the appointment.
- Staff can view delivery status per reminder (sent/delivered/failed, at minimum).
- Failure behavior (e.g., invalid phone/email, send failure) — **TBD**, open question below.

### Scope

**MVP (In Scope)**
- CSV import + manual entry of appointments
- One-way SMS and email reminders
- Configurable lead time per clinic (default 24h)
- Delivery status visibility for staff
- Pilot rollout to a few clinics

**Out of Scope / Later**
- Two-way patient actions (confirm/cancel/reschedule via reply)
- EHR/scheduling system integration
- Appointment scheduling itself (out of scope per BRD)
- Billing reminders (out of scope per BRD)

### Product Requirements (draft — pending allocation)
- **PR-001-R001** — Staff shall be able to import appointments via CSV.
- **PR-001-R002** — Staff shall be able to manually enter an appointment.
- **PR-001-R003** — The system shall send patients a one-way SMS reminder before their appointment.
- **PR-001-R004** — The system shall send patients a one-way email reminder before their appointment.
- **PR-001-R005** — Clinic admins shall be able to configure the reminder lead time for their clinic, with a default of 24 hours.
- **PR-001-R006** — Staff shall be able to view the delivery status of a reminder sent for an appointment.

### Acceptance Expectations
- A pilot clinic can import a CSV of appointments and have reminders go out automatically at the configured lead time.
- Front-desk staff can find any appointment and see whether its reminder was delivered.
- No patient-facing reply/confirm/cancel capability is expected in MVP — **TBD**: what exact stakeholder check confirms "acceptable"? (e.g., X% of reminders delivered successfully?)

### Constraints and Dependencies
- CSV format/fields: **TBD**
- SMS/email provider(s): **TBD**
- EHR/scheduling integration: deferred, not MVP
- Privacy/consent regulations and patient opt-out mechanics: **TBD** (BR-001 also flags this as unresolved)

### Assumptions and Open Questions
- **Assumption:** Front-desk staff is the primary day-to-day user; clinic owner is an admin/buyer role, not a daily operator.
- **Assumption:** "A few pilot clinics" means a handful of design-partner-style clinics, not a broad launch — **please confirm scale (e.g., 2–5 clinics)?**
- **Open question:** How does patient consent/opt-out work in the product (e.g., opt-out link in SMS/email, staff-managed flag)? Owner: Unknown (also open in BR-001).
- **Open question:** What "delivered" statuses matter to staff (sent/delivered/opened/failed)? Owner: Unknown.
- **Open question:** What happens when a reminder fails to send (retry? staff alert)? Owner: Unknown.
- **Open question:** Is reminder channel (SMS vs. email) chosen per patient, per clinic, or sent via both? Owner: Unknown.
- **Open question:** CSV format and required fields? Owner: Unknown.

---

A few things I still need from you before this is ready to write:
1. Roughly how many pilot clinics, and any target dates?
2. Reminder channel selection — per patient, per clinic default, or always both?
3. Anything on failure/retry behavior for failed sends, or is that fine as an open question for now?

Let me know if the draft direction looks right, and answer what you can on those — then I'll write the file.

### USER

Pilot: 3 clinics, dates TBD. Channel: per-clinic default, staff can override per patient. Failure/retry: TBD, leave it as an open question. Write it.

### AGENT (claude -p, project skills via install/claude_code.py)

Written and validated clean — no errors or warnings, just the expected "uncovered" notices since no Stories exist yet.

- **Path:** `PR/PR-001-appointment-reminders-for-clinics.md`
- **ID:** PR-001, status: **Draft**, derived from BR-001
- **Requirements:** PR-001-R001 through R006 (CSV import, manual entry, SMS reminder, email reminder, configurable lead time, delivery status visibility)
- **Open TBDs carried forward:** consent/opt-out mechanics, delivery status granularity, failure/retry behavior, CSV format/fields, pilot launch dates

Next step would be `create-stories` to turn these requirements into user stories — let me know if you want that now or later. I haven't set status to Approved; that's your call whenever you're ready.

