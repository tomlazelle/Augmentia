# M6 — End-to-End Validation & Release Handoff

**Status:** Ready after human M5 approval  
**Milestone:** M6 — End-to-End Validation & Release  
**Authority:** `docs/SDLC-SKILL-ARCHITECTURE.md`, then `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`. Preserve all approved M1–M5 contracts.

## Objective

Prove that the complete first-party SDLC Skill library works as a releasable product from a clean environment.

M6 is primarily a **release-readiness and end-to-end validation milestone**, not a new feature milestone.

It must validate:

1. clean installation and packaging;
2. project initialization;
3. first-party Skill discovery;
4. Markdown document creation and traceability;
5. technical planning, implementation, review and verification;
6. status reporting;
7. controlled GitHub publication;
8. both supported agent environments;
9. user-facing installation and operating documentation;
10. final regression and release sign-off.

Do not redesign working M1–M5 architecture merely to make the release exercise more elaborate.

---

# 1. M6 invariants

- Local Markdown remains authoritative.
- All approved M1–M5 semantics remain in force.
- M6 fixes defects discovered by release validation, but does not introduce unrelated features.
- No Jira, bidirectional synchronization, workflow runtime, UI, database, background daemon, semantic validator, or advanced agent memory.
- Human approval remains required where the architecture requires it.
- Actual execution evidence must never be replaced by agent assertions.
- Tests must distinguish simulated/stubbed external behavior from live external behavior.
- Release evidence must disclose skipped, blocked, mocked, failed, manually corrected, or hand-authored steps.

---

# 2. Release packaging

## 2.1 `pipx` installation

Produce a package installable through `pipx`.

The release candidate must support a clean-user workflow equivalent to:

```bash
pipx install <package-source>
sdlc --help
sdlc init
```

The installed console entry point must expose the supported CLI without requiring:

```bash
python -m sdlc
```

Retain `python -m sdlc` compatibility if it already exists.

Validate installation from a clean isolated environment rather than relying on the editable development checkout.

## 2.2 Package contents

Verify the installed distribution contains everything required at runtime, including:

- CLI modules;
- canonical Skill sources;
- shared Skill references/conventions;
- `AGENTS.md` and `CLAUDE.md` templates;
- document/templates required by Skills;
- package metadata.

No Skill should depend accidentally on files that exist only in the source checkout.

## 2.3 Supported runtime

Python 3.11 remains the release baseline.

Run the authoritative release suite on Python 3.11.x.

Other currently tested Python versions may remain in the evidence matrix, but success on a newer interpreter does not replace the Python 3.11 release gate.

---

# 3. User documentation

Create concise user-facing documentation sufficient for a new user who has not participated in development.

At minimum document:

## Installation

- prerequisites;
- `pipx` installation;
- upgrade/reinstall procedure;
- uninstall procedure;
- how to verify installation.

## Agent integration

- Claude Code project installation/linking;
- Codex project installation/linking;
- where installed Skills appear;
- how to verify Skill discovery.

Do not claim untested user-scope behavior as verified.

## Starting a project

Explain:

```bash
sdlc init
```

and the generated structure, including:

- `AGENTS.md`;
- `CLAUDE.md`;
- `BR/`;
- `PR/`;
- `Stories/`;
- `Artifacts/`;
- `.sdlc/`.

Explain create-if-missing behavior for existing project instructions.

## Typical workflow

Provide a concise workflow such as:

```text
init
  ↓
BRD (optional)
  ↓
PRD (optional)
  ↓
Stories
  ↓
Refine
  ↓
Design / Plan / Test Plan as appropriate
  ↓
Implement
  ↓
Review
  ↓
Verify
  ↓
Status
  ↓
Publish
```

Make clear that independent entry is supported; BRD/PRD/Design are not universally mandatory.

## Core concepts

Explain:

- document IDs;
- requirement IDs;
- maps;
- relationships;
- document `status`;
- Story `delivery_status`;
- TBD/unresolved acceptance behavior;
- validation;
- coverage notices;
- publication records;
- Markdown authority.

## GitHub publishing

Document:

- configuration;
- authentication expectations;
- preview;
- explicit confirmation;
- Story + provider + repository identity;
- duplicate prevention;
- one-way publishing boundary.

Do not include credentials in examples.

---

# 4. Clean-repository end-to-end walkthrough

Create a **new temporary repository** that has not been used by prior fixtures or milestone tests.

Do not seed it from an M1–M5 fixture.

Record the complete walkthrough in M6 evidence.

## 4.1 Install

From an isolated environment:

1. install the release candidate through `pipx`;
2. run `sdlc --help`;
3. verify expected commands;
4. install/link Skills for Claude Code and Codex using supported installation mechanisms.

Record exact versions and commands.

## 4.2 Initialize

Run `sdlc init`.

Verify:

- expected directories/files;
- valid `.sdlc/config.md`;
- empty/fresh ledger;
- maps;
- canonical project instructions;
- repeated init is idempotent;
- existing project instructions are not overwritten.

