# M7.4 report — status, publishing, GitHub provider, canonical digest

Scope: `status`, `publish-preview`, `publish-apply`, the GitHub provider, the canonical digest. Oracle: Python `python-1.0.0rc1`. No live GitHub Issue was created (stub `gh` only).

## Results

| Item | Result |
|---|---|
| Applicable corpus cases | **1,844 of 1,848** (4 are monkeypatch-only, non-replayable; an equivalent filesystem-induced case is in the corpus) |
| Corpus outcome | 1,831 exact + 13 exempt (12 argparse help/usage, 1 version) = 1,844 passed, **0 failed** |
| M7.4 commands | status 35, publish-preview 72, publish-apply 44 — all pass (stdout/stderr/exit/post tree/gh call log) |
| Node tests | **91 tests, 91 pass** (corpus replay included) |
| Python oracle | `sdlc/` unchanged vs `python-1.0.0rc1`; default suite 623 passed/10 skipped; `SDLC_TEST_INSTALL=1` 632 passed/1 skipped; Python replay clean |
| Unexplained differences | **none** |

## Digest equality (absolute)

- 81 digest-bearing corpus runs, 29 distinct digests: every digest and every Story item (title, body, action, known publication) is byte-identical to the oracle's (`test/digest-parity.test.ts`).
- Digest matrix (`parity/digest-matrix.json`, generated from the oracle, frozen in `EXPECTATIONS.sha256`): 26 scenarios, Node digest equals the oracle digest in 26/26.
- Canonical form: SHA-256 of sorted-key compact UTF-8 JSON of `{provider, repository, stories:[{id, action, title, body, known}]}`.

## Digest sensitivity

14 scenarios must change the digest (Story body, title, target repository, provider-visible publication metadata for the same repository, selection, action) — all changed. 12 must not (status/delivery_status, Implementation and Review records, other-repository publication records, `updated`, unrelated Stories, etc.) — all unchanged. Matches the oracle in every case.

## Provider / stub failure matrix (`test/provider.test.ts`, `publish-semantics`)

| Failure | Result |
|---|---|
| `gh` missing; non-executable; path is a directory; bad shebang; unreadable directory | `provider-unavailable`, exit 1, no traceback, nothing changed (PARITY-EXCEPTION-001) |
| Not authenticated | `provider-auth` |
| Repository not found; issues disabled; repo error | existing preflight classes, nothing created |
| Repo-view JSON that is not an object | `provider-failed` (proposed EX-006; Python crashes) |
| Malformed JSON | provider-failed unexpected response |
| Timeout (injected, deterministic) | `provider-failed … timed out after 60s` |
| Create forbidden / auth text | `provider-auth` vs `provider-failed` classification as oracle |
| Create without URL | `provider-ambiguous`; run stops, no blind retry |
| Partial success | per-Story outcomes reported |
| Record write fails after create | INCONSISTENCY reported, never retried |

## Publication-record parity, duplicates, strictness

- Apply mutates only the Story `updated` date and appends `PUB-n`; status/delivery_status untouched (exact record diff test). Hand-edited duplicate same-repo records: latest shown, same as oracle (verified directly against the oracle).
- Identity is Story + provider + repository: same repo → SKIP; another repo → CREATE with a `published-elsewhere` notice and its own `PUB-2`; both known afterwards → nothing created.
- Digest authorizes only exact state: changed body/title/repo/selection/known publication → `preview-stale`, nothing written; missing digest → `confirmation-missing`.
- Preview is offline: zero provider calls, zero file changes.

## Redaction and secrets

Every token shape is redacted from provider diagnostics; a token in provider output or the environment never reaches stdout, stderr, project files or the call log. `evidence-secrets` scans docs/parity/fixtures for token-shaped strings: none (stub sources build the fake token from two literals).

## PARITY-EXCEPTION-001 evidence

Oracle with a non-executable `gh`: exit 1, uncaught `PermissionError: [Errno 13] Permission denied` traceback. Node normalizes five spawn-failure mechanisms (not only EACCES) to `provider-unavailable`. **EX-006 is proposed** (see `parity/EXCEPTIONS.md`): oracle crashes with `AttributeError: 'list' object has no attribute 'get'` on a JSON-array repo view.

## Mutation sensitivity

51 deliberate Node mutations (26 earlier + 25 new M7.4: digest form/order/hash/body/repository, stale and missing confirmation, identity, latest-record, notices, Issue body, record numbering/layout/date, provider classes, redaction, EX-001/EX-006, status ordering/TBD/verification). The first run missed 2 (one equivalent mutant, one unobserved behavior); the mutant was replaced and a test added, oracle-verified. Final: all detected (the re-run of the two corrected mutations caught; remaining 49 caught).

## Dead-code register

`publish.py:175-178` and `204-209`, `_bump_updated` fallbacks ported as-is (uncertain); `Publication.number` dropped. See `parity/DROPPED.md`.
