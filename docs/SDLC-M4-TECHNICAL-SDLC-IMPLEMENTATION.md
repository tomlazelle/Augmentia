# M4 — Technical SDLC Implementation Handoff (R2)

**Status:** Proposed for human review; implementation not yet authorized  
**Authority:** Repository `docs/SDLC-SKILL-ARCHITECTURE.md` (approved revision, including subsequent approved amendments), then `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`. This document scopes M4; resolve conflicts explicitly rather than silently replacing approved R1 behavior.

## Objective

Extend the first-party Markdown-first Skill library so a Story can move from **Ready → In Progress → Implemented → Verified**, with traceable technical artifacts, repository-aware work, and verification based on actual executions. Preserve the CLI as the deterministic authority for IDs, maps, links and structural validation. Do not build a runtime/orchestrator, database, UI, publisher, or automatic approval system.

## Before coding: R2 contract review

Review and document the following in the architecture and conventions, obtaining human approval for any materially new semantics:

- Existing document `status` (Draft / In Review / Approved / Superseded) remains distinct from Story `delivery_status` (Not Started / Ready / In Progress / Implemented / Verified).
- Only `implement-story` may set `Implemented`; only `verify-story` may set `Verified`, and only when supported by recorded, actual results. No agent may infer test success.
- Define explicit allowed transitions, prerequisites and behavior for rework after `Implemented` or `Verified` (e.g. material changes invalidate prior verification); never silently retain a stale Verified state.
- Define minimal artifact templates and references for `DES-NNN`, `PLAN-NNN`, `TEST-NNN`, and optional `RES-NNN` research. Keep optional artifacts optional: a standalone Story must remain actionable.
- Specify the format for recording verification commands, timestamps, observed exit codes/results, failures, environment and relevant evidence links. Distinguish **not run**, **blocked**, **failed** and **passed**.
- Agree how a reviewer reports findings and whether a review blocks subsequent steps. Human approval remains human approval.

Do not introduce a new CLI command just to implement agent reasoning. Extend the existing validator only for deterministic schema/link/ID checks actually required by R2.

## Implementation sequence

### 1. Shared technical conventions and templates
- Add focused shared guidance for repository inspection, traceability, status transitions, evidence and revision rules. Reuse `shared/interview.md` for focused clarification rounds, recap, explicit TBDs, and no invented facts.
- Add templates and section catalogs for Design, Implementation Plan and Test Plan. Include source Story IDs, applicable PR requirement IDs, relative links, decisions/alternatives, assumptions, risks and unresolved questions.
- Technical Skills must inspect the actual repository, current code/tests and linked documents before making a proposal. When source code or an execution environment is unavailable, report that limitation and do not pretend to have inspected or tested it.
- Preserve the R1 overlap workflow: deterministic CLI check followed by separately labeled contextual review, with human revise/relate/create-new decision before allocating a document ID.

### 2. `refine-stories`
- Inspect selected Story, linked PRD/requirements, other Stories, code and existing tests when present.
- Ask only targeted missing questions; distinguish decided behavior from TBD acceptance behavior. Do not turn TBD outcomes into executable Given/When/Then.
- Produce a clear, bounded Story with verifiable acceptance criteria, dependencies and relevant edge cases; explain what is needed for `Ready`.
- Do not change approval or delivery state merely because the agent believes a Story is ready. Follow the approved transition and human decision rules.

### 3. `create-design` (`DES-NNN`)
- Create or revise a technical design tied to one or more source Stories, with relevant architecture/context, options, trade-offs, interfaces/data flow, dependencies, migration/security/operational considerations as applicable, and open decisions.
- Avoid invented implementation details and unnecessary sections for small changes. Use CLI allocation and map regeneration. Preserve authored text outside generated map regions.
- A design is not a prerequisite for every Story unless the human/project explicitly requires one.

### 4. `plan-implementation` (`PLAN-NNN`)
- Derive an actionable sequence from selected Stories and any design, after inspecting code/tests.
- Specify files/components likely affected (as proposals, not facts if unverified), dependencies, steps, risks, acceptance-to-test mapping and validation commands.
- Allow planning without a Design when appropriate. Require human clarification on material uncertainty rather than fabricate a decision.

### 5. `implement-story`
- Select and re-read the Story, its `covers` requirements and applicable plan/design; inspect repository state and existing conventions.
- Obtain authorization to modify code, keep changes scoped, and record what was actually changed. Avoid claiming completion based on generated code alone.
- Apply the approved `delivery_status` transitions. Only this Skill sets `Implemented`, when implementation work is complete under the agreed contract. Do not set `Verified`.
- Capture tests executed during implementation with observed results; never invent a pass or claim an unrun command succeeded.

