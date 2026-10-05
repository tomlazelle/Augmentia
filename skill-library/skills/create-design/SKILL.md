---
name: create-design
description: Create or revise a technical Design document (DES-NNN) for one or more Stories in the SDLC project (Artifacts/design/), grounded in inspection of the actual repository, with options, trade-offs, decisions, risks and open decisions, and optional supporting Research (RES-NNN). Use when the user wants a design, technical approach, architecture note or research note for a Story. A design is optional; Stories do not require one.
---

# create-design

Produces a **Draft** Design (`DES-NNN`) for one or more Stories after inspecting the code base, and optionally a supporting Research note (`RES-NNN`, `references/research-template.md`, `Artifacts/research/`, allocated with `--category RES` through the same overlap workflow). Audience: engineers implementing and reviewing the Story.

Method and rules: `../../shared/technical-conventions.md` (read it) and `../../shared/interview.md`. Sections and rules: `references/section-catalog.md`. Questions to draw from: `references/discovery-questions.md`. Layout to write: `references/template.md`. Conventions: `../../shared/document-conventions.md`, `map-conventions.md`, `reference-conventions.md`. CLI: `sdlc` (`../../shared/cli-contract.md`); if it fails with `command not found: sdlc`, tell the user to install the library and stop. All commands run from the project root.

## Workflow

1. **Initialize and discover.** Run `sdlc init` (safe to repeat). Read the root `map.md` and `Artifacts/map.md` (and `Artifacts/design/map.md` if it exists). Run `sdlc list --category US`, pick the source Story or Stories with the user, and read them **in full** together with the requirement documents they cover. `sdlc references <US-ID>` shows existing artifacts already linked to a Story.
2. **Inspect the repository** as `technical-conventions.md` §7 requires: open the code, tests and conventions that matter for these Stories before proposing anything. Record what you opened and what you could not inspect; if there is no repository or a tool is unavailable, say so and do not pretend.
3. **Classify the request:** *new* Design, *revise*, *extend*, or *summarize*. Ask if unclear.
4. **Check overlap before creating anything new.** Run `sdlc find-overlaps --category DES --title "<proposed title>" --purpose "<one sentence>" --covers <source Story IDs>` (`--covers` is only a search hint). If candidates come back: present the candidates **exactly as the CLI returned them**: for each, its ID, title, `level`, `score` and every `reason`, copied from the command output (`--json` is easiest). Do not paraphrase, round, reorder, summarize or invent any ID, score or reason; if the command returns no candidates, say so.
   **Contextual overlap review (after the CLI check, before `allocate-id`).** The CLI score is lexical and can miss a document about the same concern in different words, so also review context yourself: run `sdlc list --category DES`, read the titles and purposes and the summaries in `Artifacts/design/map.md`, and open any document that looks close. Present anything you judge to be a conceptual overlap **separately**, under the heading **Conceptual overlaps (my judgement, not CLI-scored)**: the document ID, its title, and one sentence saying why, quoting its title or purpose. Never attach a score, percentage or level to these, never merge them into the CLI list, and never invent a similarity value; if you see none, say "No conceptual overlaps found." Do this even when the CLI returned no candidates. Whenever either kind of overlap exists, ask the human to choose **revise** the existing Design, **relate** (create a new Design that links the existing one under `### Related To`), or **create new** (independent). Do not allocate an ID until they choose; *revise* follows the revision workflow, *relate* and *create new* continue with a new document.
5. **Clarify** per `shared/interview.md`: about 3–5 related questions per round, only what the Story, requirements and repository do not settle; skip answered questions; accept `Unknown`/`TBD`/`Not applicable`; offer options as suggestions. After every round, give the **mandatory recap** before asking the next questions. Do not invent decisions, code details or facts.
6. **Draft and review.** Show a substantive draft (built from the Story, the requirements and what you inspected) with **assumptions, open questions/TBDs and material tradeoffs** listed. Revise until the user says to write it. Do not write files before that.
7. **Write (new document).**
   - First use of this folder: `sdlc create-dir --artifact design` (safe to repeat).
   - `sdlc allocate-id --category DES --title "<title>"` → use the returned `id` and `path`.
   - Fill `references/template.md` (layout and rules in the section catalog): `status: Draft`, `created`/`updated` = today from `date +%F`, `purpose` = one sentence. Under `### Derived From` link **every source Story** with a valid relative link and cite the requirement IDs it serves. If the user chose **relate** in the overlap review, link that document under `### Related To`.
   - If the design needs evidence, offer an optional Research note (`create-dir --artifact research`, then `allocate-id --category RES`, template `references/research-template.md`) and link it under `### Supporting Artifacts`. Never invent sources.
8. **Revise (existing document).** Read it fully; show the proposed material changes and get agreement; edit in place, keeping the document ID and filename and preserving unrelated content. **Approved documents:** a material change to an `Approved` Design sets `status: In Review` and `updated` to today, and you **tell the user explicitly**; typos and formatting are not material. Always update `updated`. A material change to an Approved Design includes changes to the decision, options, interfaces or risks.
9. **Index and validate.** Run `sdlc update-map`, then `sdlc validate`. Report **errors, warnings and coverage notices separately**; fix errors you caused and re-run. Do not claim success while errors remain.
10. **Report.** Give the path, ID, status, the Stories it is derived from, what was inspected versus not, the remaining TBDs and the validate summary. Approval is the human's decision.

## Rules

- Never set `status: Approved` on your own; only if the user explicitly states that they approve the document.
- Never change a Story's `delivery_status`. A Design is never required for a Story; do not imply otherwise.
- Never invent code details, file contents, test results or requirement IDs; unknown stays unknown, and unverified statements are labeled proposals.
- Never hand-calculate IDs, edit `.sdlc/ledger.md`, or edit the generated region of a `map.md`.
- Keep the design proportionate: small changes get a short design; omit optional sections that do not apply.
