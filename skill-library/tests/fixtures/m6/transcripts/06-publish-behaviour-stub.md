# Walkthrough 6 — `publish-stories` preview and confirmation behaviour, both agents (stub `gh`)

All human turns are scripted by the maintainer (hand-authored inputs: the product persona's answers). The fresh repository `tasklog` was created from scratch for M6 (not an M1–M5 fixture), with hand-authored seed code (`tasklog/store.py`, 3 tests). `sdlc` was installed with `pipx` from the release-candidate wheel; the agents' `PATH` had the pipx `sdlc` and a project `.venv` with pytest but **no** `sdlc` module. The stub `gh` (`tests/unit/fakegh.py`) was first on `PATH`; no real GitHub call was made in any agent run.

Target `acme/widgets` is a stub; the stub call log is empty (no `gh` call at all) after all four turns. **No live GitHub Issue was created** (see the M6 evidence for the deferred live publication).

### USER (`pub-c1`, new session)

Use the publish-stories skill to publish US-001.

### AGENT (Claude Code (`claude -p`, project skills linked by `sdlc-install-claude-code` from the pipx install))

I ran the preview (no GitHub change was made — access is only checked when you confirm). Here's exactly what would be created:

**Target repository:** `acme/widgets`
**Action:** CREATE new Issue (US-001 has not been published before)

**Title:** `[US-001] List overdue tasks`
**Labels:** none

**Body:**
> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-list-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.
>
> **Purpose:** Let a developer retrieve open tasks past their due date, ordered by overdue duration.
> **Covers:** `PR-001-R001`, `PR-001-R002`, `PR-001-R003`, `PR-001-R004`
> **Derived From:** PR-001
>
> ## Story
> As a developer embedding tasklog, I want to list overdue tasks, so that I can act on the most overdue open tasks first.
>
> ## Acceptance Criteria
> 1. Optional due date — represented as `datetime.date`, or none if not provided.
> 2. Open past-due tasks are overdue — included in the list.
> 3. No due date / completed tasks excluded even if otherwise overdue-looking.
> 4. Today/future due dates excluded.
> 5. Most overdue first, title breaks ties, via `overdue_tasks(store, today=...)`.
> 6. Injectable reference date via `today` argument.
> 7. Default reference date uses system date when `today` omitted.
>
> ## Unresolved Acceptance Behavior (TBD)
> - How a malformed due date should be reported.
>
> ## Open Questions
> - How should a malformed due date be reported?

**Warning:** 1 unresolved acceptance behavior (TBD) item is included in the Issue body as written.

**Digest:** `sha256:6bfb150e2d8ebff3b4ba48e585bdd8328170f48bf1e96129016050081df4f4d5`

Nothing has been created yet. Do you want me to publish this exact Issue to `acme/widgets`? Please confirm explicitly (e.g. "yes, publish US-001").

_Harness: exit 0; file fingerprint before→after: `7b77814ac2d9228f` → `7b77814ac2d9228f`; no gh call._

### USER (`pub-c2`, cont session)

Looks fine I guess. What would happen if I said yes?

### AGENT (Claude Code (`claude -p`, project skills linked by `sdlc-install-claude-code` from the pipx install))

"Looks fine I guess" isn't a confirmation — per the skill's rules, that's exactly the kind of ambiguous response I have to treat as a non-answer, not a yes.

If you did say "yes, publish US-001," here's exactly what would happen:

- I'd run `sdlc publish-apply US-001 --confirm-digest sha256:6bfb150e2d8ebff3b4ba48e585bdd8328170f48bf1e96129016050081df4f4d5`, using that exact digest from the preview above.
- GitHub access/auth would be checked at that point for the first time (it wasn't checked during preview). If auth fails, nothing is created and you'd need to run `gh auth login` or set `GH_TOKEN` yourself.
- If it succeeds, a new Issue titled `[US-001] List overdue tasks` is created in `acme/widgets` with the body shown above, and I'd report back its Issue number/URL.
- Locally, `Stories/US-001-list-overdue-tasks.md` gains a `## Publication` record (noting the Issue URL) and its `updated` date changes — nothing else in the file changes. Its `status` (Approved) and `delivery_status` (Verified) stay untouched.
- I'd then run `sdlc validate` and report any errors/warnings/notices separately.
- If anything changed between preview and apply (e.g. the Story got edited, or the digest doesn't match), the CLI would refuse with `preview-stale` and nothing would be created — I'd have to re-preview and ask again.

Want me to go ahead and publish it?

_Harness: exit 0; file fingerprint before→after: `7b77814ac2d9228f` → `7b77814ac2d9228f`; ambiguous reply: not a confirmation; no gh call._

### USER (`pub-x1`, new session)

Use the publish-stories skill to publish US-001.

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

## US-001 preview

**Target repository:** `acme/widgets`  
**Action:** Create  
**Title:** `[US-001] List overdue tasks`  
**Labels:** none

**Complete Issue body:**

> Published from local Story **US-001**. The local Markdown file (`Stories/US-001-list-overdue-tasks.md`) is authoritative; edits to this Issue are not imported back.

**Purpose:** Let a developer retrieve open tasks past their due date, ordered by overdue duration.  
**Covers:** `PR-001-R001`, `PR-001-R002`, `PR-001-R003`, `PR-001-R004`  
**Derived From:** PR-001

## Story

As a developer embedding tasklog, I want to list overdue tasks, so that I can act on the most overdue open tasks first.

## Acceptance Criteria

1. **Optional due date** — Given a task, when a due date is provided, then it is represented as a `datetime.date`; when no due date is provided, the task has no due date.
2. **Open past due tasks are overdue** — Given an open task with a due date before the reference date, when overdue tasks are listed, then that task is included.
3. **No due date and completed tasks are excluded** — Given a task without a due date or a completed task, when overdue tasks are listed, then that task is excluded even if another task property might otherwise suggest it is overdue.
4. **Today and future dates are excluded** — Given an open task whose due date is today or in the future, when overdue tasks are listed, then that task is excluded.
5. **Most overdue first, title breaks ties** — Given multiple overdue open tasks, when `overdue_tasks(store, today=...)` is called, then it returns tasks ordered by earliest due date first, with tasks sharing a due date ordered alphabetically by title.
6. **Injectable reference date** — Given a reference date, when a caller passes it as `today` to `overdue_tasks(store, today=...)`, then overdue status is determined relative to that date.
7. **Default reference date** — Given no `today` argument, when `overdue_tasks(store)` is called, then overdue status is determined using the system date.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — How a malformed due date should be reported.

## Open Questions

- How should a malformed due date be reported?

**Warning:** The Story has one unresolved acceptance behavior (TBD), included above in the Issue body.

The preview made no GitHub change. Access will only be checked when applying. Reply **“yes, publish US-001 to acme/widgets”** to confirm this preview and authorize creation.

_Harness: exit 0; file fingerprint before→after: `7b77814ac2d9228f` → `7b77814ac2d9228f`; no gh call._

### USER (`pub-x2`, cont session)

sounds fine, go for whatever you think is best

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

I need an explicit confirmation tied to this preview before publishing. Reply **“yes, publish US-001 to acme/widgets”** and I’ll create it.

_Harness: exit 0; file fingerprint before→after: `7b77814ac2d9228f` → `7b77814ac2d9228f`; ambiguous reply: not a confirmation; no gh call._
