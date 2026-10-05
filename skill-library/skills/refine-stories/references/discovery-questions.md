# Story Refinement Questions

A **pool**, not a script. Read the Story, its source requirements, neighboring Stories and the relevant code and tests first; ask only what is still ambiguous (`../../../shared/interview.md`: 3–5 per round, recap between rounds, `TBD` accepted).

- **Behavior:** what exactly should happen in the main path? Which rules (limits, formats, permissions, timing) apply?
- **Acceptance:** what would a reviewer observe to accept it? (turn each answer into a decided Given/When/Then; leave undecided ones in the Unresolved section)
- **Edge and negative paths:** invalid or missing input, no permission, empty or duplicate data, failures of dependencies — which have a decided outcome?
- **Scope seams:** which behavior belongs to a neighboring Story? Is this Story too big and should it be split (hand off to `create-stories`)?
- **Dependencies and sequencing:** does it need another Story, service or decision first?
- **Existing code and tests:** the repository already does X; does this Story change, reuse or replace it?
- **Readiness:** is anything still blocking the human from declaring this Story Ready?
