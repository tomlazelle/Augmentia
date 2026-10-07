# codex — 05-status

### USER

Use the sdlc-status skill and tell me where this project stands and what I should do next.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 14 s)

## Project health

Validation is **OK**: 0 errors, 0 warnings, and 1 notice across 2 documents. No invalid references are reported.

## Document inventory

- BR: none
- PR: none
- US: 1 Draft
- TEST: 1 Draft
- DES, PLAN, RES: none

## Story delivery

- Ready: **US-001**
- Not Started, In Progress, Implemented, Verified: none

## Traceability

US-001 is standalone (`covers: []`) and has unresolved acceptance behavior (TBD). The standalone status is informational; the TBD needs a decision.

## Suggested next steps

1. Decide or explicitly accept the unresolved behavior in US-001. Use **refine-stories** to clarify its acceptance criteria.
2. If the story is ready to proceed, use **implement-story** to implement US-001.
3. After implementation, use **verify-story** to check its acceptance criteria and record evidence.

