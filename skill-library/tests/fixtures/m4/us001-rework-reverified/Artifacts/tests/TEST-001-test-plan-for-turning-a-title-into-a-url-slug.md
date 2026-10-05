---
id: TEST-001
title: Test plan for turning a title into a URL slug
purpose: Map US-001's decided acceptance criteria for slugify to automated test scenarios.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# TEST-001 — Test plan for turning a title into a URL slug

## References

### Derived From
- [US-001 — Turn a title into a URL slug](../../Stories/US-001-turn-a-title-into-a-url-slug.md) — serves PR-001-R001.

### Related To
- [DES-001 — Standard-library slugify](../design/DES-001-standard-library-slugify.md)
- [PLAN-001 — Implement slugify for US-001](../plans/PLAN-001-implement-slugify-for-us-001.md)

### Supporting Artifacts
- None identified.

## Scope

- Covers US-001's decided acceptance criteria AC-1 through AC-6 for the `slugify` function: lowercase-and-hyphenate, punctuation treated as a separator (collapsed, no leading/trailing hyphen), whitespace collapse, digit preservation, empty result for empty or non-alphanumeric-only input, and collapsing a run of mixed symbol characters (e.g. `++`) into a single separator.
- Excludes accented/non-Latin character handling (TBD in US-001 and DES-001) and storage, de-duplication or maximum slug length (out of scope per US-001).

## Test Scenarios

### TS-1 — Simple two-word title
- **Criterion:** AC-1 — Given the title `"Hello World"`, when `slugify` is called, then it returns `"hello-world"`.
- **Method:** automated
- **Setup:** None; call `slugify` directly.
- **Steps:** `from textkit import slugify; slugify("Hello World")`
- **Expected result:** `"hello-world"`
- **Evidence to capture:** pytest output (pass/fail) and exit code from `python -m pytest -q`.

### TS-2 — Punctuation treated as separator
- **Criterion:** AC-2 — Given the title `"Hello, World!"`, when `slugify` is called, then it returns `"hello-world"` (punctuation acts as a separator, collapsed, no leading/trailing hyphen).
- **Method:** automated
- **Setup:** None; call `slugify` directly.
- **Steps:** `slugify("Hello, World!")`
- **Expected result:** `"hello-world"`
- **Evidence to capture:** pytest output (pass/fail) and exit code from `python -m pytest -q`.

### TS-3 — Collapsing multiple/leading/trailing spaces
- **Criterion:** AC-3 — Given the title `"  Multiple   Spaces  "`, when `slugify` is called, then it returns `"multiple-spaces"`.
- **Method:** automated
- **Setup:** None; call `slugify` directly.
- **Steps:** `slugify("  Multiple   Spaces  ")`
- **Expected result:** `"multiple-spaces"`
- **Evidence to capture:** pytest output (pass/fail) and exit code from `python -m pytest -q`.

### TS-4 — Digits preserved
- **Criterion:** AC-4 — Given the title `"Post 42"`, when `slugify` is called, then it returns `"post-42"` (digits are preserved, not stripped).
- **Method:** automated
- **Setup:** None; call `slugify` directly.
- **Steps:** `slugify("Post 42")`
- **Expected result:** `"post-42"`
- **Evidence to capture:** pytest output (pass/fail) and exit code from `python -m pytest -q`.

### TS-5 — Empty or non-alphanumeric-only input
- **Criterion:** AC-5 — Given an empty string or a title containing only non-alphanumeric characters (e.g. `"!!!"`), when `slugify` is called, then it returns `""`.
- **Method:** automated
- **Setup:** None; call `slugify` directly with both `""` and `"!!!"`.
- **Steps:** `slugify("")` and `slugify("!!!")`
- **Expected result:** `""` for both inputs.
- **Evidence to capture:** pytest output (pass/fail) and exit code from `python -m pytest -q`.

### TS-6 — Symbol run collapsed to a single separator
- **Criterion:** AC-6 — Given the title `"C++ Tips"`, when `slugify` is called, then it returns `"c-tips"`.
- **Method:** automated
- **Setup:** None; call `slugify` directly.
- **Steps:** `slugify("C++ Tips")`
- **Expected result:** `"c-tips"`
- **Evidence to capture:** pytest output (pass/fail) and exit code from `python -m pytest -q`.

