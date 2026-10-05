# M3 — Business & Product Skills Implementation Handoff

**Status:** Ready for implementation following approved M2.  
**Release:** Completes R1 together with M2.  
**Authority:** Repository copies of `SDLC-SKILL-ARCHITECTURE.md` revision 3, `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`, and the established M2 CLI/shared conventions. If these conflict with this handoff, surface the conflict before coding.

## Objective

Implement first-party, Markdown-driven Skills that transform a sparse idea into useful Business Requirements (BRD), Product Requirements (PRD), and traceable User Stories through adaptive, human-guided interrogation. Every Skill works independently: a PRD requires no BRD, and Stories may be created without upstream requirements (`covers: []`). Do not invent business decisions or introduce a new runtime, UI, or orchestration system.

## Deliverables

- `skill-library/shared/interview.md`: shared interviewing *method*, not a separate user-facing Skill or duplicated discipline template.
- `skill-library/skills/create-brd/SKILL.md` and supporting BRD section catalog, discovery questions and template.
- `skill-library/skills/create-prd/SKILL.md` and supporting PRD section catalog, discovery questions and template.
- `skill-library/skills/create-stories/SKILL.md` and supporting story/acceptance-criteria template.
- Tests and documented end-to-end acceptance fixtures. Extend M2 CLI only to fix a demonstrated gap; preserve its existing contract and add regression tests.
- Updated M3 checklist with evidence and a human-review gate.

## Shared execution contract — all three creating Skills

1. Invoke `sdlc init` safely; discover `map.md`, the target map, relevant existing documents, and references using the CLI and file reading.
2. Classify intent: new, revise, extend, or summarize. For new documents, run `find-overlaps` **before** `allocate-id`; show plausible overlaps and ask the user to choose new/revise/extend. Never auto-merge or silently duplicate.
3. Identify known facts, assumptions, proposals, unknowns and decisions. Read available source material before asking the user to repeat it.
4. Interview in batches of approximately **3–5 related high-value questions**. Adapt subsequent questions to answers and relevant document sections. Offer options when helpful, allow free-form responses, and accept `Unknown`, `TBD`, `Not applicable`. Do not fabricate specifics or force completion of every optional section.
5. Produce a substantive **Draft** after initial discovery. Present important assumptions, open questions and material tradeoffs for review; revise iteratively.
6. Before writing a **new** document, allocate its document ID via the CLI; allocate each requirement ID through `allocate-id --requirement DOC-ID`. Do not hand-calculate or reuse IDs. Keep stable IDs when editing existing requirements; retire removed requirements via the CLI.
7. Use required YAML metadata, ISO dates, correct `<ID>-<short-kebab-title>.md` filenames, document-specific section catalog and `References` sections with valid relative Markdown links. `purpose` is one sentence and maps copy it verbatim.
8. For material changes to an Approved document, change `status` to **In Review**, update `updated`, and explicitly inform the user. Skills never set Approved without a human approval decision. Do not conflate document `status` and Story `delivery_status`.
9. Invoke `update-map`, then `validate`; report structural errors, warnings, and coverage notices separately. Do not claim success when validation errors remain.
10. Keep CLI operations deterministic and inside the CLI; Skills own conversational analysis and drafting, not ID allocation, overlap scoring, map regeneration or validation algorithms.

## Shared interview guidance (`shared/interview.md`)

Specify how to: start from a one-sentence idea or from an existing document; infer only what is grounded in project material; prioritize missing material decisions; group questions by topic; skip already answered questions; carry unknowns forward visibly; distinguish requirement vs suggested option; summarize decisions between rounds; and obtain human feedback before writing. Include a lightweight example with two rounds and an explicit TBD. Avoid an exhaustive fixed questionnaire or requiring an external interview tool/UI.

## Skill-specific content

### `create-brd`

Audience: business stakeholders. A section catalog should cover business context/problem, objectives and desired outcomes, stakeholders, scope and exclusions, business requirements with stable `BR-NNN-RNNN` IDs, constraints/dependencies, success measures, risks/assumptions, open questions and References. Ask about the problem and outcomes before proposing a solution. Include only relevant optional sections. A BRD can stand alone without product or technical design.

