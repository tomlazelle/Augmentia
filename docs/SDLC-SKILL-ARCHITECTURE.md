# SDLC Skill Library — Architecture & Conventions

**Milestone:** M1 | **Revision:** 3 (+ post-M3 hardening, see checklist) | **Status:** Conditionally approved; three corrections incorporated (greenfield) | **Purpose:** First-party, Markdown-first SDLC Skill architecture.

## 1. Why this is being done

This is a new, greenfield project. The direction is simple: a human invokes a task-specific AI Skill, answers relevant questions, and receives useful, interconnected Markdown documents inside their Git repository. No third-party Skill library is a dependency, and no UI is required.

The core requirement is continuity: each Skill must discover existing work, read related documents, avoid duplicates, preserve relative references, and update navigable indexes. Git handles version history. Versioned folder trees, attempt records, and advanced AI recall are explicitly deferred.

## 2. Principles

1. Human-facing SDLC documents, indexes, templates and reports use Markdown with YAML front matter.
2. Files are usable without a custom UI. Skills are independently invocable; there is no mandatory BRD → PRD → Stories sequence.
3. Read before write. Ask about ambiguity; do not fabricate business decisions, approvals, KPIs or test results.
4. Each managed content directory has `map.md`; each authored document has a stable ID and working relative links. `.sdlc/` is an internal configuration directory and is exempt (§3).
5. Documents own their content and declared references; maps are maintained, regenerable indexes, never a separate source of truth.
6. Deterministic work (initialization, ID allocation, index updates, overlap search, validation) is performed by the first-party `sdlc` Python CLI (§9). Skill prompts invoke it and must not re-implement filesystem algorithms.
7. Approval is a human-declared status. There is no approval workflow engine.
8. Publishing to external services requires a preview and explicit human confirmation.
9. This is a new repository. There is no legacy Runtime, Bridge, Visual Workspace, or migration/compatibility requirement anywhere in this design.

## 3. Project layout (in a user's repository)

```text
project-root/
├── AGENTS.md        # created by init if missing (narrow SDLC guidance for agents)
├── CLAUDE.md        # created by init if missing
├── map.md
├── BR/
│   ├── map.md
│   └── BR-001-business-overview.md
├── PR/
│   ├── map.md
│   └── PR-001-product-overview.md
├── Stories/
│   ├── map.md
│   └── US-001-register-user.md
├── Artifacts/
│   ├── map.md
│   ├── design/      # created on first use, with its own map.md
│   ├── plans/       # created on first use
│   ├── research/    # created on first use
│   └── tests/       # created on first use
└── .sdlc/
    ├── config.md    # project configuration (YAML front matter)
    └── ledger.md    # ID allocation ledger and tombstones
```

`.sdlc/` is an internal configuration directory maintained by the CLI. It has no `map.md`, is not listed in any map, and is exempt from the map requirement, ID assignment and document front matter rules; the validator does not require or generate maps for it.

`AGENTS.md` and `CLAUDE.md` are copied from the CLI's packaged templates by `sdlc init` only if missing; existing instruction files are never modified. They direct agents to invoke or consult the creating Skill (and its revision rules) when modifying SDLC-governed documents; they add no mechanism and are outside the map and validation rules.

`sdlc init` creates only `map.md`, `BR/`, `PR/`, `Stories/`, `Artifacts/`, `.sdlc/` and, if missing, the two instruction files. The `Artifacts/` subdirectories are created (with a `map.md`) by the first command that needs them and are linked from `Artifacts/map.md`.

Skill definitions live centrally in the SDLC tool's source repository (§9). Project installation is agent-specific linking or installation following each agent's discovery convention; independently maintained copies are not placed into every project.

## 4. Document conventions

### 4.1 IDs and filenames

| Category | Document ID | Example filename | Directory |
|---|---|---|---|
| Business Requirements | `BR-NNN` | `BR-001-business-overview.md` | `BR/` |
| Product Requirements | `PR-NNN` | `PR-001-product-overview.md` | `PR/` |
| User Story | `US-NNN` | `US-001-register-user.md` | `Stories/` |
| Design | `DES-NNN` | `DES-001-authentication.md` | `Artifacts/design/` |
| Plan | `PLAN-NNN` | `PLAN-001-auth-rollout.md` | `Artifacts/plans/` |
| Research | `RES-NNN` | `RES-001-oauth-providers.md` | `Artifacts/research/` |
| Test plan/report | `TEST-NNN` | `TEST-001-registration.md` | `Artifacts/tests/` |

