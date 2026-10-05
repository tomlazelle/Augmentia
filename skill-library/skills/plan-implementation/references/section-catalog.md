# Implementation Plan Section Catalog

Audience: the engineer (or agent) implementing the Story and the person reviewing progress. A Plan (`PLAN-NNN`, `Artifacts/plans/`) is an **actionable sequence** derived from one or more Stories after inspecting the repository. It works **with or without a Design**; the human decides whether a Design is needed.

| Section | Core? | Content |
|---|---|---|
| Front matter | Core | `id`, `title`, `purpose` (one sentence), `status: Draft`, `created`, `updated` |
| References | Core | `Derived From`: source Story link(s) with requirement IDs; `Related To`: a Design if any |
| Scope | Core | Stories/criteria delivered; explicit exclusions |
| Repository Context | Core | **Inspected** files actually opened; **Not inspected / unavailable** |
| Approach | Core | The approach in brief |
| Steps | Core | Ordered steps; files (verified vs proposed), dependencies, a check per step |
| Acceptance-to-Test Mapping | Core | Each *decided* acceptance criterion → the test or check that will demonstrate it |
| Validation Commands | Core | Commands proposed for the implementation and verification; mark those you have not run |
| Risks | Core | Risks and mitigations |
| Open Questions | Core | Unresolved items carried forward |
| Rollout / Migration | Optional | Only when the change affects existing data, deployment or users |

## Using the template

`template.md` is the exact layout. Replace every `{{PLACEHOLDER}}`, delete rows and bullets that do not apply, leave no `{{...}}` text behind. Source Story links are relative from `Artifacts/plans/` (`../../Stories/US-001-slug.md`).

## Rules

- **Verified vs proposed:** name a file as *verified* only if you opened it; otherwise write "proposed". Do not present guessed file names as facts.
- Steps must be small and checkable; each states how completion is demonstrated.
- The mapping covers only *decided* criteria. TBD acceptance behavior stays TBD in the Story; the plan lists it under Open Questions, never with an invented expected result.
- Material uncertainty is a question for the human, not a decision for the plan.
- A Plan never changes a Story's `delivery_status`; implementing is `implement-story`'s job.
