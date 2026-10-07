# claude — 07-publish-preview

### USER

Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 17 s)

Here's the preview — no GitHub changes have been made, and access will only be checked at apply time.

**Target repository:** `acme/widgets`

**US-001 — CREATE**
- **Title:** `[US-001] Export overdue tasks`
- **Labels:** none
- **Body:** the full exported Markdown shown above (purpose, story, in/out of scope, acceptance criteria, the unresolved TBD item, edge cases, open questions)
- **Action:** will create a new Issue (not previously published to this repository)

**Warnings/notices:**
- Story status is **Draft**, not Approved — the Issue will reflect the current (unapproved) text as-is.
- There is **1 unresolved acceptance-behavior (TBD)** item — whether completed-and-overdue tasks are included — and it's included in the Issue body as written.
- This is a standalone Story (no `covers` — no PRD/BRD linkage); that's expected and publishable.

**Digest:** `sha256:edad41d6d19aeca89864b069420ee108b802415f9c2d7bc2659166e2abc45877`

Nothing has been published. If you'd like me to proceed, say so explicitly (e.g. "yes, publish US-001") and I'll run `publish-apply` with this exact digest.

