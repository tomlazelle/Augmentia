---
id: TEST-001
title: Word counting tests for US-002
purpose: Test the decided word counting acceptance criteria for US-002.
status: Draft
created: 2026-09-29
updated: 2026-09-29
---

# TEST-001 — Word counting tests for US-002

## References

### Derived From
- [US-002 — Count the words in a text](../../Stories/US-002-count-the-words-in-a-text.md) — AC-1 and AC-2; the Story has `covers: []`, so no covered requirement IDs are asserted.

### Related To
- [PR-001 — Text utilities](../../PR/PR-001-text-utilities.md) — PR-001-R002 describes word counting; contextual relationship only, since US-002 does not declare coverage.

### Supporting Artifacts
- None identified. No Design or Implementation Plan is required or supplied.

## Scope

- Cover US-002 AC-1 (runs of whitespace separate words) and AC-2 (empty or whitespace-only input returns zero).
- Exclude reading-time estimation. Non-string inputs, punctuation-specific tokenization and performance limits have no decided acceptance outcomes and are not release gates in this plan.
- Decision: use the project command `python -m pytest -q`, as supplied by the user and documented in the README.
- Proposal: add pytest cases to the existing `tests/test_text.py`. These cases are planned, not implemented by this document.
- Assumption: expose `word_count` through `textkit`, following the existing public import convention for `truncate`; this is a proposed test integration choice, not an additional acceptance criterion.
- No material tradeoffs or unresolved outcomes affect the two decided criteria.

## Repository Context

- **Inspected:** `textkit/text.py`, `textkit/__init__.py`, `tests/test_text.py`, `pyproject.toml`, `README.md`, `AGENTS.md`, `CLAUDE.md`, root and artifact maps, US-002 in full, and PR-001 in full; Git status and latest commit.
- **Observed:** the library implements and exports only `truncate`; the three existing pytest cases cover unchanged short text, truncation with a suffix, and an invalid width. There are no existing word-count tests. Configuration requires Python 3.11 or newer and collects tests from `tests/`.
- **Not inspected / unavailable:** no Design or Implementation Plan exists. Runtime behavior and dependency availability were not tested during test planning.
- **Environment for future execution:** use Python 3.11 or newer with pytest available, run from the repository root, and make the library importable. No external services or fixtures are proposed.

## Test Scenarios

### TS-1 — Count words separated by whitespace runs
- **Criterion:** AC-1 — given `"one two  three"`, `word_count` returns 3; runs of whitespace separate words.
- **Method:** automated.
- **Setup:** proposed parametrized pytest cases in `tests/test_text.py`; implemented and importable `word_count`. Include `"one two  three"`, `"one\ttwo\nthree"`, and `"  one \t two\nthree  "`.
- **Steps:** call `word_count` for each input, assert the expected count, and execute `python -m pytest -q` from the repository root.
- **Expected result:** each input returns 3. Repeated, mixed, leading and trailing whitespace does not create additional words.
- **Evidence to capture:** test cases and their input assertions, code revision, exact command, UTC timestamp, Python/pytest environment, exit code and complete output log; future verification must establish that these cases were collected and executed.

### TS-2 — Empty text contains no words
- **Criterion:** AC-2 — an empty string returns 0.
- **Method:** automated.
- **Setup:** proposed pytest case in `tests/test_text.py` using `""`; implemented and importable `word_count`.
- **Steps:** assert `word_count("") == 0`, then execute `python -m pytest -q` from the repository root.
- **Expected result:** the function returns 0.
- **Evidence to capture:** test assertion, code revision, exact command, UTC timestamp, Python/pytest environment, exit code and complete output log showing the case executed.

### TS-3 — Whitespace-only text contains no words
- **Criterion:** AC-2 — whitespace-only input returns 0.
- **Method:** automated.
- **Setup:** proposed parametrized pytest cases in `tests/test_text.py` using `" "`, `"   "`, `"\t"`, `"\n"`, and `" \t\r\n "`; implemented and importable `word_count`.
- **Steps:** call `word_count` for each input and assert zero; execute `python -m pytest -q` from the repository root.
- **Expected result:** each input returns 0.
- **Evidence to capture:** parametrized inputs and assertions, code revision, exact command, UTC timestamp, Python/pytest environment, exit code and complete output log showing the cases executed.

## Failure, Boundary and Regression Cases

- AC-1: TS-1 guards against treating each space as a word separator that produces empty words, or recognizing only literal spaces rather than whitespace runs.
- AC-2: TS-2 and TS-3 cover zero-content boundaries, including mixed whitespace.
- Supporting regression checks: retain the existing tests asserting `truncate("hello", 10) == "hello"`, `truncate("hello world", 8) == "hello w…"`, and `truncate("hello", 0)` raises `ValueError`. These run with the same project command but do not demonstrate a US-002 acceptance criterion.
- A successful run of only the existing truncation tests cannot verify US-002. Missing word-count implementation or missing proposed tests must be reported as an evidence gap during future verification.

## Verification Runs

### VR-1 — 2026-09-29T23:56:59Z
- **Story:** US-002
- **Kind:** automated
- **Result:** passed
- **Criteria:** AC-1, AC-2
- **Command:** `python -m pytest -q`
- **Exit code:** 0
- **Environment:** Python 3.11.16, pytest 9.1.1, Linux-7.0.0-34-generic-x86_64-with-glibc2.43; repository root.
- **Performed by:** agent (Codex exec_command)
- **Observed:** 12 passed in 0.01s, with no skipped cases. Inspected `tests/test_text.py` contains exactly those 12 cases: TS-1's three whitespace-separated inputs (AC-1), TS-2's empty string and TS-3's five whitespace-only inputs (AC-2), plus three truncation regressions. All nine planned word-count cases executed and passed; truncation regressions are supporting checks only. No manual checks or unresolved acceptance behavior remain.
- **Ref:** working tree (uncommitted) based on HEAD `5d5b3dd11dd40795e48fa27508fc6390ce4fb7d5`; inspected code and tests match IR-1's description. IR-1 has no immutable snapshot to prove byte-for-byte identity, so this run establishes fresh evidence for the current files. Source contents and SHA256 hashes are captured in the log.
- **Evidence:** [Full output, environment and source snapshot](evidence/US-002-20260929T235659Z.log)
