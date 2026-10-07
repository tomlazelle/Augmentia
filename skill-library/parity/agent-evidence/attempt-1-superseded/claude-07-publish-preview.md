# claude — 07-publish-preview

### USER

Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 14 s)

Here's the preview — no GitHub change has been made yet.

**Target repository:** `acme/widgets`
**Action:** CREATE (US-001 has not been published before)

**Title:** `[US-001] Export overdue tasks`
**Labels:** none

**Body** (full text as it will appear):

> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-export-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.
>
> **Purpose:** Let a developer export overdue tasks as CSV so they can share them.
> **Covers:** none — standalone Story
>
> ## Story
> As a developer using tasklog, I want to export the overdue tasks as CSV, so that I can share them.
>
> ## Scope
> **In Scope**
> - Exporting tasks that are past their due date as a CSV file.
> - One CSV row per overdue task, containing title and due date.
> - Producing a CSV with only the header row when there are no overdue tasks.
>
> **Out of Scope**
> - Exporting tasks that are not overdue.
> - Any export format other than CSV.
>
> ## Business Rules
> - None identified.
>
> ## Acceptance Criteria
> 1. Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date.
> 2. Given no overdue tasks, when I export, then the CSV has only the header row.
>
> ### Unresolved Acceptance Behavior (TBD)
> - TBD — Whether completed tasks that are past their due date are included in the export.
>
> ## Edge Cases and Negative Paths
> - None identified.
>
> ## Open Questions
> - Whether completed tasks are exported — Unknown.

**Warnings/notices:**
- ⚠️ Story status is **Draft**, not Approved — the Issue will show this current text as-is.
- ⚠️ There's 1 unresolved TBD item, included verbatim in the Issue.
- ℹ️ Standalone Story (no `covers` requirements) — this is fine/publishable.

**Digest:** `sha256:96e4f29a347318f09faf9a197e0bee5145e4ee6d6789c43f4d19f4990629ca86`

This preview made no GitHub changes — access is only checked when applying. I will not publish unless you explicitly confirm (e.g., "yes, publish US-001").

