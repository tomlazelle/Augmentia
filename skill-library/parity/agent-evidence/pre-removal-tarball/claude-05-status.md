# claude — 05-status

### USER

Use the sdlc-status skill and tell me where this project stands and what I should do next.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 12 s)

## Project status

**Health:** Valid — 0 errors, 0 warnings, 1 notice.

**Document inventory:**
- BR: none
- PR: none
- Stories (US): 1, in Draft
- DES/PLAN/RES: none
- TEST: 1, in Draft

**Story delivery:**
- Ready: **US-001 — Export overdue tasks** (Draft status, no delivery started)
- Not Started / In Progress / Implemented / Verified: none

**Traceability:**
- US-001 is a standalone story (not linked to a PR requirement) — this is informational, not a defect.
- US-001 has an **unresolved TBD** in its acceptance criteria.

**Needs attention:**
1. US-001 has an unresolved acceptance behavior (TBD) — needs a decision, or an explicit decision to accept the residual as-is.
2. Despite the TBD, it's marked Ready to implement.

## Suggested next steps
- Resolve the open TBD in US-001 via **`refine-stories`** (recommended first, since an undecided acceptance criterion could affect implementation scope).
- Once settled, proceed to **`implement-story`** for US-001.
- Optionally, add a Design (`create-design`) or Implementation Plan (`plan-implementation`) first if the change is non-trivial — both are optional.
- No BRD/PRD exists yet; this project currently runs off a standalone story, which is fine but worth knowing if broader requirements tracking is wanted later (`create-brd`/`create-prd`).