## 4.3 Create product context

Use an agent to create enough product context for a realistic Story.

The walkthrough should exercise a normal chain such as:

```text
BRD → PRD → Story
```

This does not change the independent-entry rule; the chain is used here because it exercises more of the released product.

Require:

- adaptive interrogation;
- fixed recap behavior;
- requirement IDs;
- source relationships;
- map updates;
- clean validation.

## 4.4 Contextual overlap

Exercise deterministic and contextual overlap behavior.

At least one scenario must intentionally create a conceptual overlap that lexical scoring alone does not reliably identify.

The human must be presented the revise / relate / create-new decision **before ID allocation**.

This walkthrough must include the previously deferred **real Codex contextual-overlap run**.

Retain the transcript.

## 4.5 Story refinement and technical artifacts

Take a Story through the R2 technical flow.

Exercise, where appropriate:

- `refine-stories`;
- `create-design`;
- `plan-implementation`;
- `create-test-plan`.

Artifacts must use their proper IDs, maps and relationships.

Do not create optional artifacts merely to increase artifact count; each should have a defensible purpose in the walkthrough.

## 4.6 Live-agent RES exercise

Exercise the previously deferred `RES-NNN` path through a **real agent**, not only templates/CLI tests.

The agent must create/use a Research artifact for a legitimate question arising during the walkthrough.

Verify:

- ID allocation;
- location under `Artifacts/research`;
- front matter;
- references;
- map behavior;
- validation;
- actual use by the agent in subsequent reasoning/work where relevant.

Do not fabricate research conclusions. If external research is not necessary, use repository/local technical research with a real decision question.

## 4.7 Implementation

Use `implement-story` against actual source code in the fresh repository.

The implementation must make a real, inspectable code change.

Verify the approved Story delivery transitions.

Do not mark `Verified` during implementation.

## 4.8 Review

Use `review-implementation`.

The review must inspect the actual implementation/diff and trace findings to Story acceptance criteria and relevant design/plan material.

Record whether findings were discovered and, if fixes are required, how they were resolved.

Review alone must not set `Verified`.

## 4.9 Verification

Use `verify-story`.

Execute real relevant tests/commands.

Verification evidence must record actual observed results according to the R2 contract.

Demonstrate that the Story reaches `Verified` only after successful verification.

Run `sdlc validate` after the completed technical flow.

## 4.10 Status

Run `sdlc-status`.

Verify that it accurately reports:

- project health;
- document inventory;
- Story delivery state;
- traceability;
- relevant notices;
- next actions.

Confirm the status operation causes no repository mutation.

---

# 5. Live GitHub publication

M6 must close the M5 live-provider gap with **one real GitHub Issue publication**.

## 5.1 Safety boundary

Use a specifically designated repository suitable for testing.

Before mutation:

1. identify the exact repository;
2. prepare the complete `publish-stories` preview;
3. show the proposed Issue title/body;
4. obtain explicit human authorization for that live publication.

Do not interpret M6 authorization in general as authorization to create an Issue. Authorization must occur after the concrete live preview is available.

## 5.2 Execute

After explicit confirmation:

- execute the real GitHub publication;
- capture returned Issue number/URL;
- verify the correct `PUB-n` record;
- verify provider/repository identity;
- verify local Story semantic content/status was not materially changed;
- verify validation remains clean.

## 5.3 Duplicate prevention

Preview/re-run the same Story for the same repository and prove it is skipped rather than duplicated.

Do **not** create a second live Issue merely to test cross-repository publication. Existing automated tests cover that contract.

## 5.4 Cleanup

Do not automatically delete or close the Issue unless the human explicitly asks.

Record the live Issue as release evidence.

Never place authentication tokens in evidence.

---

# 6. Cross-agent release matrix

M6 must establish that both supported agents can use the installed Skills from the packaged release.

At minimum provide release evidence for:

| Capability | Claude Code | Codex |
|---|---|---|
| Discover installed Skills | Required | Required |
| Create/use governed docs | Required | Required |
| Respect project instructions | Required | Required |
| Contextual overlap decision | Existing evidence acceptable | **New live run required** |
| Technical Skill execution | Required representative run | Required representative run |
| `sdlc-status` | Required | Required |
| `publish-stories` preview/confirmation behavior | Required | Required |

Not every row needs a separate fresh repository. Avoid redundant agent runs when existing M4/M5 evidence remains valid, but clearly distinguish reused milestone evidence from newly executed M6 evidence.

The fresh end-to-end walkthrough itself should use both agents at meaningful points rather than being exclusively performed by one agent.

---

# 7. Release regression matrix

## 7.1 Automated suite

Run the complete suite on Python 3.11 with installation tests enabled.

M5 approved baseline:

```text
SDLC_TEST_INSTALL=1
Python 3.11.16
493 passed
```

M6 must not regress below the approved baseline except where tests are deliberately replaced/changed with documented justification.

Also record the default suite result and any additional interpreter run used for compatibility evidence.

