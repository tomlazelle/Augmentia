# Story Section Catalog

Audience: implementers and product reviewers. A Story is one appropriately sized slice of user value with observable behavior. It may be **standalone** (`covers: []`) or trace to specific documented requirements.

| Section | Core? | Content |
|---|---|---|
| Front matter | Core | `id`, `title`, `purpose` (one sentence of value), `status: Draft`, `created`, `updated`, **`delivery_status`**, **`covers`** |
| References | Core | `Derived From` links to **every document that owns a covered requirement** (and any other source); `Related To`, `Supporting Artifacts` |
| Story | Core | "As a … I want … so that …" |
| Scope (In / Out) | Core | What this Story delivers and what neighboring Stories own |
| Acceptance Criteria | Core | Numbered, observable Given/When/Then checks a reviewer can verify |
| Unresolved Acceptance Behavior (TBD) | Optional | `- **TBD** — …` bullets for outcomes nobody has decided; states the open question, never a result |
| Edge Cases and Negative Paths | Core | Invalid input, permission failures, empty states, limits — only cases with a **decided** observable outcome; undecided ones go under *Unresolved Acceptance Behavior* |
| Business Rules | Optional | Rules that govern the behavior — only if stated by the user or the source |
| Open Questions | Core | Unknowns carried forward |
| Dependencies / Notes | Optional | Other Stories or systems this relies on |

## Using the template

`template.md` is the exact file layout. Replace every `{{PLACEHOLDER}}`, delete sections that do not apply, and leave no `{{...}}` text behind. `covers: [{{...}}]` becomes e.g. `covers: [PR-001-R001, PR-001-R002]`, or `covers: []`.

## Front matter rules

- `delivery_status: Not Started` unless a human explicitly establishes another valid state. Never set `Implemented` or `Verified` here; those belong to later implementation and verification Skills. Do not confuse it with document `status`.
- `covers` is present in every Story and holds **specific, existing requirement IDs only** (e.g. `PR-001-R003`) — never a document ID, never an ID you invented, never an ID `python -m sdlc references` cannot find. Confirm IDs by reading the source documents.
- Each owning document of a covered ID must be linked under `### Derived From` with a valid relative link (`- [PR-001 — Title](../PR/PR-001-slug.md)`). `validate` errors otherwise.
- **Standalone Story:** `covers: []`, and `Derived From` may be `None identified.` (or list a non-requirement source). It is valid: `validate` reports it as a `story-no-coverage` **notice**, not an error, and exits 0. State that to the user. Never create a fake PRD or invent requirement IDs to avoid the notice.

## Verifiable versus unresolved

An **acceptance criterion** (or edge case) is verifiable: Given/When/Then with a **decided, observable** outcome that a reviewer could test. If the outcome is unknown, it is *not* a criterion: do not write `then … is TBD` in Given/When/Then form (it would read as an executable test). Record it as a `- **TBD** — …` bullet under `### Unresolved Acceptance Behavior (TBD)` that states the question, add it to Open Questions, and keep it out of the numbered criteria.

## Sizing and quality

- One Story, one coherent behavior a user can observe; if it needs "and" between unrelated outcomes, split it. Stories in a set have **distinct scope**; use *Out of Scope* to state the seams.
- Acceptance criteria describe observable outcomes (what a user or reviewer sees), not implementation. Every covered requirement must be addressed by at least one criterion.
- Do not start any list item outside References with a requirement ID; cite requirements in `covers` or mid-sentence.
