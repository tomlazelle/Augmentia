### USER

Use the create-prd skill. I want a PRD titled 'Patient notification service for clinics' with purpose 'Notify patients ahead of appointments by text and email'. Do not write or allocate anything yet.

### AGENT (claude -p, project skills via install/claude_code.py)

The automated CLI check found no lexical overlap, but a manual review flags one:

**Conceptual overlaps (my judgement, not CLI-scored)**
- **PR-001 — Appointment Reminders for Clinics**: purpose is "Let clinic front-desk staff import or enter appointments and automatically send patients SMS/email reminders, reducing no-shows and manual reminder calls." This looks like the same product concern as "Patient notification service for clinics" (notify patients ahead of appointments by text and email) — same channels (SMS/email), same audience (clinic patients), same trigger (appointments).

Before I go further (and per your instruction, I won't allocate or write anything), how do you want to proceed?

1. **Revise** PR-001 — treat this as the same product, refine/extend it under the existing ID.
2. **Relate** — create a new PRD "Patient notification service for clinics" that links to PR-001 under `### Related To` (e.g. if this is meant as a broader notification service vs. a narrower reminders feature).
3. **Create new / independent** — if you're confident this is a genuinely separate product/document despite the similarity.

Which would you like?