### `create-prd`

Audience: product and delivery stakeholders. Catalog: product summary, target users and needs, user journeys/use cases, behavior and capabilities, MVP/in/out of scope, requirements with stable `PR-NNN-RNNN` IDs, observable acceptance expectations, constraints/dependencies, assumptions/open questions and References. If a BRD exists, offer it as a source and link it under `Derived From`; if none exists, proceed independently. Do not manufacture business requirements or treat a BRD as mandatory.

### `create-stories`

Audience: implementers and product reviewers. Derive scoped user value and behavior from a PRD or other supplied context; interrogate missing edge cases, business rules, negative paths and observable acceptance criteria. Produce appropriately sized `US-NNN` documents, with required `delivery_status` (initially `Not Started` unless a human establishes another valid state), and present `covers` key. When a Story satisfies documented requirements, populate `covers` with **specific existing requirement IDs**, not document IDs, and link every owning source document under `Derived From`. A standalone Story uses `covers: []`, explicitly acknowledged as a coverage notice rather than an error. Never invent requirement IDs or create a fake PRD solely to satisfy traceability. Do not set `Implemented` or `Verified` in M3.

## Revision behavior

Support revising existing BRD, PRD and Story documents without allocating replacement document IDs. Show material proposed changes, retain stable requirement IDs for edits to wording, allocate IDs only for added requirements, retire removed ones, and update affected source links/Story `covers` when reconciliation is required. A material edit to Approved changes status to In Review and is explained to the human. Preserve unrelated authored content; no per-edit version folders (Git is revision history).

## Acceptance tests and demonstrations

Use isolated fixture projects, including agent-run demonstrations, not only static inspection of Skill text:

1. Sparse idea → at least one adaptive interview round → substantive BRD with meaningful sections, `BR` requirement IDs, valid front matter and map entry. No invented user answers.
2. PRD **with** a BRD: discovers relevant source, adds a working `Derived From` link, uses substantive PR sections and allocates valid `PR` requirement IDs.
3. PRD **without** a BRD: completes independently and validates; no synthetic upstream document.
4. PRD → multiple Stories: each linked Story has valid `covers` requirement IDs, source links, distinct scope, and observable acceptance criteria; `validate` exits 0.
5. Standalone Story: present `covers: []`; `validate` emits `story-no-coverage` notice but exits 0 when no errors exist.
6. Ambiguous overlap: show CLI candidates **before** allocating an ID; demonstrate user selection of revise vs new. No silent duplication.
7. Unknown/TBD: preserve unanswered material questions visibly; do not fill them with plausible-looking assertions.
8. Material edit to Approved BRD/PRD/Story → In Review, updated date and explicit explanation; no silent reapproval.
9. Removed requirement → tombstone and reported retired references; a requirement move follows the architecture's reconciliation procedure.
10. After each creation/revision, maps reflect metadata and links, authored map text survives, and `validate` reports no structural errors.
11. Skills use the CLI rather than duplicating its algorithms; verify installation/discovery through both existing Codex and Claude Code adapters. Add regression tests for any M2 CLI changes.

## M3 exit and review report

Before claiming completion, run the full test suite under Python 3.11, present test command and pass/skip counts, plus paths to representative **generated** BRD, PRD and Story fixtures. Show at least one agent-run interrogation transcript or concise transcript excerpts for each discipline, one standalone PRD scenario, one overlap decision, and an Approved → In Review revision. Include final `validate` output for fixture projects, remaining TBDs, deviations and checklist state. A human must review actual generated BRD, PRD and Story content. **M3 + M2 = R1 only after this review and approval. Stop before M4.**

## Non-goals

No R2 technical Skills (`refine-stories`, design, implementation, test/verify), no R3 publishing/status, no Jira/GitHub synchronization, no new UI, mandatory BRD→PRD→Stories pipeline, event stream, database, third-party Skill dependency, or advanced AI recall.
