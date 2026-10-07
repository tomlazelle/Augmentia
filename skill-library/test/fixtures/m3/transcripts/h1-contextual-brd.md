### USER

Use the create-brd skill. I want a BRD titled 'Automated appointment reminders for independent clinics' with purpose 'Send patients reminders to cut no-shows'. Do not write or allocate anything yet.

### AGENT (claude -p, project skills via install/claude_code.py)

This is clearly the same concern as an existing BRD, even though the automated overlap check found nothing.

**Conceptual overlaps (my judgement, not CLI-scored)**
- **BR-001 — "Appointment Reminders for Small Clinics"**: same purpose in different words — "Enable small, independent clinics to automatically send patients appointment reminders, reducing no-shows..." matches your stated purpose almost verbatim ("Send patients reminders to cut no-shows" for "independent clinics").

The CLI's lexical check returned no candidates, but reading BR-001's content myself, this looks like the same business need already drafted.

How would you like to proceed?
1. **Revise** BR-001 in place (keep its ID, update title/content as needed)
2. **Relate** — create a new BRD that links to BR-001 under `Related To`
3. **Create new** — an independent document, treating this as a distinct concern

I won't allocate an ID or write anything until you choose.

### USER

Relate. The new BRD is about the clinic-owner side: owners need a way to see whether reminders actually reduce no-shows (reporting on outcomes). Problem: owners currently can't tell if reminders help. Stakeholders: clinic owners. Success target: TBD. Scope: outcome reporting only; out of scope: sending reminders. Constraints: TBD. Write it now, keep unknowns as TBD, no more questions.

### AGENT (claude -p, project skills via install/claude_code.py)

Written and validated cleanly.

- **BR-002** — `BR/BR-002-appointment-reminder-outcome-reporting-for-clinic-owners.md`, status `Draft`, related to BR-001
- Requirement: **BR-002-R001** — clinic owners can see whether reminders are reducing no-shows
- Open TBDs: success metric/target, constraints/dependencies
- `validate`: 2 documents, 0 errors, 0 warnings, 0 notices

Approval is your call whenever you're ready.

