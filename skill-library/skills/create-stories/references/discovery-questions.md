# Story Discovery Questions

A **pool**, not a script. Ask 3–5 per round using `../../../shared/interview.md`. Read the PRD (or other source) first and derive the candidate Stories yourself; ask the human only what the source does not settle.

## Deriving candidates (before asking)

- List the source requirements (`PR-…-R…`) and group them by user goal or journey step.
- Propose a Story breakdown as a **suggestion** ("US-A covers R001, US-B covers R002 and R003 — split or merge?"). Do not treat it as decided until the user agrees.

## Order of priority

1. **Value and scope**
   - Which user goal does this Story serve, and what is the smallest useful slice?
   - What is explicitly a different Story?
2. **Behavior and business rules**
   - What exactly happens, in order? What rules apply (limits, formats, permissions, timing)?
3. **Edge cases and negative paths**
   - What if the input is invalid, missing, duplicate, or too large?
   - What if the user lacks permission, is offline, or the dependency fails?
   - Empty states, first-time use, concurrent changes?
4. **Observable acceptance**
   - What would a reviewer see or check to accept it? What message, state or data change?
5. **Sequencing and dependencies**
   - Does this need another Story first? Any known ordering or release constraints?

## Follow-ups triggered by answers

| If the user says… | Consider asking… |
|---|---|
| "It should validate input" | Which fields, which rules, what message is shown |
| "Admins can also…" | Split into a separate Story or same? Permission boundaries |
| "It depends on the other system" | Failure/timeout behavior; is that a separate Story |
| Something the PRD doesn't mention | Is this a new requirement (→ suggest updating the PRD via `create-prd`) or Story-level detail? Never add a requirement ID yourself |
| "I don't know" | Record in Open Questions and, if it blocks an acceptance criterion, write that criterion as TBD |

## Useful option sets (suggestions only)

- Story size: one Story per requirement / group related requirements / split by user role / not decided
- Negative-path depth: main failure modes only / exhaustive / defer to a later refinement
