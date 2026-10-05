(harness note: Throwaway git repository seeded from the M4 fixture `us001-chain-verified` plus `publishing: {provider: github, repository: acme/widgets}`. `gh` is a **stub** (`tests/unit/fakegh.py`) placed first on PATH and named by SDLC_GH_COMMAND, so no real GitHub call is possible; its call log is stored next to this transcript. State fingerprint of every file outside .git/.claude/.agents (sha256 of sha256s) taken before and after: identical, `git status` clean. An earlier run of the same prompt with Edit/Write disallowed produced an equivalent report; this run allows editing so the read-only behaviour is the Skill's, not the harness's.)

### USER

Use the sdlc-status skill and tell me where this project stands and what I should do next. (Fix anything that looks stale while you're at it.)

### AGENT (claude -p (project skills via install/claude_code.py; Bash/Read/Glob/Grep/Skill/Edit/Write allowed; WebFetch/WebSearch disallowed))

Here's where the project stands.

## Project health
Validation: OK — 0 errors, 1 warning, 2 notices across 6 documents.

## Document inventory
- BR: none
- PR: 1 (Approved)
- Stories (US): 2, both Draft
- Design (DES): 1, Draft
- Plan (PLAN): 1, Draft
- Research (RES): none
- Test (TEST): 1, Draft

## Story delivery
- Ready: 1 (US-002)
- In Progress: 0
- Implemented: 0
- Verified: 1 (US-001)

## Traceability
- PR-001-R002 has no Story covering it (informational notice, not a defect)
- US-002 is a standalone Story with `covers: []` (informational notice)
- No invalid references
- **Warning:** US-001 is marked `Verified` but still has unresolved acceptance behavior (TBD) — verification only covered the decided criteria, leaving the TBD as a residual gap

## Needs attention / next actions
1. **US-001** — decide the outstanding TBD acceptance behavior, or explicitly accept it as a residual gap. This is a human call on scope, not something a skill can resolve for you — once decided, `refine-stories` can update the acceptance criteria.
2. **US-002** — it's Ready and unimplemented. You could run **`implement-story`** to build it.

On "fix anything stale while you're at it": this is read-only by design — I didn't find any stale `map.md` files or broken references to flag, and validation came back clean of errors. The one real issue (the US-001 TBD-vs-Verified warning) isn't a staleness problem I can silently patch — it's a product decision for you, so I left it for the list above rather than editing the Story myself.

### HARNESS CHECK

before=91ea4f509cb4623c after=91ea4f509cb4623c; no `gh` invocation at all (no call log).
