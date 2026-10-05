---
name: create-prd
description: Interview the user about a product and produce or revise a Product Requirements Document (PRD) as Markdown in the SDLC project (PR/ folder) with stable requirement IDs, references and an updated map. Use when the user wants to draft, write, extend, review or revise product requirements or a PRD, from a one-sentence idea or from an existing BRD. Works with or without a BRD.
---

# create-prd

Turns a product idea, or an existing BRD, into a **Draft** PRD in `PR/` through a short, adaptive interview, then keeps maps and validation clean. Audience: product and delivery stakeholders. The PRD says what the product does for its users, not the technical design.

Method: `../../shared/interview.md` (read it). Sections and rules: `references/section-catalog.md`. Questions to draw from: `references/discovery-questions.md`. Layout to write: `references/template.md`. Conventions: `../../shared/document-conventions.md`, `map-conventions.md`, `reference-conventions.md`. CLI: `python -m sdlc` (`../../shared/cli-contract.md`); if it fails with `No module named sdlc`, tell the user to install the library and stop. All commands run from the project root.

## Workflow

1. **Initialize and discover.** Run `python -m sdlc init` (safe to repeat). Read the root `map.md`, `PR/map.md` and `BR/map.md`; run `python -m sdlc list`. Read any material the user pointed to.
2. **Find optional sources.** Run `python -m sdlc list --category BR`. If BRDs exist, read the relevant one(s) and **offer** them as a source ("BR-001 covers X; should this PRD be derived from it?"). If none exist, or the user does not want one, proceed **independently**. A BRD is never required; never create one, or any placeholder upstream document, to satisfy this Skill.
3. **Classify the request:** *new* PRD, *revise*, *extend*, or *summarize*. Ask if unclear.
4. **Check overlap before creating anything new.** Run `python -m sdlc find-overlaps --category PR --title "<proposed title>" --purpose "<one sentence>"` (add `--covers <BR-ID or BR requirement IDs>` when the PRD derives from a BRD; that flag is only a search hint). If candidates come back: Present the candidates **exactly as the CLI returned them**: for each, its ID, title, `level`, `score` and every `reason`, copied from the command output (`--json` is easiest). Do not paraphrase, round, reorder, summarize or invent any ID, score or reason; if the command returns no candidates, say so. Then ask the user to choose **revise/extend the existing one** or **create a new one**. Never merge or duplicate silently. Do this **before** `allocate-id`.
   **Contextual overlap review (after the CLI check, before `allocate-id`).** The CLI score is lexical and can miss a document about the same concern in different words, so also review context yourself: run `python -m sdlc list --category PR`, read the titles and purposes and the summaries in `PR/map.md`, and open any document that looks close. Present anything you judge to be a conceptual overlap **separately**, under the heading **Conceptual overlaps (my judgement, not CLI-scored)**: the document ID, its title, and one sentence saying why, quoting its title or purpose. Never attach a score, percentage or level to these, never merge them into the CLI list, and never invent a similarity value; if you see none, say "No conceptual overlaps found." Do this even when the CLI returned no candidates. Whenever either kind of overlap exists, ask the human to choose **revise** the existing PRD, **relate** (create a new PRD that links the existing one under `### Related To`), or **create new** (independent). Do not allocate an ID until they choose; *revise* follows the revision workflow, *relate* and *create new* continue with a new document.
5. **Interview** per `shared/interview.md`: about 3–5 related questions per round; use what the BRD/source already answers; adapt to answers; accept `Unknown`/`TBD`/`Not applicable`; offer options as suggestions; do not invent users, behavior, numbers or decisions. After every round, give the **mandatory recap** (`shared/interview.md`) before asking the next questions.
6. **Draft and review.** After the first useful round, show a substantive draft (real sections built from the answers) with **assumptions, open questions/TBDs and material tradeoffs** listed. Revise until the user says to write it. Do not write files before that.
7. **Write (new document).**
   - `python -m sdlc allocate-id --category PR --title "<title>"` → use the returned `id` and `path`.
   - For every product requirement, `python -m sdlc allocate-id --requirement <PR-ID>` and use the returned ID; allocate only what will actually be written.
   - Fill `references/template.md` (see the section catalog): `status: Draft`, `created`/`updated` = today from `date +%F`, `purpose` = one sentence. Unresolved unknowns stay visible.
   - If derived from a BRD, add `- [BR-001 — Title](../BR/BR-001-slug.md)` under `### Derived From` (relative link; verify the file exists). Without one, keep `None identified.` If the user chose **relate** in the overlap review, also link that PRD under `### Related To`.
8. **Revise (existing document).** Read it fully; show the proposed material changes and get agreement; then edit in place, preserving unrelated content, keeping the document ID, filename and existing requirement IDs when wording changes. Added requirement → `allocate-id --requirement <PR-ID>`. Removed requirement → `python -m sdlc retire-id <PR-ID-Rnnn> [--replaced-by <ID>] --note "<why>"` and delete or mark its text *Retired*; then find affected Stories with `python -m sdlc references <ID>` and ask the user how their `covers` should change. Moving a requirement follows the reconciliation in `document-conventions.md`.
   - **Approved documents:** a material change (requirements, scope, MVP, acceptance, references) to an `Approved` PRD sets `status: In Review` and `updated` to today, and you **tell the user explicitly** that approval was reset and why. Typos/formatting are not material. Always update `updated` on any edit.
9. **Index and validate.** Run `python -m sdlc update-map`, then `python -m sdlc validate`. Report **errors, warnings and coverage notices separately**: a `requirement-uncovered` notice for a new PR requirement is expected until Stories exist (`create-stories`) and is not a failure. Fix errors you caused and re-run. Do not claim success while errors remain.
10. **Report.** Give the path, ID, status, requirement IDs, remaining TBDs, the validate summary, and mention that `create-stories` can turn these requirements into Stories. Approval is the human's decision.

## Rules

- Never set `status: Approved` on your own. Only if the user explicitly states that they approve the document may it be recorded as Approved.
- Never invent product decisions, users, metrics, dates or approvals. Unknown stays unknown.
- Never hand-calculate IDs, edit `.sdlc/ledger.md`, or edit the generated region of a `map.md`.
- Do not add technical design; do not restate or invent business requirements.
- Acceptance Expectations state only what the user established. Do not add behavior stronger than the requirements support (for example duplicate detection because a list is shared). An unresolved expectation is written as `TBD — <question>`, never as an assertion.
