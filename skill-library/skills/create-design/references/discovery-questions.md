# Design Discovery Questions

A **pool**, not a script. First read the Story, its requirements and the relevant code and tests; ask only what they do not settle (`../../../shared/interview.md`: 3–5 per round, recap between rounds, `TBD` accepted).

- **Scope of the design:** which Story or Stories does this design serve? Is a full design warranted, or a short one?
- **Constraints:** compatibility, performance, platform, libraries you must or must not use, deadlines?
- **Existing patterns:** the code shows X convention; should the new work follow it, or is there a reason to diverge?
- **Options:** I see options A and B in this codebase; do you have a preference or a constraint that rules one out? (record as a proposal until the user chooses)
- **Data and interfaces:** who calls this, what data is persisted, what must stay backward compatible?
- **Security / migration / operations** (only if the change touches them): permissions, existing data, rollout and rollback?
- **Unknowns:** what is the biggest technical unknown, and would a small spike or research note (RES) resolve it?
