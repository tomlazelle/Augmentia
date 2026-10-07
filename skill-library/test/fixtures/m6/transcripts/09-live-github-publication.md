# Live GitHub publication (the one real publication required by M6)

Real `gh` 2.46.0 (stub removed from `PATH`; `SDLC_GH_COMMAND=/usr/bin/gh`), pipx-installed `sdlc 1.0.0rc1`, in the walkthrough project `tasklog` (US-001: `status: Approved`, `delivery_status: Verified`). Human turns are the maintainer's actual messages.

### Designation and authorization sequence (chronological)

1. Agent asked which repository to use. Human: "use local for now" (read as deferral; nothing created).
2. Human later designated `https://github.com/tomlazelle/Augmentia`. Agent checked it read-only (public, Issues enabled, no Issues) and showed the full live preview for it (digest `sha256:f1d2d577…`). **No publication.**
3. Human asked "What do you want to do exactly?" Agent explained the single Issue and waited.
4. Human re-designated: "You can publish here https://github.com/tomlazelle/UsedForPractice". Agent did **not** treat that as authorization: it checked the repo read-only (public, Issues enabled, no Issues), set the walkthrough config to it, regenerated the preview (body byte-identical to the one shown before, verified with `diff`), showed it in full, and asked for explicit confirmation of that specific preview.
5. Human: "do it". This was the reply to that exact request, and only then was the Issue created.

### Live preview that was authorized (`sdlc publish-preview US-001`)

```text
Target: github tomlazelle/UsedForPractice   (access is checked only when applying)
=== US-001 — CREATE ===
Title: [US-001] List overdue tasks
Labels: none
Body: (full text = ../live-publication/issue-body.md)
Will create: US-001
Digest: sha256:befd69bfd947b43bd85d4cc7e4a1c133e5c0a3bde1b822fdf2f6ab36dd5f158b
Preview only — no external mutation was made.
```

### Publication (`sdlc publish-apply US-001 --confirm-digest sha256:befd69bf…`)

```text
US-001: published https://github.com/tomlazelle/UsedForPractice/issues/1
External mutations: 1
```

### Verification (read-only)

`gh issue view 1 --repo tomlazelle/UsedForPractice --json …` → `{"number":1,"state":"OPEN","title":"[US-001] List overdue tasks","labels":[],"author":{"login":"tomlazelle"},"createdAt":"2026-10-05T20:15:19Z","url":"https://github.com/tomlazelle/UsedForPractice/issues/1"}`. The Issue body on GitHub equals the previewed body (checked programmatically: `True`). Snapshot: `live-publication/issue.json`, `issue-body.md`.

Local record appended to the Story (`live-publication/US-001-list-overdue-tasks.md`):

```markdown
## Publication

### PUB-1 — 2026-10-05
- **Provider:** github
- **Repository:** tomlazelle/UsedForPractice
- **Issue:** #1
- **URL:** https://github.com/tomlazelle/UsedForPractice/issues/1
- **Recorded by:** `sdlc publish-apply` (publication is non-material; local Markdown stays authoritative)
```

`status: Approved` and `delivery_status: Verified` unchanged; only `updated` moved; the Story file is the only file changed (9 lines added).

### Same-repository duplicate prevention

`sdlc publish-preview US-001` → `=== US-001 — SKIP ===`, notice `already-published … tomlazelle/UsedForPractice#1`, `Will create: nothing`. `sdlc publish-apply US-001 --confirm-digest <that digest>` → `US-001: skipped already published`, `External mutations: 0`. `gh issue list --repo tomlazelle/UsedForPractice --state all` afterwards: exactly one Issue (`#1`) (`live-publication/issues-after-duplicate-attempt.json`).

### Final `sdlc validate`

`7 document(s): 0 error(s), 1 warning(s), 0 notice(s)`, exit 0; the single warning is the expected `verified-with-unresolved-tbd`. The Issue was not closed, edited or deleted.