- Filenames are `<ID>-<short-kebab-title>.md`. Do not renumber because ordering changes.
- Uniqueness is per category. The validator checks uniqueness for every category above.

### 4.2 Front matter (required)

Every authored document begins with YAML front matter, then a descriptive title heading.

```markdown
---
id: PR-001
title: Product Overview
purpose: Core product expectations for the first release.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# PR-001 — Product Overview
```

Required for all authored documents: `id`, `title`, `purpose` (one sentence, used verbatim by maps), `status`, `created`, `updated`. Dates are ISO `YYYY-MM-DD`; do not invent historical dates.

Additional fields for Stories only:

```yaml
delivery_status: Not Started     # Not Started | Ready | In Progress | Implemented | Verified
covers: [PR-001-R003]            # requirement IDs this story satisfies; [] for a standalone Story
```

`covers` is required but may be an empty list (`covers: []`) for a standalone Story that is not derived from a documented requirement. The key must be present.

`map.md` files and `.sdlc/` files are not authored documents and have no ID. `.sdlc/config.md` uses front matter for configuration values; its minimal schema is in §14.

### 4.3 Status model

- **Document `status`:** Draft, In Review, Approved, Superseded. Approval requires an actual human decision; Skills never set Approved on their own.
- **Story `delivery_status`:** Not Started, Ready, In Progress, Implemented, Verified. This is independent of document `status`. `Implemented` and `Verified` are set only by `implement-story` and `verify-story` (R2), and `Verified` only from actual reported results.
- R2 adds explicit `delivery_status` transitions, rework/invalidation and evidence rules: see §15 and `skill-library/shared/technical-conventions.md`.
- **Material edits to an Approved document** (any change to requirements, scope, acceptance criteria or references beyond typo/formatting) return `status` to In Review and update `updated`. The editing Skill must say so to the user. Approval is never silently retained.
- Git provides revision history. There are no per-edit `vX.X.X` directories.

### 4.4 Requirement IDs

- Requirement IDs are document-scoped: `BR-001-R001`, `PR-001-R003`. They are declared in the owning document as a list item or heading that begins with the bold ID, e.g. `- **PR-001-R003** — Users can reset their password.`
- Requirement IDs are stable and never recycled. Editing a requirement's wording preserves its ID.
- Removing a requirement retires its ID (tombstone in the ledger) rather than deleting the number; the text may be kept and marked *Retired*.
- **Moving a requirement to another document** is a reconciliation, not a rename: the requirement receives a new ID in the target, the old ID is retired with a pointer to the new one, and all `covers` values and prose references are updated. The validator reports references to retired IDs.

### 4.5 ID ledger

`.sdlc/ledger.md` is a Markdown table (ID, kind, state `Allocated` | `Retired`, date, note) maintained only by the CLI. Allocation takes the highest of (ledger, files on disk) plus one, so an ID is not reissued if its highest-numbered file is deleted. Allocation is **monotonic per checkout, not collision-proof across branches**: two branches may allocate the same ID. `sdlc validate` must detect duplicate IDs after a merge and report both files; resolution (retiring/renumbering one) is a human-approved action.

### 4.6 References

```markdown
## References

### Derived From
- [BR-001 — Business Overview](../BR/BR-001-business-overview.md)

### Related To
- None identified.

### Supporting Artifacts
- None identified.
```

`Derived From` identifies source requirements; `Related To` identifies peers or relevant downstream documents; `Supporting Artifacts` identifies research, design or evidence. A document may have no upstream links; never manufacture a BRD merely because a PRD was requested. All paths are relative to the containing file. On rename/move, update affected links and maps. Incoming references are derived by scanning (`sdlc references <ID>`); redundant backlinks are not required.

### 4.7 Traceability

