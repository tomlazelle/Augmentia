# Interview Method (shared)

How every creating Skill (`create-brd`, `create-prd`, `create-stories`) questions the human. Each Skill decides **what** to ask (its `references/discovery-questions.md` and `section-catalog.md`); this guide defines **how**. It is a method, not a Skill or a form: use the host agent's ordinary way of asking the user questions, and never require an external tool or UI.

## 1. Start from what exists

- **From a one-sentence idea:** restate it in your own words, list what you can already say, and go straight to questions.
- **From an existing document or supplied material:** read it (and the documents it references) *first*. Extract facts, then ask only about what is missing, contradictory or undecided.
- Read the root `map.md`, the target directory's `map.md`, and run `python -m sdlc list` / `references <ID>` before asking anything the project may already answer.
- **Infer only what is grounded** in project material or the user's words. If you infer something, label it *Assumption* and show its source. Never turn a guess into a stated fact.

## 2. Classify what you know

Keep five buckets in mind and keep them visible in every summary:

| Bucket | Meaning |
|---|---|
| **Fact** | Stated by the user or found in a document (cite it) |
| **Assumption** | You or the user believe it but it is unconfirmed |
| **Proposal** | A suggestion you made that the user has not accepted |
| **Decision** | Explicitly chosen by the user |
| **Unknown** | Material and unanswered (`Unknown`, `TBD`, `Not applicable`) |

Distinguish a **requirement** (something the user decided) from a **suggested option** (something you offered). Only requirements go in requirement lists; options go in Proposals or Open Questions until chosen.

## 3. Ask well

- Ask **about 3–5 related, high-value questions per round**, grouped under one topic. Lead with the gaps that would change the document most (the problem before the solution; who before what; success before scope detail).
- **Skip** anything already answered, including answers given earlier in the conversation or found in documents. Never re-ask.
- **Adapt.** Each round's questions depend on the previous answers: follow up on surprises, drop branches that no longer apply, open optional sections only when the answers make them relevant. Do not walk a fixed questionnaire and do not force every optional section.
- Offer **suggested options** where they help (`A / B / C / something else`), always with room for free-form answers. Mark options as suggestions.
- Accept **`Unknown`, `TBD` and `Not applicable`** as complete answers. Do not press, and never replace them with plausible-sounding content.
- **Mandatory recap between rounds.** Every time you finish one round of questions and before you ask the next, write a short recap, in this shape, even if the round was small:
  > **Recap so far** — *Decided:* … · *Facts:* … · *Assumptions:* … · *Unknown / TBD (carried forward):* …
  > The recap covers only what the user has said or the documents state (use "none yet" for an empty bucket) and comes **before** the new questions in the same message, so the user can correct it cheaply. Skipping it is not allowed; when the user says "just draft it", the recap is folded into the draft's assumptions and open-questions lists instead.
- If the user answers everything at once or says "just draft it", stop interviewing and draft; list what you had to leave as TBD.

## 4. Draft early, iterate, then write

1. After the first useful round (usually one or two), produce a **substantive Draft**: real sections with real content built from answers, not a skeleton of placeholders.
2. Present, alongside it: the **assumptions** you made, the **open questions / TBDs**, and any **material tradeoffs** that need a human choice.
3. Revise as many times as the user wants.
4. **Obtain the user's go-ahead before writing files.** Only then allocate IDs and write. The document is written as **Draft**; approval is the human's separate decision, and you never set `Approved`.
5. Carry unresolved unknowns into the document visibly (an *Open Questions* section, or `TBD` in place), never as invented specifics.

## 5. Example: two rounds with an explicit TBD

*User:* "We need a way for small clinics to send appointment reminders."

**Round 1** (you have read the project maps; nothing relevant exists):
> I understand this as: clinics need to reduce missed appointments by reminding patients. Before I draft, a few questions about the business problem:
> 1. What is going wrong today — how are reminders handled now, and what does a missed appointment cost?
> 2. Who are the stakeholders (clinic owners, front-desk staff, patients, anyone regulatory)?
> 3. What would make this a success in, say, six months — do you have a target for no-shows?
> 4. Any hard constraints: budget, launch date, regulations on patient contact? *(Options: HIPAA-style privacy rules / regional SMS rules / none known / other)*

*User:* "Front desks phone patients by hand; no-shows are about 15%. Owners and front desk staff. Target: TBD. Privacy rules apply but I don't know which."

**Recap before Round 2 (mandatory):** *Facts:* manual phone reminders; ~15% no-shows; stakeholders owners and front-desk staff. *Unknown (carried forward):* no-show target (TBD); which privacy rules apply. Nothing assumed.

**Round 2** (adapted: skipped stakeholders and problem; targets what the answers opened up):
> 1. Is patient-facing messaging in scope, or only clinic tooling? *(Suggestions: SMS / email / both / not decided)*
> 2. Out of scope for now — for example billing, scheduling itself?
> 3. Who owns finding out which privacy rules apply, and by when?

*User:* "SMS and email. Scheduling and billing are out. Privacy — clinic owner, Unknown timeline."

You now have enough for a **Draft**: present it with the assumption "reminder timing is unspecified" and open questions "no-show target (TBD)" and "applicable privacy rules — owner: clinic owner, date unknown". On the user's go-ahead, write it; the two unknowns appear in the document exactly as unknowns.

## 6. Do not

- Invent business or product decisions, numbers, KPIs, dates, approvals or stakeholders.
- Ask the user to restate what a document already says.
- Present a long exhaustive questionnaire.
- Write files before the user has seen and accepted a draft.
- Move from one question round to the next without the recap.
- Present an unresolved outcome as a verifiable acceptance criterion (see each Skill's `section-catalog.md`): unknown stays `TBD`.
- Perform ID allocation, overlap scoring, map generation or validation yourself: those are `python -m sdlc` commands (`cli-contract.md`).
