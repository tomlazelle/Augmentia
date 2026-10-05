### USER

Use the create-prd skill. Product idea: a shared shopping list for households, where members add items and see what others have added. There is no business requirements document and I don't want one. Ask me your first questions; don't write yet.

### AGENT (claude -p, project skills via install/claude_code.py)

No BRDs exist yet, so I'll proceed independently. Let's start with the basics:

1. **Users**: Who's using this — household members generally? Any roles like an "owner" who creates the household vs. members who join? Any secondary users (e.g., guests, kids with limited access)?

2. **Core need today**: How do households currently keep a shared shopping list (paper list on the fridge, a notes app, texting each other)? What's breaking about that, that this product should fix?

3. **Primary journey**: Walk me through the main flow — someone realizes they're out of milk, adds it to the list; who sees it next, and when/how does it get resolved (marked bought, removed)?

4. **Household structure**: Is a "household" a fixed group people explicitly join (invite-based), or something looser? Can someone belong to more than one household (e.g., their own place + parents')?

5. **First release focus**: Of everyone who'd use this, which single user type matters most to get right for v1 — e.g., the person adding items, or the person shopping and checking things off?

### USER

1. Household members, any of them; one creator/owner who invites others; no guest role in v1. 2. Today they text each other; lists get lost and items get bought twice. 3. Someone adds 'milk'; others see it; whoever shops ticks it off, and it moves to a bought section. 4. Invite-based; one household per person in v1, multiple TBD. 5. The person shopping and checking items off matters most. Not decided: offline use, notifications, quantities - all TBD. Skip the draft review and write it now, but keep the TBDs as open questions.

### AGENT (claude -p, project skills via install/claude_code.py)

Written and validated clean (0 errors, 0 warnings — the 6 notices are expected until Stories exist).

**PR-001 — Shared Household Shopping List**, status `Draft`, at `PR/PR-001-shared-household-shopping-list.md`

Requirements: PR-001-R001 through R006 (household creation/invite, add item, view list, mark bought, bought section, one-household-per-user v1).

Open questions carried forward as TBD: whether to show who added/bought each item, offline use, notifications, item quantities, exact invite mechanism, multi-household support later.

Next steps: I can run `create-stories` to turn these requirements into user stories whenever you're ready. Approval of the PRD itself is your call — let me know when you want it marked `Approved`.

