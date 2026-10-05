---
id: US-002
title: Count the words in a text
purpose: Let callers know how many words a piece of text contains.
status: Draft
created: 2026-09-01
updated: 2026-09-01
delivery_status: Ready
covers: []
---

# US-002 — Count the words in a text

## References

### Derived From
- None identified.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Story

As a blogger, I want to know how many words a text has, so that I can show a reading-time estimate.

## Scope

### In Scope
- A `word_count` function in the library.

### Out of Scope
- Reading-time estimation itself.

## Acceptance Criteria

1. **Given** the text "one two  three", **when** `word_count` is called, **then** it returns 3 (runs of whitespace separate words).
2. **Given** an empty string or only whitespace, **when** `word_count` is called, **then** it returns 0 (a text of only whitespace also returns 0).

## Open Questions

- None.