Stories that derive from requirements must cite the specific requirement IDs they satisfy in `covers`, **and** link the source documents in `Derived From` with relative links. The validator checks that every ID in `covers` exists, is not retired, and belongs to a document that the story links to. A standalone Story with `covers: []` is valid and does not produce a validation error; instead the validator reports it separately as a **coverage notice** (Stories with no requirement coverage), alongside PR requirements that no Story covers (R1; BR requirements are expected to be covered through PRDs, so they produce no notice). Story front matter `covers` holds requirement IDs only; document IDs are accepted only as search hints by `find-overlaps --covers`. Coverage notices are informational and do not affect the `validate` exit code; `sdlc-status` (R3) surfaces them. Other documents may cite requirement IDs in prose or in a `Derived From` line; the validator also checks any requirement ID that appears in a reference list.

## 5. map.md contract

Every map answers: what is this folder for, what documents exist, what is each for, and how do they relate.

- Root `map.md`: project title/summary, links to `BR/map.md`, `PR/map.md`, `Stories/map.md`, `Artifacts/map.md`, optional open questions.
- Directory `map.md`: heading and one-paragraph purpose; a table (ID, linked title, purpose, status); relevant cross-document relationships with working relative links; subdirectory map links where applicable; optional open questions.
- `Artifacts/` sub-maps follow the same contract.

The **purpose** column is copied from each document's `purpose` metadata, and title/status from `title`/`status`; nothing is authored in the map. Story tables also show `delivery_status`. The Relationships table is derived from each document's declared References.

Map files contain a generated region delimited by `<!-- sdlc:generated:start -->` and `<!-- sdlc:generated:end -->`. `sdlc update-map` rewrites only that region, so hand-written open questions outside it survive regeneration.

```markdown
# Product Requirements

Product capabilities, user expectations and release scope.

<!-- sdlc:generated:start -->
## Documents

| ID | Document | Purpose | Status |
|---|---|---|---|
| PR-001 | [Product Overview](PR-001-product-overview.md) | Core product expectations for the first release. | Draft |

## Relationships

| Source | Relationship | Target |
|---|---|---|
| [PR-001](PR-001-product-overview.md) | Derived From | [BR-001](../BR/BR-001-business-overview.md) |
<!-- sdlc:generated:end -->

## Open Questions
- (hand-written, preserved)
```

A document is authoritative for its content, metadata and declared references. A stale map is a validation problem fixed by regeneration; it is never grounds for editing document content.

## 6. Shared Skill execution contract

Every document-producing Skill follows this sequence:

1. **Initialize:** `sdlc init` (idempotent; never overwrites an existing document).
2. **Discover:** Read the root map, target directory map, applicable source documents and their references.
3. **Check overlap:** Run `sdlc find-overlaps` (§7) before allocating any ID. Present plausible overlaps to the user; never auto-create a duplicate or auto-merge.
4. **Classify:** Decide whether the user wants a new document, revision, extension or summary. Ask if unclear.
5. **Analyze:** Distinguish known facts, assumptions, proposals, unresolved decisions and missing information.
6. **Interrogate:** Ask focused questions only about material gaps; reuse answers already available (§8).
7. **Draft:** Apply the discipline-specific template and audience.
8. **Review:** Surface uncertainties; obtain human review/approval where appropriate.
9. **Write:** `sdlc allocate-id` for new documents and requirements; create/update Markdown without destructive replacement; apply the material-edit rule of §4.3.
10. **Index:** `sdlc update-map`.
11. **Validate:** `sdlc validate`; report remaining problems.

## 7. Overlap detection

Before a new document ID is allocated, `sdlc find-overlaps` inspects existing documents in the same category and reports candidates ranked by: same category, title similarity, purpose similarity, and shared linked requirement IDs / `Derived From` targets. The Skill presents plausible overlaps to the user and asks whether to revise an existing document, extend it, or create a new one. Matching is deterministic and advisory; the human decides.

## 8. Shared interrogation convention

A shared guide (`shared/interview.md`, the `sdlc-interview` guidance) defines **how** to question; each Skill defines **what** to question.

- Read existing context before asking anything.
- Include core document sections and select optional sections based on relevance.
- Ask about 3–5 related, high-value questions per round rather than an exhaustive form.
- Provide suggested options where useful, with room for free-form answers.
- Accept `Unknown`, `TBD`, `Not applicable`; never fabricate an answer.
- Generate a substantive Draft after initial discovery and permit iterative revision.
- BRD questions focus on business problem, objectives, stakeholders, scope, constraints and success.
- PRD questions focus on users, needs, journeys, product behavior, MVP and acceptance.
- Story questions focus on scoped value, behavior, edge cases and observable acceptance criteria.
- Technical Skills inspect repository code and related requirements before suggesting designs.
- Use the host agent's available questioning mechanism; do not assume a new UI, checkpoint schema or chat transport.

