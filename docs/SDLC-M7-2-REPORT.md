# M7.2 — Node Core: completion report

Scope (per the M7 plan and your M7.1 gate message): TypeScript/Node scaffold; frontmatter/Markdown/model/project infrastructure; ledger and ID mechanics; `init`, `allocate-id`, `retire-id`, `create-dir`; CLI skeleton, `--json` envelope, exit-code behavior. `update-map` and the whole map generator were also ported because `init` and `create-dir` depend on them (they were scheduled for M7.3; nothing else from M7.3+ was started). No human gate is requested: no contract question was found.

## 1. Results

| Item | Result |
|---|---|
| Node tests (`node:test`, `npm test`) | **24 passed, 0 failed** (7 CLI, 4 Markdown, 7 Python-compat helpers, 4 YAML-oracle suites, 2 corpus gates) |
| Applicable frozen-corpus cases | **1,351 of 1,848** (the rest belong to commands not yet ported: list, references, find-overlaps, validate, status, publish-*; and 4 non-replayable recordings) |
| …passed byte-for-byte (JSON by value) | **1,342** |
| …passed under an approved exemption | **9** (8 × PARITY-EXCEPTION-002 argparse help/usage prose; 1 × PARITY-EXCEPTION-003 version string) |
| …failed | **0** |
| By command | init 295 (293 + 2 exempt), allocate-id 713 (710 + 3), retire-id 26 (25 + 1), create-dir 87 (86 + 1), update-map 229 (228 + 1), `--version` 1 (exempt) |
| YAML parity vs the oracle (`parity/yaml-expectations.json`, generated from Python/PyYAML) | 133 parse inputs: **every one of the 97 that PyYAML accepts is reproduced exactly** (except 3 documented rare-type gaps below); all 36 rejected inputs are rejected; **31 of 36 error messages identical**; 96 of 96 emitted `config.md` texts **byte-identical** to `yaml.safe_dump` for names including quotes, colons, emoji, >80-character names, control characters |
| Python oracle changes | **zero**: `git diff python-1.0.0rc1 -- skill-library/sdlc/` is empty; the Python suite is unchanged (622 passed, 10 skipped) |
| Corpus integrity | frozen: `MANIFEST.sha256` verified by a Node test and a Python test; no expectation was generated from Node |
| Dependencies | one runtime dependency (`yaml` 2.x); dev-only `typescript` 5, `@types/node` 22 |

Replay time for the applicable corpus is about 30 seconds on 8 workers. Sensitivity: injecting defects into the compiled Node output (ID padding, an empty-map sentence, a ledger state string) is detected by the corpus replay (317, 448 and 593 failing cases respectively). Two injected changes were not detected: removing the exclusive-create flag (an equivalent mutant, because the `lexists` guard in front of it already prevents overwriting, exactly as in Python) and returning the parsed config despite config errors (that behavior is observable only through `validate`, M7.3).

## 2. What was built (`skill-library/node/`)

`src/`: `pyfmt.ts` (Python-compatible whitespace/strip/split, `repr`, `quote`/`unquote`, code-point ordering, `Path.resolve`, universal-newline reads, atomic writes), `yaml.ts` (PyYAML-exact implicit typing, constructors, merge keys, timestamps and scanner rules over the `yaml` package's failsafe AST; a port of PyYAML's scalar emitter for `config.md`), `model.ts`, `frontmatter.ts`, `markdown.ts`, `ledger.ts`, `project.ts` (config loading, document loading and front-matter validation with the exact diagnostics), `ids.ts`, `maps.ts`, `init.ts`, `resources.ts`, `cli.ts` (argparse-compatible option parsing, JSON envelope, human output), `version.ts`; `bin/sdlc.js`; `test/` (unit tests, corpus replayer, YAML oracle tests); `scripts/sync-assets.mjs` (copies the instruction templates next to the build while Python still owns them). Layout adjustment recorded in the plan: the Node project lives in `skill-library/node/` until Python is removed.

## 3. Parity exceptions encountered

- **PARITY-EXCEPTION-002** (approved): 8 corpus cases are argparse help/usage text; the Node CLI satisfies the required exit code (2 for usage errors, 0 for help), recognizes every command and flag, includes the flag names in its own deterministic text, and prints `usage:`/`error:` lines.
- **PARITY-EXCEPTION-003** (approved): `sdlc --version` prints `sdlc 2.0.0-rc.1`.
- PARITY-EXCEPTION-001 (spawn failure of `gh`) does not arise until the provider is ported in M7.4; its Node regression test is scheduled there.

## 4. Unexpected Python/Node differences found (and how each was resolved)

Two were behavioral and were fixed to match the oracle: PyYAML treats a tab outside quoted scalars, comments and block scalars as an error (tab after `:`, inside flow collections, between words of a plain scalar), and treats `\x85`/` `/` ` as line breaks except inside quoted scalars; the `yaml` package does neither. Both rules are now implemented and tested against 19 added oracle inputs.

Remaining known differences (all outside the corpus, none silently chosen; the two proposed exceptions are recorded in `parity/EXCEPTIONS.md`):

1. **YAML error prose** (PARITY-EXCEPTION-004, proposed): 5 of 36 oracle error inputs still differ in the text after `invalid YAML:` (`a: [` → Python "while parsing a flow node", Node "while parsing a flow sequence"; four "simple key" cases). Error classification and every `invalid YAML value:` message are exact. The two prose messages that occur in the corpus are reproduced.
2. **Unicode shorthand classes** (PARITY-EXCEPTION-005, proposed): `\d` in ID patterns is ASCII in Node; Python also accepts non-ASCII decimal digits by accident.
3. **Rare YAML types**: `!!binary` and `!!set` raise an error in Node (Python constructs bytes/sets); never used in front matter.
4. **Plain scalar folded across a literal U+2028/U+2029** keeps that character in PyYAML but folds to a space in Node.
5. **JavaScript number model**: floats and integers are both numbers (`5.` and `5` are indistinguishable) and integer-like mapping keys sort first; neither affects any diagnostic that can occur for a valid document.

## 5. Dropped/ported-as-uncertain code (register: `parity/DROPPED.md`)

Dropped in M7.2: `bad-artifact` (argparse `choices` makes it unreachable; the Node parser validates the same closed set at the CLI layer, covered by the usage-error test). Ported as uncertain (kept until proven dead): the empty-message YAML fallback, `Outcome`'s `None` diagnostics default, and `Project.rel()`'s out-of-root fallback.

## 6. Contract changes proposed

None. Two parity exceptions (004, 005) are proposed for recording; the defaults described above are in effect and cost nothing if approved, a small port if rejected. The next milestone (M7.3: `list`, `references`, `find-overlaps`, `validate`) proceeds without a gate.
