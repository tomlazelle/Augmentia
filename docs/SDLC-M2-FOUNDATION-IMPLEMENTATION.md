# M2 — Foundation Implementation Handoff

**Status:** Ready to start after human M1 approval  
**Source of truth:** `SDLC-SKILL-ARCHITECTURE.md` revision 3 and `SDLC-IMPLEMENTATION-CHECKLIST.md` (repository copies). If this handoff conflicts with either, stop and ask rather than silently changing the architecture.

## Objective

Build the small, deterministic Python foundation for a greenfield, Markdown-first, first-party SDLC Skill library. At M2 exit, an empty repository can be initialized repeatedly without data loss; documents can be indexed, discovered, assigned stable IDs, and validated; Codex and Claude Code can invoke the same centrally maintained foundation Skills. **Do not implement BRD, PRD, Story authoring or interview flows in M2.**

## Implementation sequence

Work in reviewable increments; update the existing M2 checklist only when an item is implemented **and tested**.

### 1. Package and CLI contract
- Create `skill-library/pyproject.toml`, Python 3.11+ `sdlc/` package, `__main__.py`, and `tests/`. Support `pip install -e .` and `python -m sdlc`.
- PyYAML is the only preapproved third-party runtime dependency; justify any additional dependency before introducing it.
- Support `python -m sdlc <command> [--root <project-root>] [--json]`. Root defaults to the nearest ancestor with `.sdlc/`; `init` falls back to current directory.
- Document command arguments, stable JSON output shape, diagnostics, and exit codes in `shared/cli-contract.md`. Default output is human-readable. Exit `0`: successful operation, including coverage notices; `1`: structural validation failures; `2`: usage/environment errors. Define command-specific failure behavior consistently.

### 2. Initialization and configuration
- Implement `init` to create root `map.md`, `BR/map.md`, `PR/map.md`, `Stories/map.md`, `Artifacts/map.md`, `.sdlc/config.md`, and `.sdlc/ledger.md`.
- `.sdlc/` is internal: **no `.sdlc/map.md`**, document ID, or authored-document front matter required for its internal files. The validator must not require or generate its map.
- `.sdlc/config.md` uses YAML front matter with `project_name`, `schema_version`, `directories` (default BR/PR/Stories/Artifacts), and optional `publishing`. Validate this minimal schema.
- Implement `create-dir --artifact <design|plans|research|tests>` to create optional Artifacts subdirectories and their maps on first use. Regenerate `Artifacts/map.md` accordingly.
- Repeat `init` must not overwrite existing documents, custom map text, ledger contents or configuration.

### 3. Metadata and ID ledger
- Parse and validate required authored-document YAML fields: `id`, `title`, `purpose`, `status`, `created`, `updated`. Dates use ISO `YYYY-MM-DD`; document status is Draft / In Review / Approved / Superseded.
- Stories additionally require `delivery_status` (Not Started / Ready / In Progress / Implemented / Verified) and a present `covers` list, which **may be empty** for a standalone Story.
- Support categories BR, PR, US, DES, PLAN, RES, TEST; filenames `<ID>-<short-kebab-title>.md` in the defined directories.
- Implement `allocate-id --category ...`, `allocate-id --requirement <DOC-ID>`, and `retire-id <ID> [--replaced-by ...] [--note ...]`.
- `.sdlc/ledger.md` is a CLI-maintained Markdown table tracking allocated/retired IDs and tombstones. Allocate above the highest relevant ledger or on-disk ID; never recycle an ID within a checkout. Requirement IDs are document-scoped (`PR-001-R003`), declared as `- **PR-001-R003** — ...`.
- Concurrent Git branches are not globally collision-proof; validate and report duplicates after simulated merge rather than claiming distributed uniqueness.

