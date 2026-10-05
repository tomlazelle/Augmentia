---
id: DES-001
title: Standard-library slugify
purpose: Design the slugify utility and public export for US-001.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# DES-001 — Standard-library slugify

## References

### Derived From
- [US-001 — Turn a title into a URL slug](../../Stories/US-001-turn-a-title-into-a-url-slug.md) — serves PR-001-R001.

### Related To
- None identified.

### Supporting Artifacts
- None identified.

## Context and Problem

Provide a small title-to-slug helper for readable blog URLs. Storage, de-duplication and maximum slug length are outside the Story's scope.

## Repository Context

### Inspected
- `textkit/text.py` — contains the typed `truncate` helper.
- `textkit/__init__.py` — imports `truncate` and lists it in `__all__`.
- `tests/test_text.py` — pytest tests import the helper from the package root.
- `pyproject.toml`, `README.md` — Python >=3.11 and the documented `python -m pytest -q` command.
- `AGENTS.md`, project maps, US-001 and PR-001 — document conventions, scope and requirements.

### Not Inspected or Unavailable
- Runtime behavior and test execution were not examined; this is a documentation-only design.

## Requirements and Acceptance Traceability

All five decided criteria of US-001 serve PR-001-R001:

| Criterion | Required result | Design responsibility |
|---|---|---|
| AC-1 | `Hello World` → `hello-world` | Lowercase letters and separate words with hyphens. |
| AC-2 | `Hello, World!` → `hello-world` | Treat punctuation as separators, collapse runs and trim boundary hyphens. |
| AC-3 | `  Multiple   Spaces  ` → `multiple-spaces` | Collapse whitespace separators and trim boundaries. |
| AC-4 | `Post 42` → `post-42` | Preserve digits. |
| AC-5 | Empty or non-alphanumeric-only input such as `!!!` → empty string | Permit an empty result after separator removal. |

Proposed validation: add these cases to `tests/test_text.py`, importing `slugify` from `textkit` to also exercise its public export; run the existing pytest suite. Accented/non-Latin behavior remains outside decided test expectations.

## Options Considered

### Option A — Standard-library helper
- **Idea:** Use `re` and string methods in the existing text module.
- **Advantages:** Fits the current helper layout and adds no dependencies.
- **Drawbacks:** Character classification requires an explicit future Unicode policy; a regex alone must not establish that policy accidentally.

## Decision

The user chose implementation in `textkit/text.py` using only `re` and string methods, exported from `textkit/__init__.py` like `truncate`, with no new dependencies.

## Design

### Components and Responsibilities
- `textkit/text.py`: add `slugify(text: str) -> str`, with a docstring, to perform the transformation.
- `textkit/__init__.py`: import `slugify` alongside `truncate` and include both in `__all__`.

### Interfaces and Data Flow

For the decided inputs, lowercase with `str.lower()`, replace runs of punctuation/whitespace separators with one hyphen using `re.sub`, then remove leading/trailing hyphens with `str.strip("-")`. Preserve letters and digits and return the resulting string, including an empty result. Keep character classification inside the helper; the exact regex and any normalization of accented/non-Latin characters remain subject to the open decision below.

## Dependencies

Python standard library only (`re` and string methods); no new dependencies.

## Risks

An ASCII-only character class would implicitly strip accented letters, while Unicode-aware matching could preserve them. Do not interpret either behavior as an accepted contract before the open decision is resolved.

## Assumptions

The proposed interface accepts strings, matching the existing typed helper style. Non-string input behavior is unspecified; a requirement for coercion or explicit validation would require revisiting this assumption.

## Open Decisions

- **TBD:** How accented and non-Latin characters should eventually be handled: transliteration, Unicode preservation or stripping. No policy is selected here. Owner: Unknown. Decision date: Unknown.
