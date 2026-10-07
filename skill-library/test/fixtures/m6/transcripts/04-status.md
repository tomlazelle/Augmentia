# Walkthrough 4 — `sdlc-status` on the final state, both agents (read-only)

All human turns are scripted by the maintainer (hand-authored inputs: the product persona's answers). The fresh repository `tasklog` was created from scratch for M6 (not an M1–M5 fixture), with hand-authored seed code (`tasklog/store.py`, 3 tests). `sdlc` was installed with `pipx` from the release-candidate wheel; the agents' `PATH` had the pipx `sdlc` and a project `.venv` with pytest but **no** `sdlc` module. The stub `gh` (`tests/unit/fakegh.py`) was first on `PATH`; no real GitHub call was made in any agent run.

`st-1`/`st-2` ran **before** a defect was found: Codex had written the TBD heading at level 2 and `status` did not see it, so both agents reported "no unresolved TBD". After the fix (`unresolved_tbd_bullets` accepts level 2 or 3) the release candidate was rebuilt and `st-3`/`st-4` correctly report the TBD. Every run was told "fix anything stale" or run in a clean tree; fingerprints are identical.

### USER (`st-1`, new session)

Use the sdlc-status skill and tell me where this project stands and what to do next. (Fix anything that looks stale while you are at it.)

### AGENT (Claude Code (`claude -p`, project skills linked by `sdlc-install-claude-code` from the pipx install))

Here's where things stand for this project (`tasklog`):

**Project health:** Clean. `sdlc validate` and `sdlc status` both report 0 errors, 0 warnings, 0 notices. No stale maps, no broken references. Nothing to fix — I checked, and there's genuinely nothing stale here (the Draft/Verified combination below is expected SDLC behavior, not a defect, see below).

**Document inventory** (7 docs total, one of each type, all `status: Draft`):
- BR-001 — tasklog: Surface Past-Due Tasks
- PR-001 — tasklog: Overdue Task Listing
- US-001 — List overdue tasks
- DES-001, PLAN-001, RES-001, TEST-001 (one each)

**Story delivery:**
- US-001 is the only story, and it's **Verified** — fully implemented and verified with recorded evidence.

**Traceability:** No uncovered requirements, no standalone stories, no invalid references, no unresolved TBDs. US-001 cleanly covers PR-001-R001 through R004.

**About the Draft/Verified combination:** this isn't stale data — `status: Draft` tracks the *document's* review lifecycle (has a human approved this writeup?) while `delivery_status: Verified` tracks whether the *code* has been implemented and tested. They're independent axes. Right now every document is still Draft, meaning no one has formally approved the BRD, PRD, Story, Design, Plan, or Test Plan — even though the underlying feature is built and verified.

**What to do next:**
1. There's no more work in the pipeline — US-001 is the only story and it's done end-to-end.
2. If you want these documents to reflect real sign-off, someone should review and approve BR-001, PR-001, US-001, DES-001, PLAN-001, RES-001, and TEST-001 (the relevant skills — `create-brd`, `create-prd`, `refine-stories`, `create-design`, `plan-implementation`, `create-test-plan` — handle moving `Draft → In Review → Approved`; only you can approve).
3. If there's a next increment of this feature, start with `create-brd` or `create-prd` to scope it, or `create-stories` if the PRD already covers it.

_Harness: exit 0; file fingerprint before→after: `5bec361003df3c4f` → `5bec361003df3c4f`; BEFORE the TBD-detector fix: misses the TBD._

### USER (`st-2`, new session)

Use the sdlc-status skill and tell me where this project stands and what to do next. (Fix anything that looks stale while you are at it.)

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

## Project health

Validation is **OK**: 0 errors, 0 warnings, and 0 notices across 7 documents. There are no stale maps or broken references reported.

## Document inventory

There is one Draft document in each category: BR, PR, US, DES, PLAN, RES, and TEST.

## Story delivery

`US-001` is **Verified**. There are no Stories in Not Started, Ready, In Progress, or Implemented.

## Traceability

No uncovered PR requirements, standalone Stories, invalid references, or unresolved TBD acceptance behavior were reported.

## What to do next

Nothing needs attention. The `sdlc-status` skill is explicitly read-only and says not to regenerate maps; the status report also found no stale maps to fix.

_Harness: exit 0; file fingerprint before→after: `5bec361003df3c4f` → `5bec361003df3c4f`; BEFORE the TBD-detector fix: misses the TBD._

### USER (`st-3`, new session)

Use the sdlc-status skill and tell me where this project stands and what to do next.

### AGENT (Claude Code (`claude -p`, project skills linked by `sdlc-install-claude-code` from the pipx install))

## Project Health
✅ Valid — 0 errors, 1 warning, 0 notices, no stale maps or broken references.

- **Warning**: `US-001` is Verified but still has an unresolved TBD in its acceptance criteria. Verification only covers the decided criteria, not the TBD residual.

## Document Inventory
All 7 documents exist, one per type, and all are still `Draft`:

| Type | Total | Draft |
|---|---|---|
| BR | 1 | 1 |
| PR | 1 | 1 |
| US (Stories) | 1 | 1 |
| DES | 1 | 1 |
| PLAN | 1 | 1 |
| RES | 1 | 1 |
| TEST | 1 | 1 |

## Story Delivery
- **Verified**: US-001 "List overdue tasks" — delivery_status is Verified, but the document's own `status` field is still `Draft`.
- No stories in Not Started, Ready, In Progress, or Implemented.

## Traceability
- No uncovered requirements, no standalone stories, no invalid references.
- **Unresolved TBD**: US-001.

## Needs Attention / Next Actions
1. **US-001 has an unresolved TBD acceptance criterion.** Even though it's Verified, that TBD was never decided. Options:
   - Run **`refine-stories`** to pin down the TBD behavior, then (if it changes scope) re-run **`implement-story`** / **`verify-story`** as needed.
   - Or explicitly accept the residual as out of scope, documented via `refine-stories`.
2. **All 7 documents (BR, PR, US, DES, PLAN, RES, TEST) are still `Draft`.** Since the Story has already been implemented and verified, these would normally move toward `Approved` once reviewed. That's a human decision — I can walk through review with **`create-brd`**, **`create-prd`**, **`refine-stories`**, **`create-design`**, **`plan-implementation`**, **`create-test-plan`** respectively if you want to advance any of their statuses, but only you can approve them.
3. No Stories currently sit in Ready/In Progress/Implemented, so there's nothing queued for `implement-story` or `verify-story` right now beyond resolving US-001's TBD.

**Bottom line**: the pipeline for US-001 ran end-to-end (planned → implemented → verified), but it's not fully closed out — there's a loose TBD and all docs are still in Draft status awaiting review/approval.

_Harness: exit 0; file fingerprint before→after: `5bec361003df3c4f` → `5bec361003df3c4f`; after the fix._

### USER (`st-4`, new session)

Use the sdlc-status skill and tell me where this project stands and what to do next.

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

## Project health

Validation is **OK**: 0 errors, 1 warning, and 0 notices across 7 documents. The status output doesn’t report stale maps or broken references.

## Document inventory

- BR: 1 Draft
- PR: 1 Draft
- US: 1 Draft
- DES: 1 Draft
- PLAN: 1 Draft
- RES: 1 Draft
- TEST: 1 Draft

## Story delivery

- Not Started: 0
- Ready: 0
- In Progress: 0
- Implemented: 0
- Verified: 1 (`US-001`)

`US-001` is Verified, but it still has unresolved acceptance behavior marked TBD.

## Traceability

No uncovered PR requirements, standalone Stories, or invalid references are reported. The outstanding issue is the TBD acceptance behavior in `US-001`.

## Suggested next steps

- Decide the TBD behavior or explicitly accept the residual, using **`refine-stories`**.
- Then rerun **`sdlc-status`** to see the updated project snapshot.

_Harness: exit 0; file fingerprint before→after: `5bec361003df3c4f` → `5bec361003df3c4f`; after the fix._
