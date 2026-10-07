# codex — 07-publish-preview

### USER

Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 18 s)

## Preview: US-001

- **Target repository:** `acme/widgets`
- **Action:** Create
- **Title:** `[US-001] Export overdue tasks`
- **Labels:** none
- **Preview digest:** `sha256:6a0cfb7801e7be402dd85a51b2f5119be554b0ad03943e25eb78187283de218a`

**Warnings and notices:**
- The Story is Draft, not Approved; the Issue would use its current text.
- One unresolved acceptance behavior (TBD) is included as written.
- The Story is standalone (`covers: []`), which is publishable.

**Complete Issue body:**

> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-export-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.

**Purpose:** Let tasklog developers share overdue tasks as a CSV.  
**Covers:** none — standalone Story

## Story

As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them.

## Scope

### In Scope
- Export overdue tasks as CSV, with each task represented as a row containing its title and due date.
- Produce a header-only CSV when there are no overdue tasks.

### Out of Scope
- No other export behavior is specified.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export overdue tasks as CSV, **then** the CSV contains one row per overdue task, and each row contains that task's title and due date.
2. **Given** there are no overdue tasks, **when** I export overdue tasks as CSV, **then** the CSV contains only its header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Whether completed tasks are exported.

## Edge Cases and Negative Paths

- No additional decided edge cases.

## Open Questions

- Whether completed tasks are exported.

The preview was read-only: **no GitHub change was made**, and repository access has not been checked.

