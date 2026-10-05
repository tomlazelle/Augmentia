# Design Section Catalog

Audience: engineers implementing and reviewing the Story. A Design (`DES-NNN`, `Artifacts/design/`) explains **how** to build what one or more Stories need, grounded in the actual repository. It is **optional**: no Story requires one unless the human or project says so, and small changes should get a short design (or none). Optional Research (`RES-NNN`, `Artifacts/research/`) records evidence behind a decision; create it only when a question needs sources (`references/research-template.md`); link it under the Design's `### Supporting Artifacts`.

| Section | Core? | Content |
|---|---|---|
| Front matter | Core | `id`, `title`, `purpose` (one sentence), `status: Draft`, `created`, `updated` |
| References | Core | `Derived From`: the source Story link(s) with requirement IDs; `Related To`; `Supporting Artifacts` (Research) |
| Context and Problem | Core | What the Stories need technically |
| Repository Context | Core | **Inspected** files/areas actually opened; **Not inspected / unavailable** |
| Requirements and Acceptance Traceability | Core | Story IDs, acceptance criteria and requirement IDs the design serves |
| Options Considered | Core (may be one option for small changes) | Alternatives with advantages and drawbacks |
| Decision | Core | Chosen option; who decided, or "Proposed, not yet decided" |
| Design | Core | Components, interfaces, data flow — as much as the change needs |
| Dependencies | Core | Libraries, services, other work |
| Risks | Core | Known risks and mitigations |
| Assumptions | Core | Labeled, with what would invalidate them |
| Open Decisions | Core | Unresolved choices carried forward |
| Security, Migration and Operational Considerations | Optional | Only when the change touches auth/data/permissions, existing data, or deployment and operations |
| Data Model / API Sketch | Optional | Only when the Story introduces or changes them |

## Using the template

`template.md` is the exact layout. Replace every `{{PLACEHOLDER}}`, delete sections and bullets that do not apply, and leave no `{{...}}` text behind. `{{SOURCE_STORY_LINK_AND_REQUIREMENT_IDS}}` becomes e.g. `[US-001 — Title](../../Stories/US-001-slug.md) — serves PR-001-R003`, one bullet per source Story (relative links from `Artifacts/design/`).

## Rules

- **Inspect first.** Every design lists what was actually inspected. Statements about code you did not open are proposals.
- No invented implementation details: leave a decision open rather than guess. Do not pad small changes with empty considerations.
- A design supports the Story's *decided* acceptance criteria; it does not add requirements or turn TBD behavior into commitments.
- Do not change any Story's `delivery_status`.