## Failure, Boundary and Regression Cases

- **Public export regression:** `slugify` must be importable from the package root, matching the existing `truncate` pattern. Method: automated. Steps: `python -c "from textkit import slugify"`. Expected result: import succeeds with exit code 0.
- **Existing suite regression:** The pre-existing `truncate` tests in `tests/test_text.py` must continue to pass after `slugify` is added, so the change does not regress unrelated behavior. Method: automated. Steps: `python -m pytest -q`. Expected result: all tests, including the three existing `truncate` tests, pass.

## Unresolved Acceptance Behavior (TBD)

- **TBD** — How should accented (e.g. `é`) or non-Latin characters be handled: transliterated to ASCII, passed through as Unicode, or stripped as non-ASCII? No test scenario or expected result is defined for this until the Story decides it. Owner: Unknown.

## Verification Runs

### VR-1 — 2026-09-29T23:31:41Z

- **Story:** US-001
- **Kind:** automated
- **Result:** passed
- **Criteria:** AC-1, AC-2, AC-3, AC-4, AC-5
- **Environment:** Python 3.11.16, pytest 9.1.1, Linux, repo root, working tree matching Implementation Record IR-1 (uncommitted)
- **Performed By:** agent (Claude Code, verify-story)
- **Command:** `python -m pytest -q -v`
- **Exit Code:** 0
- **Observed:** `9 passed in 0.01s` (3 pre-existing `truncate` tests + 6 `slugify` tests covering AC-1–AC-5, with AC-5 exercised by both the empty-string and punctuation-only test cases). Full log: [TEST-001-VR-1-pytest.log](evidence/TEST-001-VR-1-pytest.log).
- **Superseded:** yes — Story changed 2026-09-29 (added AC-6).

### VR-2 — 2026-09-29T23:31:41Z

- **Story:** US-001
- **Kind:** automated
- **Result:** passed
- **Criteria:** none
- **Environment:** Python 3.11.16, Linux, repo root, working tree matching Implementation Record IR-1 (uncommitted)
- **Performed By:** agent (Claude Code, verify-story)
- **Command:** `python -c "from textkit import slugify"`
- **Exit Code:** 0
- **Observed:** Public-export regression case: `slugify` imports successfully from the package root, matching the existing `truncate` pattern. Full log: [TEST-001-VR-2-import.log](evidence/TEST-001-VR-2-import.log).
- **Superseded:** yes — Story changed 2026-09-29 (added AC-6).

### VR-3 — 2026-09-29T23:52:28Z

- **Story:** US-001
- **Kind:** automated
- **Result:** passed
- **Criteria:** AC-1, AC-2, AC-3, AC-4, AC-5, AC-6
- **Environment:** Python 3.11.16, pytest 9.1.1, Linux, repo root, working tree matching Implementation Record IR-2 (uncommitted)
- **Performed By:** agent (verify-story)
- **Command:** `python -m pytest -q -v`
- **Exit Code:** 0
- **Observed:** `10 passed in 0.01s` (3 pre-existing `truncate` tests + 7 `slugify` tests covering AC-1–AC-6, with AC-5 exercised by both the empty-string and punctuation-only test cases, and AC-6 newly exercised by `test_slugify_collapses_symbol_runs`). Full log: [TEST-001-VR-3-pytest.log](evidence/TEST-001-VR-3-pytest.log).

### VR-4 — 2026-09-29T23:52:28Z

- **Story:** US-001
- **Kind:** automated
- **Result:** passed
- **Criteria:** none
- **Environment:** Python 3.11.16, Linux, repo root, working tree matching Implementation Record IR-2 (uncommitted)
- **Performed By:** agent (verify-story)
- **Command:** `python -c "from textkit import slugify"`
- **Exit Code:** 0
- **Observed:** Public-export regression case: `slugify` imports successfully from the package root, matching the existing `truncate` pattern. This is a supporting regression check and does not itself exercise AC-1–AC-6. Full log: [TEST-001-VR-4-import.log](evidence/TEST-001-VR-4-import.log).
