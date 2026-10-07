---
id: PLAN-001
title: Implement slugify for US-001
purpose: Implement the slugify text helper per DES-001 to satisfy US-001's decided acceptance criteria.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# PLAN-001 — Implement slugify for US-001

## References

### Derived From
- [US-001 — Turn a title into a URL slug](../../Stories/US-001-turn-a-title-into-a-url-slug.md) — serves PR-001-R001.

### Related To
- [DES-001 — Standard-library slugify](../design/DES-001-standard-library-slugify.md)

### Supporting Artifacts
- None identified.

## Scope

- Delivers US-001's decided acceptance criteria AC-1 through AC-5 (lowercase and hyphenate; treat punctuation as a separator and collapse/trim it; collapse whitespace; preserve digits; return an empty string for empty or non-alphanumeric-only input).
- Excludes accented/non-Latin character handling (TBD in US-001 and DES-001) and storage, de-duplication or maximum slug length (out of scope per US-001).

## Repository Context

### Inspected
- `textkit/text.py` — contains the typed `truncate(text: str, width: int, suffix: str = "…") -> str` helper; establishes the typed, docstring style to follow for `slugify`.
- `textkit/__init__.py` — imports `truncate` and lists it in `__all__`; the pattern `slugify` must follow for export.
- `tests/test_text.py` — pytest tests import helpers from the package root (`from textkit import truncate`), one test function per case.
- `pyproject.toml` — Python `>=3.11`, `testpaths = ["tests"]`.
- `README.md` — documents `python -m pytest -q` as the test command.

### Not Inspected or Unavailable
- Runtime behavior and test execution have not been performed; no code has been written or run yet.

## Approach

Follow DES-001's decision (Option A — standard-library helper): add `slugify(text: str) -> str` to `textkit/text.py` using only `re` and string methods — lowercase with `str.lower()`, replace runs of punctuation/whitespace separators with a single hyphen via `re.sub`, then strip leading/trailing hyphens with `str.strip("-")`. Export it from `textkit/__init__.py` alongside `truncate`. No new dependencies.

## Steps

1. **Add `slugify` to `textkit/text.py`** — Files: verified: `textkit/text.py`. Depends on: none. Check: manual review that the function has a type signature and docstring matching the `truncate` style.
2. **Export `slugify` from the package** — Files: verified: `textkit/__init__.py`. Depends on: step 1. Check: `python -c "from textkit import slugify"`.
3. **Add AC-1–AC-5 test cases to `tests/test_text.py`** — Files: verified: `tests/test_text.py`. Depends on: step 2. Check: `python -m pytest -q tests/test_text.py`.
4. **Run the full test suite** — Files: none (verification only). Depends on: step 3. Check: `python -m pytest -q`.

## Acceptance-to-Test Mapping

| Acceptance criterion | Test or check | Command |
|---|---|---|
| AC-1: `"Hello World"` → `"hello-world"` | New case in `tests/test_text.py` | `python -m pytest -q` |
| AC-2: `"Hello, World!"` → `"hello-world"` | New case in `tests/test_text.py` | `python -m pytest -q` |
| AC-3: `"  Multiple   Spaces  "` → `"multiple-spaces"` | New case in `tests/test_text.py` | `python -m pytest -q` |
| AC-4: `"Post 42"` → `"post-42"` | New case in `tests/test_text.py` | `python -m pytest -q` |
| AC-5: `""` or `"!!!"` → `""` | New case(s) in `tests/test_text.py` | `python -m pytest -q` |

## Validation Commands

- `python -m pytest -q` — runs the full suite, including the new `slugify` cases; not yet run (proposed).

## Risks

- Choosing an ASCII-only punctuation/whitespace character class in the regex could implicitly decide the still-open accented/non-Latin question by stripping such characters. Mitigation: restrict the regex to ASCII punctuation and whitespace only for the decided cases, and do not treat any resulting behavior on accented input as an accepted contract.

## Open Questions

- How should accented (e.g. `é`) or non-Latin characters be handled: transliterated, preserved as Unicode, or stripped? Owner: Unknown (carried from US-001 and DES-001).
