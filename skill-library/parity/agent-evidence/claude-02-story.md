# claude — 02-story

### USER

Use the create-stories skill to create ONE standalone Story (no PRD, no BRD). I cannot answer questions interactively, so these are my complete answers; treat everything else as TBD and do not ask me anything. Title: "Export overdue tasks". As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them. Acceptance criteria (decided): 1. Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date. 2. Given no overdue tasks, when I export, then the CSV has only the header row. Unresolved (put under TBD, not as criteria): whether completed tasks are exported. Run the overlap check and the contextual overlap review as your Skill says (the project is new, so expect none), create the Story as a Draft, then update the map and validate. Do not set any delivery status.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 42 s)

Validation passed with 0 errors, 0 warnings, and 1 notice (expected for a standalone Story).

**Summary**

- **Path:** `Stories/US-001-export-overdue-tasks.md`
- **ID:** US-001, `status: Draft`, `delivery_status: Not Started` (unchanged)
- **covers:** `[]` (standalone — no PRD/BRD)
- **Overlap check:** CLI `find-overlaps` returned no candidates; conceptual review found none (project was empty)
- **Acceptance criteria:** 2 (both as you specified)
- **TBD:** whether completed overdue tasks are exported — recorded under Unresolved Acceptance Behavior and Open Questions, not as a criterion
- **Validate:** 0 errors, 0 warnings, 1 notice (`story-no-coverage`, expected for standalone Stories)

No approval or delivery-status change was made — those remain yours to decide.