## 9. Central library packaging and CLI runtime

```text
skill-library/
├── pyproject.toml            # Python >= 3.11; PyYAML is a permitted runtime dependency (front matter parsing)
├── sdlc/                     # deterministic helper CLI (python -m sdlc)
│   ├── __main__.py
│   └── ...                   # init, ids/ledger, frontmatter, maps, overlaps, validate
├── shared/
│   ├── document-conventions.md
│   ├── map-conventions.md
│   ├── reference-conventions.md
│   ├── cli-contract.md
│   └── interview.md          # shared interrogation guidance (§8)
├── skills/
│   ├── sdlc-init/SKILL.md
│   ├── sdlc-explore/SKILL.md
│   ├── sdlc-validate/SKILL.md
│   ├── create-brd/
│   │   ├── SKILL.md
│   │   └── references/{section-catalog,discovery-questions,template}.md
│   ├── create-prd/           # same structure
│   └── create-stories/       # same structure
└── tests/
    ├── unit/                 # CLI unit tests
    └── fixtures/             # sample projects for acceptance scenarios
```

PyYAML is the only approved third-party runtime dependency; any other requires a documented justification. The supported agents are Codex and Claude Code. Thin installation adapters (an `install/` directory with one adapter per agent, added in M2) link or install `skills/` per each agent's discovery convention. The logical layout above is authoritative for the source repository.

### 9.1 CLI invocation contract

Invoked as `python -m sdlc <command> [--root <project-root>] [--json]`, run by Skills through the host agent's shell capability. Project root defaults to the nearest ancestor containing `.sdlc/`, falling back to the current directory for `init`.

| Command | Responsibility |
|---|---|
| `init` | Idempotently create standard folders, root/directory maps, `.sdlc/config.md`, `.sdlc/ledger.md`. Never overwrites documents. |
| `allocate-id --category <BR\|PR\|US\|DES\|PLAN\|RES\|TEST> [--title <t>]` | Reserve the next document ID and return ID and target path. `allocate-id --requirement <DOC-ID>` returns the next `-Rnnn`. Records the ledger. |
| `retire-id <ID> [--replaced-by <ID>] [--note <n>]` | Tombstone a document or requirement ID. |
| `create-dir --artifact <design\|plans\|research\|tests>` | Create an Artifacts subdirectory with its map on first use. |
| `update-map [<dir>]` | Regenerate the generated region of affected maps from document metadata and references. |
| `list [--category <c>] [--status <s>]` | List documents with metadata (supports explore). |
| `references <ID>` | Outgoing and incoming references for a document or requirement. |
| `find-overlaps --category <c> --title <t> [--purpose <p>] [--covers <ID>...]` | Ranked overlap candidates (§7). |
| `validate` | Check structure, front matter, ID/filename agreement, duplicate and retired IDs, links, `covers`, stale maps, missing maps. |

Contract: human-readable output by default and stable JSON with `--json`; exit code `0` success/no errors, `1` validation problems found, `2` usage or environment error. Commands other than `validate` and read-only queries write only files within the project root. The CLI never contacts external services. `sdlc-status` and publishing adapters (R3) build on `list`/`references`/`validate` and are specified in M5.

## 10. First-party Skill catalog and release plan

| Release | Skill | Responsibility |
|---|---|---|
| R1 (first slice) | `sdlc-init` | Initialize project structure |
| R1 (first slice) | `sdlc-explore` | Interactive navigation: answer questions about existing documents, context and links |
| R1 (first slice) | `create-brd` | Business interrogation and BRD |
| R1 (first slice) | `create-prd` | Product interrogation and PRD |
| R1 | `sdlc-validate` | Validate structure, IDs, maps, links, traceability |
| R1 | `sdlc-interview` (shared guidance) | Shared interrogation guidance, `shared/interview.md` |
| R1 | `create-stories` | Traceable user stories with `covers` IDs |
| R2 | `refine-stories` | Improve story clarity and readiness |
| R2 | `create-design` | Technical design (`DES`) |
| R2 | `plan-implementation` | Implementation plan (`PLAN`) |
| R2 | `implement-story` | Code changes for a selected story |
| R2 | `review-implementation` | Independent code/requirement review |
| R2 | `create-test-plan` | Test scenarios (`TEST`) |
| R2 | `verify-story` | Execute verification; report actual results |
| R3 | `publish-stories` | External issue publication |
| R3 | `sdlc-status` | Structured project-wide progress and outstanding-work report |

