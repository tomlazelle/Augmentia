---
id: US-001
title: Turn a title into a URL slug
purpose: Let the blogging tool build readable URLs from post titles.
status: Draft
created: 2026-09-01
updated: 2026-09-29
delivery_status: Ready
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
- A `slugify` function in the library.

### Out of Scope
- Storing or de-duplicating slugs.
- Enforcing a maximum slug length.

## Acceptance Criteria

1. **Given** the title `"Hello World"`, **when** `slugify` is called, **then** it returns `"hello-world"`.
2. **Given** the title `"Hello, World!"`, **when** `slugify` is called, **then** it returns `"hello-world"` (punctuation acts as a separator, collapsed, no leading/trailing hyphen).
3. **Given** the title `"  Multiple   Spaces  "`, **when** `slugify` is called, **then** it returns `"multiple-spaces"`.
4. **Given** the title `"Post 42"`, **when** `slugify` is called, **then** it returns `"post-42"` (digits are preserved, not stripped).
5. **Given** an empty string or a title containing only non-alphanumeric characters (e.g. `"!!!"`), **when** `slugify` is called, **then** it returns `""`.

### Unresolved Acceptance Behavior (TBD)

- **TBD** — How should accented (e.g. `é`) or non-Latin characters be handled: transliterated to ASCII, passed through as Unicode, or stripped as non-ASCII? Owner: Unknown.

## Open Questions

- How should accented or non-Latin characters be handled? (see Unresolved Acceptance Behavior)
