# claude — 03-refine

### USER

Use the refine-stories skill on US-001. I declare it Ready, and I explicitly accept that its one unresolved item (whether completed tasks are exported) stays as TBD while the Story is Ready; that is my decision, do not ask me again. Use only what is already in the Story; do not invent anything. Then update the map and validate.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 30 s)

No requirement gaps, no edge cases to add — everything the user wanted was already accurate in the Story, so the only change needed was the readiness declaration.

**What changed:** `delivery_status: Not Started → Ready` on US-001. No other content touched — the Story already correctly carried the TBD (completed-task export behavior) under `### Unresolved Acceptance Behavior (TBD)` and `Open Questions`, so marking it Ready with that item still open is exactly the exception you accepted, not a new edit.

**Still TBD (by your explicit acceptance):** whether completed tasks past their due date are included in the export.

**Readiness checklist:** bounded scope with In/Out of Scope ✓, two decided numbered Given/When/Then criteria ✓, the one undecided item correctly listed as TBD rather than as a criterion ✓, `covers: []` is a deliberate standalone Story ✓, no named dependencies/blockers ✓, `sdlc validate` clean ✓.

**Validate result:** 0 errors, 0 warnings, 1 notice (`story-no-coverage` — expected for a standalone Story with `covers: []`, not an error).

