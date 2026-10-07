(fixture setup: BR-001 and US-003 set to Approved, dated 2026-09-01; CLAUDE.md from install/project-instructions copied to the project root; skills installed via the adapter)

### USER

Two revisions. (1) BR-001: add a business requirement that clinics must be able to see a monthly report of reminders sent. (2) US-003: add an acceptance criterion that a reminder is never sent for a cancelled appointment. Both are agreed - apply them now, then run update-map and validate.

### AGENT (claude -p, project skills via install/claude_code.py)

Both revisions are applied and validated clean (0 errors, 0 warnings; the one notice is a pre-existing, unrelated standalone-coverage note on US-006).

**BR-001** — `BR/BR-001-appointment-reminders-for-small-clinics.md`
- Added **BR-001-R006**: "The business shall provide clinics with a monthly report of reminders sent."
- Status reset from `Approved` → **`In Review`** (material change to an approved document) — this needs your re-approval.

**US-003** — `Stories/US-003-send-automatic-appointment-reminder.md`
- Added acceptance criterion #4: reminder is never sent for a cancelled appointment.
- Status reset from `Approved` → **`In Review`** — this also needs your re-approval.

`update-map` and `validate` ran clean for both. Let me know when you're ready to re-approve either document.

