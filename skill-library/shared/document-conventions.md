# Document Conventions

Applies to every authored SDLC document. The CLI (`shared/cli-contract.md`) enforces these rules; Skills follow them when writing.

## Categories, IDs and filenames

| Category | ID | Directory | Example |
|---|---|---|---|
| Business Requirements | `BR-NNN` | `BR/` | `BR-001-business-overview.md` |
| Product Requirements | `PR-NNN` | `PR/` | `PR-001-product-overview.md` |
| User Story | `US-NNN` | `Stories/` | `US-001-register-user.md` |
| Design | `DES-NNN` | `Artifacts/design/` | `DES-001-authentication.md` |
| Plan | `PLAN-NNN` | `Artifacts/plans/` | `PLAN-001-auth-rollout.md` |
| Research | `RES-NNN` | `Artifacts/research/` | `RES-001-oauth-providers.md` |
| Test plan/report | `TEST-NNN` | `Artifacts/tests/` | `TEST-001-registration.md` |

- Get IDs only from `sdlc allocate-id`. Never invent or renumber one. IDs are never reused, even after a document is deleted (`retire-id` records the tombstone).
- Filename: `<ID>-<short-kebab-title>.md` (lowercase letters, digits, hyphens).
- Allocation is monotonic per checkout, not collision-proof across branches; `validate` reports duplicate IDs after a merge.

## Front matter (required)

```yaml
---
id: PR-001
title: Product Overview
purpose: Core product expectations for the first release.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---
```

- `purpose` is one sentence; maps copy it verbatim.
- Dates are ISO `YYYY-MM-DD`. Never invent historical dates.
- `status`: `Draft`, `In Review`, `Approved`, `Superseded`. Approval is a human decision; never set `Approved` yourself.
- **Material edits to an Approved document** (requirements, scope, acceptance criteria, references) set `status: In Review` and update `updated`; tell the user. Typo and formatting fixes do not.
- Stories also require `delivery_status` (`Not Started`, `Ready`, `In Progress`, `Implemented`, `Verified`) and `covers: [ID, ...]` (**requirement IDs only**, never document IDs; `covers: []` is valid for a standalone Story, and `validate` reports it as a coverage notice, not an error).

## Requirements inside documents

Declare each requirement as `- **PR-001-R003** — text` (bold ID, space, em dash, text), or as a heading `### **PR-001-R003** — text`. The ID prefix must be the containing document's ID. Get numbers from `allocate-id --requirement <DOC-ID>`. Editing wording keeps the ID; removing a requirement retires its ID (`retire-id`), and its text may stay marked *Retired*. Moving a requirement to another document is a reconciliation: allocate a new ID there, retire the old one with `--replaced-by`, and update every `covers` and reference.

## Technical artifacts and delivery evidence (R2)

`DES`, `PLAN`, `TEST` and `RES` documents follow all rules above and link their source Story under `### Derived From`. Story `delivery_status` transitions, the invalidation rule, and the Implementation Record / Verification Runs / Review Record formats are in `technical-conventions.md`; only `implement-story` sets `Implemented` and only `verify-story` sets `Verified`.

## Verifiable versus unresolved

Acceptance criteria and edge cases are **verifiable**: Given/When/Then with a decided, observable outcome. An unknown outcome is not a criterion and must not read like a test: write it as a `- **TBD** — <the open question>` bullet (Stories: under `### Unresolved Acceptance Behavior (TBD)`), never as `then … TBD`. Requirements, acceptance expectations and success measures state only what the user established; do not add stronger behavior than the requirements support.

## Content rules

Read before writing. Ask about ambiguity. Do not fabricate business decisions, approvals, KPIs, dates or test results; record unknowns as `Unknown` or `TBD`.
