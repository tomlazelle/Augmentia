# BRD Section Catalog

Audience: business stakeholders. A BRD states **what the business needs and why**, not the product or technical solution. It can stand alone: it does not need a PRD, design or repository code.

**Core sections** are always present (a section with nothing known says `TBD` and appears in Open Questions). **Optional sections** are added only when the interview shows they matter; never pad.

| Section | Core? | Content | Include when |
|---|---|---|---|
| Front matter | Core | `id`, `title`, `purpose` (one sentence), `status: Draft`, `created`, `updated` | always |
| References | Core | `Derived From`, `Related To`, `Supporting Artifacts` with relative links | always (`None identified.` is valid) |
| Business Context and Problem | Core | Current situation, who is affected, cost of the status quo | always |
| Objectives and Desired Outcomes | Core | Outcomes wanted, independent of solution | always |
| Stakeholders | Core | Groups, interest, decision role | always |
| Scope (In / Out) | Core | Boundaries; explicit exclusions | always |
| Business Requirements | Core | Stable IDs `BR-NNN-RNNN`; one need each; only decisions the user made | always |
| Constraints and Dependencies | Core | Budget, timeline, regulatory, organizational, system | always (TBD if unknown) |
| Success Measures | Core | How success is judged; targets only if provided | always |
| Assumptions and Risks | Core | Labeled assumptions and named risks | always |
| Open Questions | Core | Unknowns carried forward, with owner/date if known | always |
| Current Process | Optional | How the work is done today | the user described a manual or legacy process worth documenting |
| Business Rules and Policies | Optional | Policies the solution must respect | policies, compliance or pricing rules came up |
| Cost/Benefit or Funding | Optional | Only user-supplied figures | the user gave financial context |
| Glossary | Optional | Domain terms | the domain vocabulary is unfamiliar or ambiguous |
| Supporting Artifacts links | Optional | Research or evidence | such documents exist (link them under References) |

## Using the template

`template.md` is the exact file layout. Replace every `{{PLACEHOLDER}}` (`{{ID}}` is the ID from `allocate-id`; requirement numbers come from `allocate-id --requirement`), delete sections that do not apply and any unused table rows or bullets, and leave no `{{...}}` text behind.

## Established versus unresolved

Success measures, constraints and requirements state only what the user established. An unresolved item is written as `TBD` (for example `Target: TBD`) and repeated in Open Questions; never fill it with a plausible value.

## Requirement rules

- Declare each as `- **BR-001-R001** — text` (bold ID, em dash). IDs come from `allocate-id --requirement <DOC-ID>`; never reuse or hand-number.
- A requirement is a need the **user decided**. A suggestion you offered that they have not accepted belongs in Open Questions or Assumptions.
- Keep each requirement an outcome ("The clinic can reduce missed appointments"), not a feature or design.
- Do not start any other list item with a requirement ID outside the References section.
