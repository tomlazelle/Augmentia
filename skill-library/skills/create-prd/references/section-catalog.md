# PRD Section Catalog

Audience: product and delivery stakeholders (product, design, engineering leads, QA). A PRD states **what the product does for its users**, not the technical design. It **does not require a BRD**: it can stand alone, and when a BRD exists it is offered as a source, never demanded.

**Core sections** are always present (with `TBD` and an Open Question if nothing is known). **Optional sections** appear only when the interview makes them relevant.

| Section | Core? | Content | Include when |
|---|---|---|---|
| Front matter | Core | `id`, `title`, `purpose` (one sentence), `status: Draft`, `created`, `updated` | always |
| References | Core | `Derived From` (a BRD or other source, if any), `Related To`, `Supporting Artifacts` | always (`None identified.` is valid) |
| Product Summary | Core | What, for whom, value | always |
| Target Users and Needs | Core | User groups and their goals | always |
| User Journeys and Use Cases | Core | Key end-to-end flows | always (even one) |
| Behavior and Capabilities | Core | Observable behavior and rules | always |
| Scope (MVP / Out of Scope) | Core | First release boundary and exclusions | always |
| Product Requirements | Core | Stable IDs `PR-NNN-RNNN`, verifiable, user-decided | always |
| Acceptance Expectations | Core | What "good enough" looks like, observably | always |
| Constraints and Dependencies | Core | Platform, integrations, policy, timeline | always (TBD if unknown) |
| Assumptions and Open Questions | Core | Labeled assumptions; unknowns carried forward | always |
| Non-Functional Expectations | Optional | Performance, accessibility, privacy, availability — only what the user stated | the user raised quality attributes |
| Release Plan / Phasing | Optional | Order of delivery | more than one release was discussed |
| Metrics and Analytics | Optional | Product signals the user wants tracked | the user named measures |
| Glossary | Optional | Domain terms | vocabulary is ambiguous |

## Using the template

`template.md` is the exact file layout. Replace every `{{PLACEHOLDER}}` (`{{ID}}` is the ID from `allocate-id`; requirement numbers come from `allocate-id --requirement`), delete sections and rows that do not apply, and leave no `{{...}}` text behind.

## Acceptance expectations: established versus unresolved

List only expectations the user established or that follow directly from a stated requirement. Do not add stronger behavior than the requirements support (a shared list does not imply duplicate detection or prevention). An unresolved expectation is a `- **TBD** — <question>` bullet, never an assertion or a test-like statement.

## Source handling

- **With a BRD:** list the BRD under `### Derived From` as `- [BR-001 — Title](../BR/BR-001-slug.md)` (relative link; `sdlc list --category BR` finds candidates). Product requirements should serve the BRD's needs, but do not restate the BRD, and do not create business requirements.
- **Without a BRD:** leave `Derived From` as `None identified.` and proceed. Never create a BRD or a placeholder upstream document.
- To cite the specific business requirement a product requirement serves, mention the ID inside the sentence or the reference item (for example `- [BR-001 — Title](../BR/…) — serves BR-001-R002`); `validate` checks such IDs exist.

## Requirement rules

- Declare each as `- **PR-001-R001** — text` (bold ID, em dash). IDs come from `allocate-id --requirement <DOC-ID>`; never hand-number or reuse.
- A requirement is something the **user decided**. Options you suggested stay in Open Questions until chosen.
- Phrase requirements so a Story can later cite them in `covers` and a reviewer can verify them; one behavior per requirement.
- Do not start any other list item with a requirement ID outside the References section.
