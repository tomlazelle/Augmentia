---
name: review-implementation
description: Independently review the actual code changes for a Story against its acceptance criteria, requirements, design, plan and tests, reporting findings with severity, location and basis (verified observation or potential concern) and a verdict of complete, requires-rework or blocked. Read-only, it never edits code and never sets or implies Verified. Use when the user asks to review or audit a Story implementation.
---

# review-implementation

Reviews what was actually built for a Story. It is **read-only** and **not verification**: it never edits code, never runs a check and calls it verification, and never changes `delivery_status`. Audience: the human deciding what happens next.

Method and rules: `../../shared/technical-conventions.md` (§6 Reviews, §7 repository work). CLI: `sdlc` (`../../shared/cli-contract.md`); if it fails with `command not found: sdlc`, tell the user to install the library and stop. Commands run from the project root.

## Workflow

1. **Select the Story** (`sdlc list --category US`) and read it **in full**: acceptance criteria (number them as `AC-n`), unresolved TBD behavior, the requirements in `covers`, and its Implementation Record. Read linked Plan/Design/Test Plan (`sdlc references <US-ID>`).
2. **Get the real diff.** Use the repository (`git diff`, `git log`, the files named in the Implementation Record) and read the changed code and tests **in full context**. If there is no repository, no recorded change, or you cannot access the code, the verdict is `blocked`: say exactly what is missing and stop.
3. **Review against evidence.** For each acceptance criterion, decide whether the code and tests actually address it; note divergences, missing edge/negative-path coverage, scope creep beyond the Story/plan, and inconsistencies with the design. You may run read-only commands to understand behavior, but do not present that as verification.
4. **Report findings.** For each finding give: **severity** (`blocker`, `major`, `minor`, `nit`), **location** (`path:line`), **basis** (*verified observation* — you read or reproduced it — or *potential concern* — inference), the **acceptance criterion / requirement** it relates to, rationale, and a suggested next step. List unresolved questions and criteria with no corresponding test. Never invent locations or line numbers; only cite what you opened.
5. **Give a verdict:** `complete` (no blocker/major findings), `requires-rework` (any blocker or major), or `blocked` (could not review). Say explicitly that **this review is not verification** and that only `verify-story` can set `Verified`, from actual runs.
6. **Record it only if the user wants it kept.** With their consent append an entry headed exactly `### RV-<n> — <YYYY-MM-DD>` (RV, not RR; continue the numbering) to the Story's `## Review Record` (format in `technical-conventions.md` §5) and update `updated`; this is not a material change. The latest verdict `requires-rework` or `blocked` will stop `verify-story` from setting `Verified` until a newer `complete` review exists or the human explicitly waives the finding (record the waiver in the Review Record). Then run `sdlc validate` and report it.

## Rules

- Read-only: no code edits, no fixes, no test-file edits. Suggest; do not apply.
- Never set or imply `Verified`; never change `delivery_status` or document `status`.
- Distinguish what you verified from what you suspect; never present a concern as a fact.
- Human approval remains human approval.
