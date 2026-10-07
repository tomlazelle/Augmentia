### USER

Use the create-prd skill to remove requirement PR-001-R002 (manual entry of appointments) from PR-001: product decided it is out of MVP. Show me what will be affected before you change anything.

### AGENT (claude -p, project skills via install/claude_code.py)

Here's the impact analysis before I touch anything:

**Requirement being removed:** PR-001-R002 — "Staff shall be able to manually enter an appointment."

**Directly affected:**
- **PR-001** (`PR/PR-001-appointment-reminders-for-clinics.md`), status `Draft`:
  - Requirement line 70 removed/retired.
  - Scope section (line 54): "CSV import + manual entry of appointments" — needs to drop "+ manual entry".
  - Behavior and Capabilities (line 44): "Staff can import appointments via CSV or enter them manually." — needs rewording.
  - Product Summary (line 4/25) and Journeys (line 37) both say "import or enter" — worth checking if these should also change to just "import" for consistency (your call — I won't touch prose beyond the requirement unless you confirm).
  - Since PR-001 is `Draft`, not `Approved`, this edit won't trigger an approval reset — just an `updated` date bump.

- **US-002** ("Manually Enter an Appointment", `Stories/US-002-manually-enter-an-appointment.md`), status `Draft`, `[Not Started]`:
  - Its `covers: [PR-001-R002]` points at the requirement being retired — this Story becomes orphaned/uncovered.
  - It's also cross-referenced from **US-001** and **US-003** ("Related To").

No other documents reference PR-001-R002.

**Questions before I proceed:**
1. For US-002 — do you want it deleted, marked out-of-scope/retired, or left as-is with a broken `covers` (not recommended)? The skill's workflow asks me to check with you on how its `covers` should change once the requirement is retired.
2. Should I also update the Product Summary / Behavior / Journeys prose in PR-001 to drop "or enter manually" language, or leave those as-is and only touch the requirement + Scope list?

Let me know how you'd like US-002 handled and I'll make the edits.

### USER

1. Keep US-002 but make it standalone: covers: [] and drop it from Derived From; note in its Open Questions that its requirement was retired. 2. Yes, update the PR-001 prose too so it only talks about CSV import. Apply everything.

### AGENT (claude -p, project skills via install/claude_code.py)

Done. Summary:

- **PR-001-R002 retired** via `sdlc retire-id`, with note "Manual entry of appointments moved out of MVP scope per product decision."
- **PR-001**: requirement removed from the Product Requirements list; "manual entry" language stripped from purpose, summary, target-user needs, journeys, and Behavior/Capabilities; MVP scope now reads "CSV import of appointments"; "Manual entry of appointments" added to Out of Scope / Later. Status stays `Draft` (no approval reset needed).
- **US-002**: `covers` set to `[]`, dropped from "Derived From," and an Open Questions note records that its originating requirement was retired and it's now a standalone/backlog story.
- Ran `update-map` (PR/map.md and Stories/map.md refreshed) and `validate`: 0 errors, 0 warnings, 2 notices — both expected `story-no-coverage` notices for standalone stories (US-002 and pre-existing US-006).

No other documents referenced PR-001-R002. Nothing here is `Approved`, so no approval was reset.

