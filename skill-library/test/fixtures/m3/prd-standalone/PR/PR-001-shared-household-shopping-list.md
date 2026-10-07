---
id: PR-001
title: Shared Household Shopping List
purpose: Let household members maintain one shared shopping list so items are added once, seen by everyone, and not bought twice.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# PR-001 — Shared Household Shopping List

## References

### Derived From
- None identified.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Product Summary

A shared shopping list for households. Any member of a household can add items to a single list that every other member can see, so the household stops relying on texting each other and no longer buys the same item twice or forgets one entirely. Whoever is shopping checks items off as they buy them, moving them to a bought section.

## Target Users and Needs

| User | Needs and goals |
|---|---|
| Household member | Add an item they've noticed is needed, and see what others have already added, without texting the household. |
| Shopper (a household member while shopping) | See the current list, know what's still needed, and mark items bought as they go so others see it's handled. |
| Household owner | Create the household and invite the other members into it. |

## User Journeys and Use Cases

1. **Adding an item** — A household member notices they're out of something (e.g., milk) and adds it to the shared list. It appears on the list for all other household members to see.
2. **Shopping and checking off** — A member shopping opens the list, buys items on it, and marks each as bought. Bought items move to a bought section, signaling to the rest of the household that the item has been handled.
3. **Creating a household and inviting members** — A user creates a household, becoming its owner, and invites others to join it. Invited members join and gain access to the shared list. (Invite mechanism: TBD.)

## Behavior and Capabilities

- Any member of a household can add an item to that household's shared list.
- All members of a household can see every item on the list. Whether the list shows who added or bought each item is not yet decided (see Open Questions).
- Any member can mark an item as bought; bought items move to a distinct bought section rather than being deleted.
- A household has exactly one owner, who creates the household and invites other members.
- In v1, a user belongs to exactly one household, and only invited members have access to it — there is no guest or view-only role.

## Scope

### MVP (In Scope)
- Creating a household (owner) and inviting members to join it.
- Adding items to the household's shared list.
- Viewing the shared list as any household member.
- Marking items as bought, moving them to a bought section.

### Out of Scope / Later
- Guest or view-only roles.
- Belonging to more than one household at once.
- Item quantities, notes, or categories.
- Notifications (e.g., when an item is added or bought).
- Offline use / offline sync.

## Product Requirements

- **PR-001-R001** — A household owner can create a household and invite other members to join it.
- **PR-001-R002** — Any household member can add an item to their household's shared shopping list.
- **PR-001-R003** — Every household member can view all items currently on their household's shared list.
- **PR-001-R004** — Any household member can mark an item as bought.
- **PR-001-R005** — Bought items move to a distinct bought section rather than being removed from the list.
- **PR-001-R006** — In v1, each user belongs to exactly one household, and only invited members can access it (no guest role).

## Acceptance Expectations

- A household owner can create a household and successfully invite another member, who gains access to the same list.
- An item added by one member is visible to every other member of the household.
- An item marked bought by any member appears in the bought section for every member, and is no longer shown as outstanding.

## Constraints and Dependencies

- TBD — no platform, integration, or timeline constraints identified yet.

## Assumptions and Open Questions

- **Assumption:** "Household" is a fixed group that a user joins by invitation from the owner, not an open or discoverable group.
- **Assumption:** The bought section is part of the same shared list view, not a separate history/archive feature.
- **Open question:** Should the list show who added or bought each item? Unknown — not raised in discovery.
- **Open question:** Is offline use required (e.g., adding items with no connectivity)? TBD.
- **Open question:** Are notifications needed when items are added or bought, and if so, which channel? TBD.
- **Open question:** Do items need quantities (e.g., "2 milk") or is a plain item name sufficient for v1? TBD.
- **Open question:** Exact invite mechanism (e.g., invite link, email, code) is undecided.
- **Open question:** Should users eventually belong to multiple households? Deferred past v1, no owner/date set.
