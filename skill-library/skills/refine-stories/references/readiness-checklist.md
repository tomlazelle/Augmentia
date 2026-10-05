# Readiness Checklist (Not Started → Ready)

`Ready` is a **human declaration**. This Skill reports the checklist and records `delivery_status: Ready` only when the user explicitly says the Story is ready **and** every item below holds (or the user explicitly accepts the noted exception).

- [ ] The Story is one bounded slice of user value with a clear In Scope / Out of Scope.
- [ ] At least one **numbered, decided** acceptance criterion in Given/When/Then form, each with an observable result a reviewer could check.
- [ ] Undecided behavior is listed under `### Unresolved Acceptance Behavior (TBD)` and Open Questions — not written as a criterion. *(Exception: the user explicitly accepts implementing with it still open.)*
- [ ] `covers` holds real requirement IDs and each owning document is linked under `### Derived From`; or `covers: []` is a deliberate standalone Story.
- [ ] Dependencies on other Stories/artifacts are named; known blockers are resolved or accepted by the user.
- [ ] `sdlc validate` reports no errors.

Not required: a BRD, PRD, Design or Plan. Being Ready says nothing about document `status` (approval is separate).
