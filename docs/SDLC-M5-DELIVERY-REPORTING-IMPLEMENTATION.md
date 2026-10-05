# M5 — Delivery & Reporting Implementation Handoff (R3)

**Status:** Ready after human M4 approval  
**Authority:** `docs/SDLC-SKILL-ARCHITECTURE.md`, then `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`. Preserve all approved M1–M4 contracts.

## Objective

Add delivery visibility and controlled external publishing while preserving local Markdown as the authoritative SDLC state.

M5 implements:
1. `sdlc-status` — read-only structured project progress reporting.
2. `publish-stories` — GitHub-first Story publication with mandatory preview and explicit human confirmation before external mutation.

No bidirectional synchronization, Jira, background publishing, database, UI, or workflow runtime.

## 1. Core invariants

- Local Markdown remains authoritative.
- `sdlc-status` is read-only.
- `publish-stories` performs no external write until a preview has been shown and explicitly confirmed.
- Preview performs zero external mutations.
- Publishing never silently changes requirements, acceptance criteria, document `status`, or Story `delivery_status`.
- GitHub Issue edits/state do not automatically flow back to local Stories.
- Do not infer local completion from GitHub Issue state.
- Credentials/tokens never belong in `.sdlc/config.md`, Markdown artifacts, maps, ledgers, fixtures, or evidence documents.
- Preserve M1–M4 CLI, validation, map, ID, overlap, project-instruction and R2 evidence contracts.

# Part A — `sdlc-status`

## 2. Purpose and boundary

`sdlc-status` answers: **What is the current project state, what needs attention, and what is ready next?**

Keep it distinct from `sdlc-explore`:
- `sdlc-explore`: interactive navigation/discovery.
- `sdlc-status`: concise structured progress snapshot.

Derive state from current repository files and existing CLI commands (`list`, `references`, `validate`) rather than agent memory. Read maps/documents only where necessary. Do not duplicate deterministic CLI algorithms in the Skill.

## 3. Required report

Default output is concise human-readable Markdown containing:

### Project health
- validation result;
- errors, warnings and notices;
- stale maps/broken references when present.

### Document inventory
Summaries for BR, PR, US, DES, PLAN, RES and TEST by document status. Absence of optional technical artifacts is not itself a defect.

### Story delivery
Summarize Not Started, Ready, In Progress, Implemented and Verified Stories.

### Traceability
Surface:
- uncovered PR requirements;
- standalone Stories (`covers: []`);
- invalid references;
- relevant unresolved/TBD behavior.

Coverage notices remain informational.

### Needs attention / next actions
Examples include structural errors, unresolved acceptance behavior, Ready Stories, In Progress Stories, Implemented Stories awaiting verification, failed/blocked verification evidence, and documents legitimately returned to In Review.

`sdlc-status` must not allocate IDs, edit files, regenerate maps, change status, publish, implement or verify work.

# Part B — `publish-stories`

## 4. Initial target

Support **GitHub Issues only**. Jira remains deferred.

Flow:

```text
Local Story -> Preview -> Explicit human confirmation -> GitHub Issue
```

GitHub is a publication target, not the source of truth.

## 5. Publishing configuration

Use the optional `publishing` area in `.sdlc/config.md`. Keep it minimal, e.g.:

```yaml
publishing:
  provider: github
  repository: owner/repository
```

Document any additional required fields before adding them. Authentication comes from the available GitHub environment/tooling, never project Markdown/config credentials. Missing auth/access blocks publication and must not be reported as success.

## 6. Story selection and eligibility

The human explicitly selects Stories. Never publish all Stories merely because they exist.

Before preview, inspect selected Stories and report relevant:
- structural/validation errors;
- broken requirement references;
- unresolved acceptance behavior;
- missing publishing configuration;
- known prior publication.

A valid standalone `covers: []` Story may be published. Do not require BRD, PRD, Design, Plan or Test Plan solely for publication.

## 7. Issue representation

Recommended title:

```text
[US-001] Story title
```

Body should faithfully include:
- local Story ID;
- summary/purpose;
- `covers` requirement IDs when present;
- acceptance criteria;
- unresolved acceptance/TBD behavior when present;
- relevant dependencies/notes;
- statement that local Markdown is authoritative.

Do not invent missing requirements or acceptance criteria, and do not hide TBDs.

## 8. Mandatory preview and confirmation

For every selected Story, preview:
- target repository;
- proposed Issue title;
- complete proposed body or faithful rendered equivalent;
- proposed labels/metadata, if any;
- whether this is new or already has a known publication;
- relevant warnings/notices.

Preview performs **no GitHub mutation**.

After preview, require an unambiguous affirmative confirmation. Merely invoking the Skill, requesting a preview, or asking what would happen is not confirmation.

If Story content or proposed publication content changes after preview, invalidate the confirmation boundary: regenerate preview and ask again.

After confirmation, publish exactly the confirmed set/content. Report success/failure per Story. Never claim success without the external operation succeeding.

## 9. Publication identity and duplicate prevention

