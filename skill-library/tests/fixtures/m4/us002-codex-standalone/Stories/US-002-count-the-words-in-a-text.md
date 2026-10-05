---
id: US-002
title: Count the words in a text
purpose: Let callers know how many words a piece of text contains.
status: Draft
created: 2026-09-01
updated: 2026-09-29
delivery_status: Verified
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
2. **Given** an empty string or only whitespace, **when** `word_count` is called, **then** it returns 0.

## Open Questions

- None.

## Implementation Record

### IR-1 — 2026-09-29
- **Summary:** Added public `word_count` using whitespace-separated tokens and all nine input cases from TEST-001 TS-1 through TS-3; retained the three truncation regression tests. No deviations or unresolved acceptance behavior.
- **Files changed:** `textkit/text.py`, `textkit/__init__.py`, `tests/test_text.py`, `Stories/US-002-count-the-words-in-a-text.md`
- **Ref:** working tree (uncommitted)
- **Tests run:** `python -m pytest -q` → exit 0 — 12 passed in 0.01s.