### 4. Maps, references, discovery and overlap
- Implement `update-map [<dir>]`, regenerating **only** content between `<!-- sdlc:generated:start -->` and `<!-- sdlc:generated:end -->`; preserve hand-authored text outside the region.
- Derive map title/status/purpose from document metadata (copy `purpose` verbatim), relationships from document References, and Story delivery status where relevant. Link subdirectory maps when created. Maps are indexes, not sources of truth.
- Implement `list [--category ...] [--status ...]` and `references <ID>` (outgoing and incoming references, including requirement IDs where applicable).
- Implement deterministic `find-overlaps --category ... --title ... [--purpose ...] [--covers ...]` using category, normalized title, purpose and requirement/source references. Document scoring/thresholds in `shared/cli-contract.md`; return candidates and reasons, **never automatically merge or create**. Ambiguous matches are presented to the human by the calling Skill.
- Relative Markdown links must resolve from the containing file. A Story with nonempty `covers` must link the corresponding source document in `Derived From`.

### 5. Validation
Implement `validate` for:
- Required directories/maps, while exempting `.sdlc/` from map generation and authored-document metadata rules.
- Front matter schema, dates/status, filename/ID agreement, duplicate IDs, ledger/retired-ID inconsistencies.
- Broken local Markdown links, stale generated map regions, missing referenced requirement IDs, retired references and mismatches between Story `covers` and its source links.
- Coverage **notices**, separately from structural errors: standalone Stories with `covers: []` and requirements with no covering Story. Notices do not change a successful exit code (`0`).
- Diagnostics that identify file/path, affected ID, reason and severity in human and JSON outputs.

### 6. Foundation Skills and installation
- Write shared `document-conventions.md`, `map-conventions.md`, `reference-conventions.md`, `cli-contract.md`.
- Implement `skills/sdlc-init/SKILL.md`, `skills/sdlc-explore/SKILL.md`, `skills/sdlc-validate/SKILL.md`. These are instructions that invoke the CLI; do not duplicate ID/map/filesystem algorithms in prompts.
- Implement thin adapters under `install/` for **Codex** and **Claude Code**. Install/link the central Skills according to each agent's supported discovery mechanism, without maintaining forked Skill bodies. Verify each by installing and invoking at least one Skill.
- `shared/interview.md`, `create-brd`, `create-prd`, and `create-stories` are **M3**, not M2.

## Required acceptance tests

Use isolated temporary fixture repositories. Demonstrate:
1. `pip install -e .` works; `python -m sdlc --help` and all documented commands are available.
2. Empty-repo `init` yields the correct structure and passes `validate`; repeat `init` is idempotent (no changes to existing content).
3. Optional Artifacts directory is created on first use, has a map, and is linked in its parent map.
4. Allocate, retire and reallocate document and requirement IDs without reuse, including deletion of the highest-numbered document.
5. Valid YAML parses; missing/invalid fields, duplicate IDs, malformed requirement declarations, and filename mismatches are reported.
6. Map regeneration preserves manually written text; deliberate map staleness is detected.
7. Broken local links, nonexistent/retired `covers` IDs, missing source links, and simulated branch-merge collisions are detected.
8. `covers: []` and uncovered requirements produce coverage notices but exit `0` when no structural error exists.
9. `list`, `references` and `find-overlaps` return deterministic, documented human and JSON outputs.
10. Codex and Claude Code adapters each install/link a Skill without forking its source.

## Deliverables and exit gate

Provide source code, CLI/shared contract documentation, three foundation Skills, two installation adapters, fixture tests, and an updated `SDLC-IMPLEMENTATION-CHECKLIST.md`.

**M2 exit criterion (from checklist):** From an empty repository, `init` produces a valid structure; repeat `init` changes nothing; `validate` passes on it and reports seeded faults (broken link, duplicate ID, stale map, bad front matter); all CLI tests pass. Also demonstrate the checklist's additional coverage, agent-installation, and configuration tests.

At the checkpoint report: commands delivered; test command and pass/fail counts; sample init tree; sample validation diagnostics (error vs coverage notice); deviations/questions; and unchecked checklist items. Do not claim M2 complete on implementation alone. **Stop for human review before starting M3.**

## Explicit non-goals

No UI, Runtime/Bridge migration, event stream, database, distributed ID service, external publishing, bidirectional sync, advanced AI recall, BRD/PRD/Story generation, or speculative general-purpose infrastructure. `pipx` is M6; Jira is deferred.