### 6. `review-implementation`
- Review actual diff and relevant Story/requirements, design, plan and tests; distinguish verified observations from potential concerns.
- Report actionable findings with severity, location, rationale, and unresolved questions. Identify missing coverage and divergences from acceptance criteria.
- Do not silently change code or mark Verified. Document whether the review is complete, blocked, or requires rework.

### 7. `create-test-plan` (`TEST-NNN`)
- Map each decided acceptance criterion to test scenarios, method (automated/manual), setup, expected result and evidence to capture.
- Put TBD acceptance behavior in an unresolved section; do not turn it into a test with an invented expected result.
- Include relevant failure, boundary and regression cases proportionate to the Story. Use the established ID/map/reference workflow.

### 8. `verify-story`
- Inspect the current implementation and applicable Story/requirements/test plan; run available relevant commands/tests when authorized and technically possible.
- Record actual command, environment, execution time, exit code, observed outcome and evidence path/log reference. Manual checks must be explicitly identified with who performed them and what was observed.
- Report failures, blocked checks, skipped/not-run tests and residual risk. **Set `Verified` only when the approved verification criteria are met by actual results.** Otherwise retain/revert to the appropriate non-Verified state and report why.
- If implementation or acceptance criteria materially change after verification, apply the approved rework/invalidation rule.

### 9. CLI and integration
- Validate uniqueness, filenames, front matter and links for DES/PLAN/RES/TEST; check their maps and references without special-casing `.sdlc/`.
- Keep the established `--root`, `--json`, exit codes, idempotency, coverage-notice and `covers` contracts.
- Install/link the seven new centrally maintained Skills via the existing Codex and Claude Code adapters; no forked copies.
- Keep `AGENTS.md` and `CLAUDE.md` centrally packaged and create-if-missing on `init`; do not overwrite user instructions.

## Required acceptance scenarios

Use isolated fixture repositories and preserve representative generated artifacts and agent transcripts.

1. All R1 regression tests remain green on Python 3.11, including opt-in installation tests.
2. `refine-stories` improves an ambiguous Story without inventing requirements, outcomes or human approval.
3. Design, plan and test-plan documents allocate unique DES/PLAN/TEST IDs, link source Stories/requirements correctly, update maps, and pass `validate`. Exercise optional RES where present.
4. A Story can be refined/planned and implemented **without a BRD or mandatory design**, preserving independent entry.
5. Technical proposals demonstrably inspect repository files and existing tests rather than making generic assumptions.
6. Implemented is set only by `implement-story`; Verified only by `verify-story`. Document status and delivery status remain separate.
7. A successful end-to-end Ready → In Progress → Implemented → Verified scenario includes actual code changes and real executed verification evidence.
8. Failed tests, unrun tests, unavailable tools and TBD acceptance outcomes do **not** produce a false Verified state; diagnostics identify what remains.
9. Material rework after verification follows the approved invalidation rule; prior evidence remains attributable rather than misrepresented as current.
10. Review findings reference actual changed code and linked acceptance criteria; review alone never asserts verification.
11. `update-map` is a no-op on current generated fixtures, and `validate` reports zero structural errors; seed broken links, duplicate technical IDs and stale maps to prove detection.
12. Both adapters discover all new Skills. Include a representative real-agent execution for Claude Code and Codex, and retain transcripts. If a run cannot be performed, mark it explicitly unverified rather than silently treating a static test as equivalent.

## M4 deliverables and exit gate

Deliver the seven `SKILL.md` files (and proportionate references/templates), reviewed R2 contract amendments, minimal shared technical conventions, any justified CLI/validator changes, regression and fixture tests, representative generated DES/PLAN/TEST and implementation/review/verification evidence, updated checklist, and `docs/SDLC-M4-EVIDENCE.md`.

**Checklist exit criterion:** A Story goes from Ready to Verified through R2 Skills on a fixture project, with accurate `delivery_status`, valid links, passing `validate`, and verification traceable to real executions.

At the M4 checkpoint report: exact Python 3.11 test commands/counts; actual agent runs and limitations; representative generated artifacts; state-transition evidence; actual pass/fail/blocked verification examples; deviations; and unchecked checklist items. **Do not mark M4 approved or begin M5. Stop for human review.**

## Explicit non-goals

No GitHub/Jira publishing or status-reporting Skill (M5), `pipx` release work or final cross-agent matrix (M6), new event stream, mandatory orchestration service, semantic embeddings, database, UI, or advanced AI memory. Maintain the greenfield first-party Skill architecture.
