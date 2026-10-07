# M7.3 — Maps, Query and Validate: completion report

Scope: the map behavior started in M7.2 (`update-map`, now subject to the full corpus), `list`, `references`, `find-overlaps`, and `validate` including the R1/R2/R3 rules (front matter, IDs and ledger, links, traceability, maps, Implementation Records, Verification Runs, `Verified` evidence, Publication records, coverage notices). Also recorded: the approved **PARITY-EXCEPTION-004** (YAML parser prose) and **-005** (ASCII-only IDs, implemented as explicit `[0-9]` patterns). No new semantic question arose; no approved contract was changed. M7.4 (status, publishing) is next.

## 1. Results

| Item | Result |
|---|---|
| Node tests (`npm test`, `node:test`) | **34 passed, 0 failed** |
| Applicable frozen-corpus cases | **1,629 of 1,848** (up from 1,351); the remainder are cases of `status`/`publish-*` and every case that runs against the stub `gh` (M7.4), plus 4 non-replayable recordings |
| …exact (JSON by value) | **1,616** |
| …under approved exceptions | **13** (12 × PARITY-EXCEPTION-002 argparse help/usage prose, one per command; 1 × -003 version string) |
| …failed | **0** |
| New this stage | validate 208 (207 exact + 1 exempt), list 17, references 28, find-overlaps 25 (24 + 1), update-map 229 (completed) |
| Python oracle changes | **zero** (`git diff python-1.0.0rc1 -- skill-library/sdlc/` empty); Python suite green: `SDLC_TEST_INSTALL=1` 632 passed, 1 skipped |
| Frozen assets | corpus (`MANIFEST.sha256`) and the two oracle-derived expectation files (`EXPECTATIONS.sha256`) are checksum-locked by Node and Python tests |

## 2. Validator diagnostic coverage

- The CLI contract's validator table lists **54 codes**; the Node source implements **54 of 54** (test `validator-coverage`).
- **54 of 54** are observed in the frozen corpus's validate outputs, each **with exactly the contracted severity** (error/warning/notice), so the replay holds Node to every code, its severity and its message byte for byte.
- Exit behavior: across all recorded validate runs `exit_code` is `1` iff there is at least one error, `0` for warnings/notices alone (never affected), `2` when there is no project; asserted for every recorded run. Counts: more than 50 error-exit runs and more than 50 clean-exit runs.
- Across the whole product the oracle defines 93 result codes (diagnostics, provider errors, status attention kinds); 92 are observed (the 93rd, `bad-artifact`, is unreachable and dropped). The provider and status codes are exercised from M7.4.

## 3. find-overlaps / score parity

- All **25** find-overlaps corpus cases pass (scores, levels, reasons, ordering, `action`).
- Rounding and formatting: **15,020** oracle-generated values (every exact `.2f`/`.3f` tie on grids up to 1/8000 plus 8,000 random numbers) match CPython for `f"{x:.2f}"`, `f"{x:.3f}"` and `round(x, 3)`. Plain JavaScript `toFixed` is wrong on the exact ties (for example 0.125 → "0.13", Python "0.12"), so the port implements round-half-even on the exact binary value.
- Score formula: **4,000** randomized (title, purpose, refs, signal) combinations reproduce the oracle's weighted mean, `round(score, 3)` and displayed `.2f`, bit for bit.
- Tokenisation (lowercasing, stop words, plural stripping): 46 oracle inputs identical.
- A crafted exact-tie project (oracle: score `0.562`, "title similarity 0.12", displayed `0.56`) is held as a regression in both JSON and human output.

## 4. Mutation / sensitivity results

26 deliberate behavior changes to a copy of the compiled Node output, each replayed against the corpus commands it can affect (and against the oracle-derived unit tests): **26 of 26 detected**: 23 by the frozen corpus replay and 3 by oracle-derived tests. The unmutated control copy passes the unit tests (guards against vacuous detection). It includes the `validate` mutations deferred from M7.2 (config returned despite errors, severity changes, exit code, sort rank, uncovered-requirement scope, verified-evidence rule, retired-reference wording, duplicate-ID wording, not-in-ledger severity, dropped TBD warning, Publication provider list) plus ID padding, map text, ledger state, query weights/threshold/tokenisation/skipped-invalid/replaced_by, score rounding, YAML date normalisation, unknown-config-key severity, instruction-file overwrite protection (both guards removed) and the JSON envelope.

The first full run detected 22 of 26. The four misses and their resolution: one mutation text did not match the compiled code (fixed); one removed only one of two redundant overwrite guards (an equivalent mutant; now removes both); and **two genuine insensitivities of the frozen corpus**, plural stripping at word length 4 and the rounding tie cases, were closed with oracle-derived tests. A further sensitivity gap surfaced and was closed the same way: **acceptance-criteria counting after a `###` subsection** (it governs `Verified` validation) is invisible to the recorded corpus; an oracle-confirmed regression test (`ac-counting`) now pins it.

## 5. Newly discovered differences and gaps

- **No behavioral Node/Python difference** was found in any ported command or in any validator code.
- **Corpus sensitivity gaps in the Python-derived corpus** (not Node defects): the three described above. They are now covered by additional frozen, oracle-derived expectations (`numeric-expectations.json`: formatting, scoring, tokenisation) and one oracle-confirmed project test. The frozen corpus itself was not edited.
- The tab/line-break and YAML-prose items from M7.2 still apply (PARITY-EXCEPTION-004 now approved; `!!binary`/`!!set` and U+2028 folding remain documented non-contract limitations).

## 6. Proposed parity exceptions

None.