## 7.2 Packaging tests

Add/retain automated tests that verify:

- package build succeeds;
- runtime templates/data are included;
- console entry point exists;
- isolated install can invoke `sdlc`;
- Skill/adapters can locate packaged resources;
- installation does not depend on source-checkout paths.

## 7.3 Release smoke test

From the isolated installed package:

```bash
sdlc --help
sdlc init
sdlc validate
sdlc status
```

and representative deterministic commands must execute successfully.

---

# 8. Documentation validation

Before release:

- follow the installation documentation exactly from a clean environment;
- follow the initialization instructions;
- follow both agent integration instructions;
- verify command examples match the released CLI;
- verify file paths/names match generated output;
- verify publishing documentation matches actual confirmation behavior.

Documentation that only describes developer-checkout behavior is insufficient.

---

# 9. M6 evidence

Create:

```text
docs/SDLC-M6-EVIDENCE.md
```

It must contain:

## Environment

- OS/environment summary;
- Python version;
- `pipx` version;
- package version/source;
- Claude Code version;
- Codex version;
- GitHub CLI version where used.

## Packaging/install evidence

Exact build/install commands and results.

## Automated tests

Exact commands and pass/skip/fail counts.

## Fresh-repository walkthrough

Chronological steps with references to generated artifacts and transcripts.

Clearly identify any manual edits/interventions.

## Deferred-item closure

Explicit evidence for:

1. real Codex contextual-overlap run;
2. live-agent RES exercise;
3. clean-repository E2E walkthrough;
4. real GitHub publication with explicit authorization.

## Cross-agent matrix

Show which evidence is new and which approved prior evidence is reused.

## Defects

For every defect found during M6:

- observed behavior;
- expected behavior;
- correction;
- regression test;
- whether architecture/contracts changed.

## Limitations

Disclose remaining limitations rather than hiding them.

## Release candidate result

State whether the release candidate is ready for human sign-off.

The document must **not** declare final human approval itself.

---

# 10. Defect policy during M6

M6 may correct defects discovered during packaging/E2E validation.

For each correction:

1. reproduce the defect;
2. determine whether it violates an approved contract;
3. fix narrowly;
4. add a regression test;
5. rerun the relevant focused tests;
6. rerun the full Python 3.11 release suite;
7. update M6 evidence.

If fixing a defect requires a new architectural semantic rather than restoring approved behavior, stop and request human review before adopting it.

Do not turn M6 into M7 through opportunistic feature work.

---

# 11. Release checklist

M6 is ready for human review only when all applicable items are complete:

- [ ] M5 human approval recorded.
- [ ] Package builds successfully.
- [ ] `pipx` clean installation succeeds.
- [ ] `sdlc` console entry point works.
- [ ] Runtime package data is complete.
- [ ] User installation documentation validated from clean environment.
- [ ] Claude Code installation/discovery validated.
- [ ] Codex installation/discovery validated.
- [ ] Fresh repository initialized successfully.
- [ ] Init idempotency confirmed.
- [ ] BRD/PRD/Story chain exercised.
- [ ] Real Codex contextual-overlap scenario completed before ID allocation.
- [ ] Technical artifact flow exercised.
- [ ] Live-agent RES scenario completed.
- [ ] Real implementation produced.
- [ ] Implementation review completed.
- [ ] Real verification evidence produced.
- [ ] Story reaches Verified correctly.
- [ ] `sdlc validate` passes.
- [ ] `sdlc-status` accurately reports final project state and is read-only.
- [ ] Live GitHub preview shown.
- [ ] Explicit human authorization obtained for the exact live GitHub preview.
- [ ] One real GitHub Issue successfully created.
- [ ] Publication record validated.
- [ ] Same-repository duplicate prevention demonstrated without creating another Issue.
- [ ] Cross-agent release matrix complete.
- [ ] Python 3.11 full suite passes with installation tests enabled.
- [ ] Documentation walkthrough passes.
- [ ] `docs/SDLC-M6-EVIDENCE.md` complete.
- [ ] Remaining limitations documented.
- [ ] Release candidate presented for human sign-off.

---

# 12. Final release gate

When all M6 work is complete, stop and present:

1. exact Python 3.11 release test command/count;
2. package/install results;
3. clean-repository E2E result;
4. Codex contextual-overlap result;
5. live-agent RES result;
6. Story implementation/review/verification result;
7. live GitHub Issue result;
8. cross-agent matrix;
9. defects found/fixed;
10. remaining limitations;
11. release documentation produced.

**Do not self-approve the release.**

The final decision belongs to the human reviewer.

---

# Explicit non-goals

M6 does not add:

- Jira publishing;
- bidirectional GitHub synchronization;
- automatic Issue update/closure;
- GitHub Projects;
- workflow orchestration;
- background agents/daemons;
- database state;
- UI/dashboard;
- semantic proof that tests exercise requirements;
- mandatory separate implementer/verifier identities;
- advanced AI memory.

Those require a future milestone and explicit architectural approval.