Define a minimal durable local publication record before coding. It must identify:
- provider (`github`);
- target repository;
- GitHub Issue number/stable identifier;
- Issue URL when returned.

Prefer explicit Markdown metadata/reference storage over a hidden database.

Rules:
- Never identify prior publication solely by Issue title.
- Re-running publication for a known Story must not silently create a duplicate.
- Show known publication in preview and make no mutation by default.
- M5 does not require updating existing Issues from changed local Stories.
- No bidirectional synchronization.

If operational publication metadata is stored on/near an Approved Story, explicitly define whether it is non-semantic metadata exempt from Approved -> In Review. Do not accidentally make publishing alter product approval state.

## 10. Provider boundary

Keep GitHub-specific mechanics narrow, but do not build a speculative tracker plugin framework.

The Skill owns selection, eligibility, preview, confirmation and reporting. Provider code owns only necessary GitHub operations.

Do not create PRs, branches, commits, releases, projects, milestones or labels unless separately approved.

## 11. Failure handling

Explicitly handle:
- missing/invalid publishing configuration;
- unsupported provider;
- missing GitHub tooling/authentication/permissions;
- repository not found;
- API/network failure;
- individual Issue failure;
- partial success;
- previously published Story;
- Story changed after preview;
- validation error affecting a selected Story.

Never record success before GitHub succeeds. If GitHub succeeds but recording publication identity fails, report the inconsistency prominently and do not retry blindly because that could create a duplicate.

# Part C — Acceptance tests

## 12. `sdlc-status`

Demonstrate:
1. Empty initialized project yields a useful report.
2. BR/PR/Story inventory and statuses are correct.
3. All five Story delivery states are distinguished.
4. Uncovered PR requirements and standalone Stories remain notices.
5. Broken links/stale maps/errors are surfaced.
6. Ready, In Progress, Implemented-awaiting-verification and Verified are distinguishable.
7. Missing optional DES/PLAN/RES/TEST is not treated as a defect.
8. Status causes no repository mutation.
9. Results come from current files, not conversational memory.

## 13. `publish-stories`

Demonstrate:
1. Missing config blocks publishing clearly.
2. Preview makes no external mutation.
3. Preview faithfully shows target/title/body.
4. No external write without explicit confirmation.
5. Ambiguous/non-affirmative responses do not publish.
6. Changed content after preview requires a new preview/confirmation.
7. Standalone `covers: []` Story can publish.
8. TBD behavior remains visible.
9. Success is recorded only after external success.
10. Failure never records false success.
11. Partial success is reported per Story.
12. Known publication prevents silent duplicate creation.
13. Local Markdown remains authoritative.
14. GitHub changes are not automatically imported.
15. Credentials never appear in generated artifacts/fixtures.

Use a fake/stub GitHub boundary for deterministic automated tests. A real GitHub mutation must use an explicitly designated safe test repository and explicit authorization; it is not required for the default suite.

## 14. Agent evidence

Exercise `sdlc-status` through Claude Code and Codex where practical, retaining representative transcripts showing read-only behavior.

For `publish-stories`, demonstrate through an agent:
- preview;
- refusal to mutate without confirmation;
- explicit confirmation boundary.

A mocked provider is sufficient for automated acceptance. Do not create public test Issues merely to satisfy M5. Disclose any unexecuted live-provider scenario in `docs/SDLC-M5-EVIDENCE.md`.

## 15. Regression requirements

Run the complete Python 3.11 suite including opt-in install tests. Preserve all R1/R2 behavior.

Keep these M6 carry-forward items:
- real Codex contextual-overlap run;
- live-agent RES exercise;
- clean-repository end-to-end release walkthrough.

Do not expand M5 to consume them.

# Part D — Deliverables

## 16. Required deliverables

- `skills/sdlc-status/SKILL.md`;
- `skills/publish-stories/SKILL.md`;
- proportionate references/templates;
- narrow GitHub provider support;
- documented publication identity representation;
- minimal publishing config contract;
- preview/confirmation/duplicate/failure tests;
- status tests;
- Claude Code and Codex adapter discovery updates;
- justified architecture/convention updates;
- updated `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`;
- `docs/SDLC-M5-EVIDENCE.md`.

## 17. Exit criterion

M5 is ready for review when:
- `sdlc-status` accurately reports a fixture project without mutation;
- `publish-stories` produces a faithful GitHub preview for selected Stories;
- external mutation cannot occur without explicit confirmation;
- confirmed publication uses the confirmed content and reports results accurately;
- duplicate publication is prevented/surfaced;
- local Markdown remains authoritative;
- the complete Python 3.11 regression suite passes;
- both Skills are discoverable through supported adapters;
- evidence/checklist are current;
- limitations/deferred work are recorded.

**Do not mark M5 human-approved. Do not begin M6. Stop for human review.**

# Explicit non-goals

No Jira, GitHub Projects, bidirectional sync, automatic Issue updates/closure, polling/webhooks, semantic requirement analysis, workflow runtime, UI/dashboard, `pipx` release work, or M6 final release validation.