**R1 is not complete** until `sdlc-validate`, `shared/interview.md` and `create-stories` are implemented and acceptance-tested in addition to the four first-slice Skills, and the `sdlc` CLI commands they depend on exist.

`sdlc-explore` and `sdlc-status` differ: explore answers ad-hoc questions interactively; status produces a repeatable report of counts by status/delivery_status, uncovered requirements, stories without coverage, open questions, and validation problems.

`publish-stories` initially supports GitHub through an adapter; Jira comes later. It requires a publication preview and explicit confirmation. Local Markdown remains authoritative for requirements; there is no automatic bidirectional sync.

Milestones (see `SDLC-IMPLEMENTATION-CHECKLIST.md`) map to releases: M2 + M3 = R1, M4 = R2, M5 = R3, M6 = end-to-end validation and release.

## 11. Acceptance criteria

M1 closes when this document and `SDLC-IMPLEMENTATION-CHECKLIST.md` are approved by a human. R1 must later demonstrate:

- Empty-repository initialization and safe repeat initialization.
- A sparse idea becomes a substantive BRD after useful questioning.
- A PRD can be generated with or without a BRD.
- Generated stories have working links to source documents and `covers` IDs that exist.
- Maps accurately describe the files present and are derived from metadata; hand-written map sections survive regeneration.
- Overlapping documents are surfaced before duplicate creation.
- The validator identifies broken links, duplicate IDs (including after a simulated merge), missing/retired `covers` IDs, invalid front matter and stale maps.
- A Story with `covers: []` validates without error and is reported separately as lacking requirement coverage.
- `.sdlc/` is not required to contain or be listed in a `map.md`.
- Material edit to an Approved document returns it to In Review.
- Skills invoke the CLI rather than reimplementing its algorithms.
- Documents work without any UI, and there is no dependency on third-party Skill libraries.

## 12. Explicit non-goals

No mandatory Workstream/Activity/Session workflow, new visual UI, versioned folder trees, attempt history, advanced AI recall, relationship graph database, automatic issue synchronization, approval workflow engine, cross-branch globally collision-proof ID allocation, or invented business/product decisions. There is no legacy implementation to migrate or preserve.

## 13. Decisions

Resolved by the architecture owner (revision 2):

1. **Requirement IDs:** document-scoped (`BR-001-R001`); stable, never recycled, tombstoned; moves require reconciliation (§4.4, §4.5).
2. **Artifacts subdirectories:** created on first use (§3, §9.1).
3. **Distribution:** central first-party library with agent-specific installation/linking (§3, §9).
4. **Approval:** human-declared status only, with material-edit reversion (§4.3).
5. **Helper runtime:** first-party Python 3.11+ CLI with a documented contract (§9).
6. **Metadata:** parseable YAML front matter; maps derived from it (§4.2, §5).

The former decision about existing Runtime files is removed; the project is greenfield.

### Review findings resolution

| # | Finding | Resolution |
|---|---|---|
| 1 | Four reference Skills vs. R1 scope | R1 defined as seven deliverables plus CLI; the four are a first slice (§10). |
| 2 | Greenfield contradiction | All legacy/migration text removed (§2.9, §12, §13). |
| 3 | Missing milestone checklist | `SDLC-IMPLEMENTATION-CHECKLIST.md`. |
| 4 | Deterministic helpers had no home | `sdlc/` Python package, tests and CLI contract (§9). |
| 5 | Regenerable maps vs. authored purpose | `purpose` in front matter; generated regions (§4.2, §5). |
| 6 | Fragile bold-line metadata | YAML front matter required (§4.2). |
| 7 | ID allocation edge cases | Ledger, tombstones, monotonic per checkout, merge duplicate detection (§4.5). |
| 8 | Lifecycle statuses | `delivery_status` separate from `status` (§4.3). |
| 9 | Editing Approved documents | Material edits return to In Review (§4.3). |
| 10 | Supporting Artifact IDs vague | `DES`, `PLAN`, `RES`, `TEST` defined with uniqueness checks (§4.1). |
| 11 | Traceability granularity | `covers` requirement IDs plus relative links, validated (§4.7). |
| 12 | Overlap detection unspecified | `find-overlaps` heuristics, human decides (§7). |
| 13 | `sdlc-status` vs. `sdlc-explore` | Distinguished (§10). |

