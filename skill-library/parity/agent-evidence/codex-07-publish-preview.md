# codex — 07-publish-preview

### USER

Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 38 s)

## Preview: US-001

**Target repository:** `acme/widgets`  
**Action:** Create  
**Title:** `[US-001] Export overdue tasks`  
**Labels:** none

**Complete Issue body:**

> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-export-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.

**Purpose:** Let tasklog developers share overdue tasks by exporting them as CSV.  
**Covers:** none — standalone Story

## Story

As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them.

## Scope

### In Scope
- Export overdue tasks as CSV rows containing each task's title and due date.
- Produce a header-only CSV when there are no overdue tasks.

### Out of Scope
- Behavior not specified in the decided acceptance criteria remains unresolved.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export, **then** each overdue task is one CSV row with title and due date.
2. **Given** no overdue tasks, **when** I export, **then** the CSV has only the header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Are completed tasks exported?

## Edge Cases and Negative Paths

- Empty overdue-task export is covered by acceptance criterion 2.

## Open Questions

- Whether completed tasks are exported.

**Warnings and notice:** The Story is Draft, not Approved; one unresolved acceptance behavior (TBD) is included in the body. It is a standalone Story with no covered requirements.

The preview made no GitHub change. Access to the repository is checked only when applying.

