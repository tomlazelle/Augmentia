---
id: US-001
title: Turn a title into a URL slug
purpose: Let the blogging tool build readable URLs from post titles.
status: Draft
created: 2026-09-01
updated: 2026-09-01
delivery_status: Not Started
covers: [PR-001-R001]
---

# US-001 — Turn a title into a URL slug

## References

### Derived From
- [PR-001 — Text utilities](../PR/PR-001-text-utilities.md)

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Story

As a blogger, I want post titles turned into slugs, so that my links are readable.

## Scope

### In Scope
- A slug function in the library.

### Out of Scope
- Storing or de-duplicating slugs.

## Acceptance Criteria

1. Slugs look nice and are safe to use in a URL.

## Open Questions

- What should happen with accented or non-Latin characters?
- Is there a maximum slug length?
