# claude — 07-publish-preview

### USER

Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 15 s)

Here's the preview — no GitHub changes have been made yet.

**Target repository:** `acme/widgets`

**US-001 — CREATE** → "[US-001] Export overdue tasks" (no labels), full body as shown above.

**Warnings/notices:**
- Story status is **Draft**, not Approved — the Issue will reflect the current (unapproved) text.
- 1 unresolved acceptance behavior (TBD): whether completed overdue tasks are included/excluded — this is included in the Issue as written.
- Standalone Story (covers: none) — publishable, just a notice.

**Digest:** `sha256:0e224e1bc9ecce0e7ab8993872baabfde004248bf3885b2457b276473d092887`

This is preview-only — nothing has been created on GitHub, and access isn't checked until an apply is run. I will not publish unless you give explicit confirmation (e.g. "yes, publish US-001").

