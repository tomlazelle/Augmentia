---
name: sdlc-validate
description: Validate the SDLC Markdown project — structure, front matter, document/requirement IDs, ledger, relative links, story-to-requirement traceability and map freshness — and explain any problems. Use when the user asks to check, lint or validate the SDLC documents, after a git merge, or after documents are moved, renamed or deleted.
---

# sdlc-validate

Runs the deterministic validator and helps the user act on the result. CLI: `python -m sdlc` (contract and diagnostic codes: `../../shared/cli-contract.md`). If the project is not initialized, suggest `sdlc-init` and stop.

## Steps

1. Run `python -m sdlc validate` (use `--json` when you need to group or count diagnostics).
2. Report the summary first (errors / warnings / notices), then the details grouped by severity. For each diagnostic give the file, the ID, and the reason in plain words.
3. Interpret by severity:
   - **error** — structural problem; exit code 1. Explain the fix.
   - **warning** — worth fixing, does not fail validation (for example an ID allocated but never used, or a document missing from the ledger).
   - **notice** — coverage information only (standalone Stories with `covers: []`, requirements no Story covers). Never present notices as failures.
4. Offer fixes; apply only what the user agrees to:
   - `stale-map` or missing map: run `python -m sdlc update-map`. Never change document content to make a map match.
   - `duplicate-id` after a merge: show every file involved and ask the user which document keeps the ID. The other document gets a fresh ID from `allocate-id`: rename its file, update its front matter `id`, re-identify any requirements it declares (see `../../shared/document-conventions.md`), and update links that point to it. Do not decide which one keeps the ID yourself.
   - broken links or bad references: propose the corrected relative path; edit only after confirmation.
   - retired-reference: point to the replacement named in the message, or ask the user.
5. Re-run `validate` after any fix and report the new summary.

## Rules

- Validation is read-only. Do not edit `.sdlc/ledger.md` or `.sdlc/config.md` by hand.
- Do not mark documents `Approved` or change statuses to silence a diagnostic.
