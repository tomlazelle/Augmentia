# Test Plan Discovery Questions

A **pool**, not a script. Read the Story (decided criteria and the TBD section), the covered requirements, any Plan or Design, and the existing tests first (`../../../shared/interview.md`).

- **Which tests already exist** for this behavior, and which criteria do they already cover? (cite the files you opened)
- **Method:** can each criterion be checked by an automated test with the project's command, or does it need a person (UI, device, an external service)?
- **Environment:** what setup, data or services do the scenarios need, and can they run here?
- **Boundaries:** which limits, invalid inputs and permission cases matter for this Story?
- **Regression:** which existing behavior could this change break?
- **Undecided outcomes:** which criteria have no decided result yet? (they go under *Unresolved*, not into scenarios)
- **Evidence:** what should be captured so a reviewer can trust the result (log files, screenshots, observer)?