### Conditional-approval corrections (revision 3)

1. PyYAML explicitly permitted as a runtime dependency (§9).
2. `covers: []` allowed for standalone Stories; missing coverage reported separately, not as an error (§4.2, §4.7).
3. `.sdlc/` declared an internal configuration directory exempt from `map.md` (§2.4, §3).

## 14. Supporting decisions and deferred items

Decided (recorded for M2; final with M1 approval):

- **Initial agents:** Codex and Claude Code. Each gets a thin, agent-specific installation adapter that installs or links the central Skills; Skill content is not forked per agent (§3, §9).
- **CLI distribution:** initially installed from the repository (`pip install -e .`). `pipx` packaging is deferred to M6.
- **`.sdlc/config.md`:** minimal front matter only: `project_name`, `schema_version`, `directories` (document directories, defaulting to `BR`, `PR`, `Stories`, `Artifacts`), and optional `publishing` defaults (e.g. target repository). No other settings without a documented need.
- **Overlap matching:** deterministic and advisory. Inputs are category, normalized title, purpose, and requirement references (`covers` / `Derived From`). Clear non-matches are ignored; ambiguous or plausible matches require human confirmation. Scoring rules are documented in `shared/cli-contract.md` in M2.

Deferred (not part of R1):

- Detecting material edits to Approved documents (e.g. content hash). Until then the material-edit rule of §4.3 is enforced by Skills only.
- `pipx` packaging.
- Jira publishing.


## 15. R2 technical contract (M4 amendments — awaiting human approval)

Added while starting M4; nothing in R1 behavior is removed. Items marked **NEW** are materially new semantics that need human approval (the M4 handoff requires it). Operational detail and record formats are in `skill-library/shared/technical-conventions.md`.

1. **Two states stay separate.** Document `status` and Story `delivery_status` never substitute for each other (§4.3 unchanged).
2. **NEW — Transition table.** Ready is set only on the human's explicit declaration; `implement-story` sets In Progress and Implemented (and pause/rework transitions); `verify-story` sets Verified (and demotes Verified → Implemented); no other Skill sets Implemented or Verified; unmet prerequisites mean stop and report, never set.
3. **NEW — Invalidation rule.** A material change to a Story's acceptance criteria, scope or `covers` after work started sets `delivery_status` back to Ready; code rework after Implemented/Verified moves it to In Progress. Existing verification runs are marked `Superseded` additively, never deleted or rewritten. *This amends the M3 `create-stories` rule "never change delivery_status as a side effect": invalidation is now the single permitted automatic change.*
4. **NEW — Evidence records in documents.** Story `## Implementation Record` (`IR-n`), TEST `## Verification Runs` (`VR-n`, append-only, result vocabulary `passed | failed | blocked | not-run`), optional Story `## Review Record` (`RV-n`). Recording them is non-material for document `status`.
5. **NEW — Validator enforcement (justified CLI extension).** `validate` checks the record schema and that `Verified` is supported: an Implementation Record exists (also for Implemented), every numbered acceptance criterion has a current, passed run (latest non-superseded run per criterion), and the Story has at least one criterion. Codes and severities are in `shared/cli-contract.md`. Unresolved TBD behavior on a Verified Story is a warning. Exit-code contract unchanged (errors ⇒ 1).
6. **NEW — Review gating.** Reviews are read-only and advisory; only a *latest* `requires-rework`/`blocked` verdict blocks `verify-story` from setting Verified until re-reviewed or explicitly waived by the human. Enforced by the Skill, not the CLI.
7. **Technical artifacts.** Templates and catalogs for `DES`, `PLAN`, `TEST` and optional `RES` live with their Skills; each links its source Stories under `Derived From`. None is a prerequisite for a Story. `Artifacts/tests/evidence/` may hold verification logs; the CLI ignores it.
8. **Instruction templates.** `AGENTS.md`/`CLAUDE.md` (create-if-missing on `init`) now also route technical artifacts and delivery-state changes to the R2 Skills.
