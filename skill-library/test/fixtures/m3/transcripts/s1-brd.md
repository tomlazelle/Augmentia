### USER

Use the create-brd skill. Idea: we need a way for small clinics to send appointment reminders. Ask me your questions; do not write anything yet.

### AGENT (claude -p, project skills via install/claude_code.py)

Good — this is a new BRD with no overlapping documents. Now let's get into it. I'll ask a first batch of questions focused on the problem and outcomes; feel free to say "unknown/TBD" on any.

1. **Who's the driving stakeholder** for this — clinic owners/office managers themselves, or a company building this as a product to sell to clinics? What's the primary pain today (no-shows, staff time on manual calls, missed follow-ups)?
2. **What does success look like?** E.g., reduce no-show rate by X%, reduce staff hours spent on reminder calls, or something else — any target numbers, or TBD?
3. **Scale/context**: roughly how many clinics, how many appointments/day per clinic, and are we talking single-location practices or small multi-location groups?
4. **Reminder channels**: any known requirement/preference (SMS, phone/voice call, email, app push), or is that open?
5. **Any known constraints** already — budget, timeline, regulatory (e.g., HIPAA/PHI handling since this touches patient appointment data), or existing systems (EHR/scheduling software) it needs to work with?

### USER

1. We're a small company selling to independent clinics; the pain is no-shows, about 15%, and front desk staff phoning patients by hand. Stakeholders: clinic owners and front-desk staff (patients are affected too). 2. Success target: TBD. 3. Unknown for now, single-location clinics mostly. 4. SMS and email, both. 5. Privacy rules apply but I don't know which ones; no budget or date decided, TBD. Still don't write files yet.

### AGENT (claude -p, project skills via install/claude_code.py)

Got it. Next round — scope boundaries and a few practical details:

6. **Where does appointment data come from?** Does the clinic have an existing scheduling/EHR system this would need to pull from, or would staff enter appointments manually into this new tool?
7. **Two-way or one-way?** Should patients be able to confirm/cancel/reschedule via the reminder (reply to SMS, click a link), or is this strictly one-way notification for now?
8. **Timing rules**: any expectation on when reminders go out (e.g., 24 hrs before, configurable per clinic), or is that unspecified/TBD?
9. **Patient consent/opt-out**: is there an existing patient consent process for receiving texts/emails, or does this need to be established as part of the requirement?
10. **Out of scope** — anything you already know this should *not* do (e.g., not a full scheduling system, not handling billing reminders, not multi-location/enterprise clinics)?

### USER

6. Staff enter or import appointments; existing systems vary, unknown. 7. Two-way would be nice but I haven't decided, TBD. 8. Timing unspecified, TBD. 9. Consent process unknown; someone at the clinic owns it. 10. Out of scope: scheduling itself and billing. That's enough - show me the draft with your assumptions and open questions, but don't write files yet.

### AGENT (claude -p, project skills via install/claude_code.py)

Here's a draft based on what we've covered. Nothing's written yet — review and tell me what to change.

---

# BR-XXX: Appointment Reminders for Small Clinics

**Status:** Draft
**Purpose:** Enable small, independent clinics to automatically send patients appointment reminders, reducing no-shows and the front-desk staff time currently spent phoning patients by hand.

## Background / Problem
Small, independent (mostly single-location) clinics currently rely on front-desk staff manually phoning patients to remind them of upcoming appointments. This is labor-intensive and no-show rates are still around 15%. We (a small company) intend to sell a reminder solution to these clinics.

## Stakeholders
- Clinic owners
- Front-desk staff
- Patients (affected, not direct purchasers/users)

## Objectives / Desired Outcomes
- Reduce appointment no-show rate (target: **TBD**)
- Reduce front-desk staff time spent on manual reminder calls (target: **TBD**)

## Scope
**In scope:**
- Sending appointment reminders via SMS and email
- Staff entering or importing appointment data into the tool (source systems vary by clinic; specific EHR/scheduling integrations: **TBD**)

**Out of scope:**
- Appointment scheduling itself
- Billing reminders
- (Two-way interaction — patient confirm/cancel/reschedule via reminder — is **undecided**; not committed as in-scope or explicitly excluded)

## Business Requirements
1. **BR-XXX-R001**: The business shall provide a way for clinic staff to send patients appointment reminders via SMS.
2. **BR-XXX-R002**: The business shall provide a way for clinic staff to send patients appointment reminders via email.
3. **BR-XXX-R003**: The business shall provide a way for clinic staff to enter or import appointment data into the system.
4. **BR-XXX-R004**: The business shall ensure patient reminder communications comply with applicable privacy/consent regulations (specific regulatory scope: **TBD** — likely includes healthcare privacy rules such as HIPAA, to be confirmed).
5. **BR-XXX-R005**: The business shall support a patient consent/opt-out process for receiving reminders (ownership: clinic; process design: **TBD**).

## Assumptions
- Target clinics are mostly single-location, independent practices (not multi-location/enterprise groups).
- Clinics have varying or no existing digital scheduling/EHR systems.
- This is a product to be sold to clinics, not an internal tool.

## Open Questions / TBDs
- Target no-show reduction and staff-time-saved metrics
- Scale (number of target clinics, appointments/day)
- Whether reminders will be one-way notifications only, or support two-way patient actions (confirm/cancel/reschedule)
- Reminder timing rules (fixed vs. configurable per clinic)
- Which specific privacy/data regulations apply (e.g., HIPAA) and what that requires
- How patient consent/opt-out is established and by whom
- Budget and timeline
- Whether/how integration with existing clinic scheduling/EHR systems is required

## References
None identified.

---

Let me know what to adjust — or say "write it" and I'll allocate IDs and create the file.

### USER

One change: R004 shouldn't name HIPAA - we don't know which rules apply. Otherwise write it.

### AGENT (claude -p, project skills via install/claude_code.py)

Done — no errors, warnings, or notices.

- **Path:** `BR/BR-001-appointment-reminders-for-small-clinics.md`
- **ID:** BR-001, **Status:** Draft
- **Requirements:** BR-001-R001 through BR-001-R005 (SMS reminders, email reminders, appointment entry/import, privacy/consent compliance, patient opt-out process)
- **Open TBDs:** success metrics, scale, one-way vs. two-way reminders, timing rules, applicable regulations, consent process ownership details, budget/timeline, EHR integration needs

This stays Draft until you explicitly approve it — happy to help resolve any of the TBDs or move on to a PRD when ready.

