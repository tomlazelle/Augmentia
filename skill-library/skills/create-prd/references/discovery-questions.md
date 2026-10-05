# PRD Discovery Questions

A **pool**, not a script. Ask 3–5 per round using `../../../shared/interview.md`: read the BRD or other source first and skip what it answers; adapt to the answers; accept `Unknown` / `TBD` / `Not applicable`.

## Order of priority

1. **Users and needs**
   - Who are the primary users? Are there secondary users or admins?
   - What is each trying to accomplish, and how do they do it today?
   - Which user matters most for the first release?
2. **Journeys**
   - Walk me through the most important journey from start to finish. What triggers it, what does the user see, what counts as done?
   - What are the second and third journeys?
3. **Behavior and capabilities**
   - What must the product do in that journey? What rules or limits apply (who can do what, quantities, timing)?
   - What happens when something goes wrong (invalid input, no connectivity, someone else's data)?
4. **MVP and scope**
   - What is the smallest release that delivers the value? What is deliberately later or never?
   - Is there anything that must not ship without?
5. **Acceptance**
   - How will you tell the product is acceptable? What would a stakeholder check?
6. **Constraints and dependencies**
   - Platforms, existing systems to integrate, policies (privacy, accessibility), timeline, team limits?
7. **Assumptions and unknowns**
   - What are we assuming about users or data? What is the biggest open question and who can answer it?

## When a BRD (or other source) exists

Summarize the relevant business needs you found and ask only: which of these does this PRD address, which are deferred, and what product decisions the BRD left open. Do not ask again about problem, stakeholders or business success measures.

## Follow-ups triggered by answers

| If the user says… | Consider asking… |
|---|---|
| Multiple user types | Permissions and differences per type; which is MVP |
| A workflow with approvals | Who approves, what states exist, what notifications |
| Integration with X | Direction of data, ownership, failure behavior |
| "It should be fast/secure/accessible" | Measurable expectation, or record as TBD (→ optional Non-Functional) |
| A design or technology choice | Why it matters to users; record as a constraint if decided, otherwise Proposal |
| "I don't know" | Who would know, by when; record as an Open Question |

## Useful option sets (suggestions only)

- Release posture: pilot with one group / MVP for one user type / full launch / not decided
- Notification channels: email / SMS / in-app / none / not decided
- Data handling: new data only / migrate existing / integrate with existing system / not decided
