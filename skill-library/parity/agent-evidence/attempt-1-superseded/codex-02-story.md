# codex — 02-story

### USER

Use the create-stories skill to create ONE standalone Story (no PRD, no BRD). I cannot answer questions interactively, so these are my complete answers; treat everything else as TBD and do not ask me anything. Title: "Export overdue tasks". As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them. Acceptance criteria (decided): 1. Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date. 2. Given no overdue tasks, when I export, then the CSV has only the header row. Unresolved (put under TBD, not as criteria): whether completed tasks are exported. Run the overlap check and the contextual overlap review as your Skill says (the project is new, so expect none), create the Story as a Draft, then update the map and validate. Do not set any delivery status.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 48 s)

Created [US-001 — Export overdue tasks](<PROJECT>/Stories/US-001-export-overdue-tasks.md) as a Draft standalone Story. It has 2 acceptance criteria, `covers: []`, and completed-task inclusion recorded as TBD. Delivery status remains **Not Started**.

The overlap check found no candidates, and the contextual review found no conceptual overlaps. The Story map was updated. Validation reported **0 errors, 0 warnings, and 1 notice**: `story-no-coverage`, expected for a standalone Story.

