---
name: publish-stories
description: Publish selected local Stories as GitHub Issues, only after showing the exact proposed Issues and receiving explicit human confirmation. Local Markdown stays authoritative; no sync back. Use when the user asks to publish, push, export or create GitHub Issues from Stories. Never publishes without a preview and an unambiguous confirmation.
---

# publish-stories

Turns local Stories into GitHub Issues **after the human has seen exactly what will be created and said yes**. GitHub is a publication target, not the source of truth. Audience: the human who owns the Stories and the repository.

Contract, formats, failure table and what counts as confirmation: `../../shared/publishing-conventions.md` (read it, especially §3, §5, §6, §7). CLI: `sdlc` (`../../shared/cli-contract.md`); if it fails with `command not found: sdlc`, tell the user to install the library and stop. If the project is not initialized, suggest `sdlc-init` and stop.

**Never create an Issue yourself** (no `gh issue create`, no API calls, no other tool). The only way to publish is `sdlc publish-apply`, which the CLI refuses unless the digest matches the current preview.

## Workflow

1. **Select.** The human must name the Stories. If they have not, show `sdlc list --category US` and ask which. Never publish all Stories because they exist.
2. **Preview (no mutation).** Run `sdlc publish-preview <US-ID> [<US-ID> …]`.
   - Missing or invalid `publishing` configuration, an unsupported provider, or a blocked Story: report it clearly and stop. For missing config, ask the human for the repository and, if they agree, add only `publishing: {provider: github, repository: owner/name}` to `.sdlc/config.md`. **Never write a token or any credential anywhere.**
   - Stories that fail validation are `blocked`; explain why and offer `sdlc-validate` or `refine-stories`. Do not publish a subset silently: the human re-selects.
3. **Show the preview to the human, verbatim.** For every selected Story show: target repository, Issue title, the **complete body** (not a summary), labels (none), whether it is `create` or already published **in this repository** (known Issue number/URL → it will be skipped, nothing created; publications in other repositories are shown as notices and do not block), and every warning or notice (unresolved TBD included in the Issue as written, not-Approved status, relative links, standalone Story). State that the preview made no GitHub change and that access is only checked when applying.
4. **Ask for explicit confirmation.** Name the Stories and the repository and ask whether to publish them. Only an unambiguous affirmative to this preview counts (e.g. "yes, publish US-001 and US-002"). Invoking this Skill, asking for a preview or "what would happen", silence, "looks good", "maybe", "ok?", a question, or approval of an earlier preview is **not** confirmation: ask again or stop. A decline ends the workflow with nothing published.
5. **Publish exactly what was confirmed.** Run `sdlc publish-apply <same IDs> --confirm-digest <digest from the preview the human saw>`. Use only that digest: never one printed by a refused apply, never an invented one.
   - If the preview content could have changed (the human or you edited a Story, the selection changed, the configuration changed) or the CLI reports `preview-stale`: nothing was published; go back to step 2, show the new preview, and ask again.
6. **Report per Story, literally.** `published` (Issue number/URL, PUB record), `skipped` (already published; say only that a known Issue exists, nothing about whether it is current), `failed` (reason; nothing recorded), `not-attempted`, `unconfirmed`, `published-unrecorded`. Never claim success for anything but `published`; never retry a failure blindly. Say precisely what changed locally: each published Story file gained a `## Publication` record and a new `updated` date, and nothing else (do not say "Local Markdown is untouched"). For `unconfirmed` or `published-unrecorded`, lead with the inconsistency, give the Issue URL if known, and tell the human not to publish that Story again until the record is fixed.
7. **Validate.** Run `sdlc validate`; report errors, warnings and notices separately. Publishing changes no map, so a stale map would be a pre-existing issue.

## Rules

- No external mutation before a shown preview **and** explicit confirmation of that preview. No exceptions, including "just this once" and automated runs.
- Publishing never changes requirements, acceptance criteria, `status` or `delivery_status`, and the Publication record is non-material (an Approved Story stays Approved). Do not "fix" a Story's content to make publishing smoother; if the human wants a change, route it through the authoring Skill and re-preview.
- Do not update, close, label or edit existing Issues, and do not import anything from GitHub. If asked, explain that M5 publishes new Issues only and local Markdown is authoritative.
- Do not describe a GitHub Issue's content or state (up to date, out of sync, open, closed): you have not read it and this Skill never does. Do not infer anything about local delivery from GitHub (an open or closed Issue says nothing about `delivery_status`).
- Do not use any provider other than GitHub Issues, and do not create PRs, branches, commits, releases, projects, milestones or labels.
- Never print or store credentials. If authentication fails, tell the human to run `gh auth login` (or set `GH_TOKEN`) themselves; do not ask them to paste a token.
- Do not hand-edit `.sdlc/ledger.md` or a `map.md` generated region.
