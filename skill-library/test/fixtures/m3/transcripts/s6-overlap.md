### USER

Use the create-brd skill. I want a BRD for automated appointment reminders for independent clinics. Ask me what you need, but do not write or allocate anything yet.

### AGENT (claude -p, project skills via install/claude_code.py)

There's already a draft BRD for this exact topic: **BR-001 — Appointment Reminders for Small Clinics**, with a set of open questions already logged (regulatory scope, consent, timing rules, two-way actions, scale, integrations, budget/timeline).

Before I ask anything new — do you want to:

1. **Revise/extend BR-001** (build on what's already captured, and work through its existing open questions), or
2. **Start a fresh BRD** for this idea, treating it as a separate/unrelated effort?

If it's the same idea (which it looks like), I'd lean toward option 1, and I'll pick up from its open questions rather than re-asking from scratch. Let me know which way to go, and then I'll start the interview — I won't write or allocate anything until you've reviewed a draft.

### USER

Option 1: revise BR-001. Resolve the timing question: reminder timing is configurable per clinic. Also add a business requirement that patients must be able to opt out of reminders. Show me the proposed changes first; don't edit yet.

### AGENT (claude -p, project skills via install/claude_code.py)

Here's what I'd propose for BR-001, based on your two answers. Nothing has been written yet — just showing the diff for your review.

## 1. Resolve the timing open question

**Remove** from Open Questions:
> What are the reminder timing rules — fixed lead time or configurable per clinic? Owner: Unknown.

**Add to Scope → In Scope:**
> - Clinic-configurable reminder timing (e.g., lead time before appointment) per clinic

**Add a new Business Requirement (would be allocated BR-001-R006):**
> The business shall allow clinic staff to configure reminder timing (lead time before the appointment) on a per-clinic basis.

## 2. Add patient opt-out requirement

Note: BR-001 already has **R005** — "The business shall support a patient consent/opt-out process for receiving reminders, owned by the clinic." That's about the clinic owning the process. Your new ask is more specific: the patient must have a way to opt out directly.

Two ways to handle it — pick one:

- **(a) New requirement** (would be allocated BR-001-R007): "The business shall provide patients with a mechanism to opt out of receiving reminders." Keep R005 as-is (clinic owns the overall consent process) alongside this more concrete guarantee.
- **(b) Fold into R005** by rewording it to make the patient-facing guarantee explicit, e.g.: "The business shall support a patient consent/opt-out process for receiving reminders, owned by the clinic, and shall ensure patients have a means to opt out of reminders." No new requirement ID.

I'd lean toward (a) since it's a distinct, testable guarantee separate from clinic-side process ownership — but let me know which you'd like.

**Also affected:**
- **Assumptions and Risks** — the risk "Without a defined patient consent/opt-out process, clinics may send reminders without proper consent" would be resolved/softened once this requirement exists; I'd leave the risk but could note it's now addressed by R00x.
- `updated` date would change to 2026-09-29 (today) — already today's date, so no change needed there.
- Status stays `Draft` (no approval change).

Confirm the opt-out approach (a or b) and I'll apply both changes, allocate the new requirement ID(s), update the map, and validate.

### USER

Go with (a). Apply the changes.

### AGENT (claude -p, project skills via install/claude_code.py)

Done. Validation is clean: 0 errors, 0 warnings, 0 notices.

**BR-001 — Appointment Reminders for Small Clinics** (`BR/BR-001-appointment-reminders-for-small-clinics.md`), status remains `Draft`.

Changes applied:
- **BR-001-R006** (new): Business shall allow clinic staff to configure reminder timing (lead time) per clinic — also added to In Scope.
- **BR-001-R007** (new): Business shall provide patients a mechanism to opt out of receiving reminders.
- Removed the now-resolved open question on timing rules.
- Noted in Assumptions/Risks that the consent risk is partially addressed by R005 + R007.

Remaining open questions in the doc (still unresolved): target no-show/staff-time metrics, expected scale, two-way patient actions (confirm/cancel/reschedule), applicable privacy regulations, budget/timeline, and EHR/scheduling integration needs.

Requirements now: R001–R007. Approval is still your call whenever you're ready to mark it `Approved`.

