# codex — 07-publish-preview

### USER

Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 32 s)

## Preview: US-001

**Target repository:** `acme/widgets`  
**Action:** Create  
**Title:** `[US-001] Export overdue tasks`  
**Labels:** none

**Complete Issue body:**

> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-export-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.

**Purpose:** Let tasklog developers share overdue tasks in CSV form.  
**Covers:** none — standalone Story

## Story

As a developer using tasklog, I want to export the overdue tasks as CSV, so that I can share them.

## Scope

### In Scope
- Export overdue tasks to CSV, with each overdue task represented as a row containing its title and due date.
- Produce a header-only CSV when there are no overdue tasks.

### Out of Scope
- No additional export behavior has been specified.

## Acceptance Criteria

1. **Given** tasks past their due date, **when** I export, **then** each overdue task is one CSV row with its title and due date.
2. **Given** no overdue tasks, **when** I export, **then** the CSV has only the header row.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — Should completed tasks whose due dates are past be included in the export?

## Edge Cases and Negative Paths

- No additional decided edge-case outcomes were provided.

## Open Questions

- Should completed tasks whose due dates are past be included in the export? (TBD)

**Warnings and notice:**

- The Story is Draft, not Approved; the Issue will show its current text.
- One unresolved acceptance behavior (TBD) is included as written.
- This is a standalone Story with no requirement coverage.

The preview made no GitHub change. Repository access is checked only when applying.

You asked for preview only and have not confirmed anything, so nothing will be published.

