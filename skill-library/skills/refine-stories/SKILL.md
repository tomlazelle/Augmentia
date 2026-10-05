---
name: refine-stories
description: Refine an existing User Story so it is clear, bounded and ready for implementation — inspect the Story, its PRD/requirements, neighboring Stories and the repository's code and tests, ask targeted questions, and produce verifiable Given/When/Then acceptance criteria with undecided behavior kept as TBD. Use when the user asks to refine, clarify, tighten, groom or check readiness of a Story. Never sets delivery state on its own.
---

# refine-stories

Improves a Story that already exists in `Stories/` (to create new Stories use `create-stories`). Audience: implementers and product reviewers.

Method and rules: `../../shared/technical-conventions.md` (read it) and `../../shared/interview.md`. Questions to draw from: `references/discovery-questions.md`. Readiness: `references/readiness-checklist.md`. Story layout and rules: `../create-stories/references/template.md` and `section-catalog.md`. CLI: `sdlc` (`../../shared/cli-contract.md`); if it fails with `command not found: sdlc`, tell the user to install the library and stop. Commands run from the project root.

## Workflow

1. **Initialize and discover.** Run `sdlc init` (safe to repeat). Read the root `map.md` and `Stories/map.md`; run `sdlc list --category US` and agree with the user which Story to refine. Read it **in full**.
2. **Gather context, do not guess.** Read the requirement documents in its `covers` and `Derived From` (`sdlc references <US-ID>`), the neighboring Stories, and the **actual code and tests** the Story touches (open them; cite what you opened). If the repository or a tool is unavailable, say so.
3. **Analyze.** Separate what is *decided* (stated in the Story, requirements, or by the user) from what is ambiguous or *TBD*. List the concrete gaps: unclear behavior, missing negative paths, criteria that are not observable, scope that spills into another Story, unnamed dependencies. Check the Story against `references/readiness-checklist.md`.
4. **Ask targeted questions** per `shared/interview.md`: about 3–5 related questions per round, only for real gaps; skip anything the documents or code answer; accept `Unknown`/`TBD`/`Not applicable`; offer options as suggestions. After every round give the **mandatory recap** before the next questions. Do not invent requirements, outcomes, rules or approvals. If the user identifies behavior missing from the PRD, suggest `create-prd` to add a requirement; do not add requirement IDs here. If the Story should be split, propose it and hand new Stories to `create-stories`.
5. **Propose the refinement.** Show the changes (clearer Story statement, bounded scope, verifiable acceptance criteria, edge cases with decided outcomes, dependencies) with **assumptions and open TBDs** listed. An acceptance criterion is verifiable Given/When/Then with a **decided, observable** outcome; an unknown outcome is a `- **TBD** — …` bullet under `### Unresolved Acceptance Behavior (TBD)`, never `then … TBD`. Get agreement before editing.
6. **Edit in place** after agreement: keep the Story's ID, filename and history-relevant content, preserve unrelated text, update `updated` (today, `date +%F`). Keep `covers` truthful: only existing requirement IDs, with each owning document linked under `### Derived From`.
   - **Approved Story:** a material change (scope, acceptance criteria, `covers`, references) sets document `status: In Review`; tell the user explicitly.
   - **Invalidation:** if the Story's `delivery_status` is `In Progress`, `Implemented` or `Verified`, a material change sets it back to `Ready` (`technical-conventions.md` §3); tell the user, and mark every still-current `### VR-n` run for this Story (find them with `sdlc references <US-ID>`; they live in TEST documents) with `- **Superseded:** yes — Story changed <date>`; never edit or delete their recorded results. Do not otherwise touch `delivery_status`.
7. **Readiness.** Report exactly what is still needed for `Ready`, using the checklist. **Never set `delivery_status: Ready` because you think the Story is ready.** Only if the user explicitly declares it ready and the checklist holds (or they accept a named exception) record `Ready`; you never set `In Progress`, `Implemented` or `Verified`. Approval (`status`) is a separate human decision.
8. **Index and validate.** Run `sdlc update-map`, then `sdlc validate`. Report **errors, warnings and coverage notices separately** (a standalone Story's `story-no-coverage` is a notice, not an error). Fix errors you caused and re-run.
9. **Report.** Summarize what changed, what remains TBD, the readiness verdict and the validate summary.

## Rules

- Never set `status: Approved` on your own; only if the user explicitly states that they approve the document.
- Never invent requirements, requirement IDs, acceptance outcomes or approvals; never present an unresolved outcome as an executable criterion.
- Never hand-calculate IDs, edit `.sdlc/ledger.md`, or edit the generated region of a `map.md`.
- A Story stays actionable without a BRD, PRD, Design or Plan: do not create any of them to make refinement "complete".
