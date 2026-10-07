# codex — 05-status

### USER

Use the sdlc-status skill and tell me where this project stands and what I should do next.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 15 s)

## Project health

Validation is **OK**: 0 errors, 0 warnings, and 1 notice across 2 documents. The status report shows no stale maps or broken references.

## Document inventory

- BR: none
- PR: none
- US: 1 — US-001 (Draft)
- DES: none
- PLAN: none
- RES: none
- TEST: 1 — TEST-001 (Draft)

## Story delivery

- Not Started: 0
- Ready: 1 — US-001
- In Progress: 0
- Implemented: 0
- Verified: 0

## Traceability

There are no uncovered PR requirements or invalid references. US-001 is standalone (`covers: []`) and has unresolved acceptance behavior (`TBD`); both are reported as notices.

## What to do next

- **Resolve the TBD behavior** in US-001, or explicitly accept the residual uncertainty. Use `refine-stories`.
- **Implement US-001**, which is Ready. Use `implement-story`.
- After implementation, **verify it** against its acceptance criteria with recorded evidence. Use `verify-story`.

