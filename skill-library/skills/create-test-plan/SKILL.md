---
name: create-test-plan
description: Create or revise a Test Plan (TEST-NNN) for a Story in the SDLC project (Artifacts/tests/) — map each decided acceptance criterion to automated or manual test scenarios with setup, expected result and evidence, keep undecided (TBD) behavior separate, and provide the Verification Runs section used by verify-story. Use when the user wants a test plan or test scenarios for a Story.
---

# create-test-plan

Produces a **Draft** Test Plan (`TEST-NNN`) whose scenarios each reference a decided acceptance criterion (`AC-n`). It plans tests; it never records or claims results. Audience: implementers, reviewers and whoever verifies the Story.

Method and rules: `../../shared/technical-conventions.md` (read it) and `../../shared/interview.md`. Sections and rules: `references/section-catalog.md`. Questions to draw from: `references/discovery-questions.md`. Layout to write: `references/template.md`. Conventions: `../../shared/document-conventions.md`, `map-conventions.md`, `reference-conventions.md`. CLI: `python -m sdlc` (`../../shared/cli-contract.md`); if it fails with `No module named sdlc`, tell the user to install the library and stop. All commands run from the project root.

## Workflow

1. **Initialize and discover.** Run `python -m sdlc init` (safe to repeat). Read the root `map.md` and `Artifacts/map.md` (and `Artifacts/tests/map.md` if it exists). Run `python -m sdlc list --category US`, pick the source Story or Stories with the user, and read them **in full** together with the requirement documents they cover. `python -m sdlc references <US-ID>` shows existing artifacts already linked to a Story.
2. **Inspect the repository** as `technical-conventions.md` §7 requires: open the code, tests and conventions that matter for these Stories before proposing anything. Record what you opened and what you could not inspect; if there is no repository or a tool is unavailable, say so and do not pretend.
3. **Classify the request:** *new* Test Plan, *revise*, *extend*, or *summarize*. Ask if unclear.
4. **Check overlap before creating anything new.** Run `python -m sdlc find-overlaps --category TEST --title "<proposed title>" --purpose "<one sentence>" --covers <source Story IDs>` (`--covers` is only a search hint). If candidates come back: present the candidates **exactly as the CLI returned them**: for each, its ID, title, `level`, `score` and every `reason`, copied from the command output (`--json` is easiest). Do not paraphrase, round, reorder, summarize or invent any ID, score or reason; if the command returns no candidates, say so.
   **Contextual overlap review (after the CLI check, before `allocate-id`).** The CLI score is lexical and can miss a document about the same concern in different words, so also review context yourself: run `python -m sdlc list --category TEST`, read the titles and purposes and the summaries in `Artifacts/tests/map.md`, and open any document that looks close. Present anything you judge to be a conceptual overlap **separately**, under the heading **Conceptual overlaps (my judgement, not CLI-scored)**: the document ID, its title, and one sentence saying why, quoting its title or purpose. Never attach a score, percentage or level to these, never merge them into the CLI list, and never invent a similarity value; if you see none, say "No conceptual overlaps found." Do this even when the CLI returned no candidates. Whenever either kind of overlap exists, ask the human to choose **revise** the existing Test Plan, **relate** (create a new Test Plan that links the existing one under `### Related To`), or **create new** (independent). Do not allocate an ID until they choose; *revise* follows the revision workflow, *relate* and *create new* continue with a new document.
5. **Clarify** per `shared/interview.md`: about 3–5 related questions per round, only what the Story, requirements and repository do not settle; skip answered questions; accept `Unknown`/`TBD`/`Not applicable`; offer options as suggestions. After every round, give the **mandatory recap** before asking the next questions. Do not invent decisions, code details or facts.
6. **Draft and review.** Show a substantive draft (built from the Story, the requirements and what you inspected) with **assumptions, open questions/TBDs and material tradeoffs** listed. Revise until the user says to write it. Do not write files before that.
7. **Write (new document).**
   - First use of this folder: `python -m sdlc create-dir --artifact tests` (safe to repeat).
   - `python -m sdlc allocate-id --category TEST --title "<title>"` → use the returned `id` and `path`.
   - Fill `references/template.md` (layout and rules in the section catalog): `status: Draft`, `created`/`updated` = today from `date +%F`, `purpose` = one sentence. Under `### Derived From` link **every source Story** with a valid relative link and cite the requirement IDs it serves. If the user chose **relate** in the overlap review, link that document under `### Related To`.
   - Number scenarios `TS-n`, each pointing at an `AC-n` (the position of the criterion in the Story's numbered list). Put undecided behavior under *Unresolved Acceptance Behavior (TBD)* with no expected result. Leave `## Verification Runs` as `None recorded.`. If the Story has no decided numbered criteria, stop and suggest `refine-stories`.
8. **Revise (existing document).** Read it fully; show the proposed material changes and get agreement; edit in place, keeping the document ID and filename and preserving unrelated content. **Approved documents:** a material change to an `Approved` Test Plan sets `status: In Review` and `updated` to today, and you **tell the user explicitly**; typos and formatting are not material. Always update `updated`. A material change to an Approved Test Plan includes changing scenarios, expected results or criteria mapping; appending verification runs is not material and is done by `verify-story`.
9. **Index and validate.** Run `python -m sdlc update-map`, then `python -m sdlc validate`. Report **errors, warnings and coverage notices separately**; fix errors you caused and re-run. Do not claim success while errors remain.
10. **Report.** Give the path, ID, status, the Stories it is derived from, what was inspected versus not, the remaining TBDs and the validate summary. Approval is the human's decision.

## Rules

- Never set `status: Approved` on your own; only if the user explicitly states that they approve the document.
- Never change a Story's `delivery_status`. Never write or edit `Verification Runs` entries, results or claims of passing here.
- Never invent code details, file contents, test results or requirement IDs; unknown stays unknown, and unverified statements are labeled proposals.
- Never hand-calculate IDs, edit `.sdlc/ledger.md`, or edit the generated region of a `map.md`.
- Keep failure, boundary and regression cases proportionate to the Story.
