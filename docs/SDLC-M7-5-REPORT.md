# M7.5 report — packaging, installers, docs, Skill text, licence

| Item | Result |
|---|---|
| npm package | `@augmentia/sdlc` 2.0.0-rc.1, MIT, `engines.node >=22`, one runtime dependency (`yaml`); `bin`: `sdlc`, `sdlc-install-claude-code`, `sdlc-install-codex` |
| Tarball (`npm pack`, 73 files, ~105 kB) | `bin/`, `dist/src`, `dist/templates`, `library/skills` + `library/shared` (every file of the canonical trees), `LICENSE`, `README.md`; no tests, sources, scripts, parity data or Python artefacts (tested) |
| Clean-prefix install | `npm install --offline --prefix <tmp> <tarball>` works (only `yaml` is fetched/cached); installed `sdlc --version` = `sdlc 2.0.0-rc.1`; release smoke sequence (init ×2, validate, status, list, allocate-id) passes; AGENTS.md = CLAUDE.md |
| Adapters (`src/adapters.ts`) | Port of `sdlc/adapters.py`: symlinks (never copies), `installed/unchanged/replaced/conflict/removed/skipped/absent`, `--scope/--project-dir/--target/--skill/--force/--uninstall`, usage errors exit 2, conflicts exit 1 and never destroy a real directory or foreign link. Installed adapters link into the installed package (not the checkout); `references/` and `../../shared/` links resolve through the symlinks |
| Licence | `LICENSE` (MIT, "Copyright (c) 2026 Thomas La Zelle"), `"license": "MIT"` |
| Docs / Skill text | `README.md` (root and user guide) rewritten for npm/Node; `sdlc-init` Skill and `shared/cli-contract.md` no longer name pipx/pip/Python (test enforced); templates unchanged (they never named Python; init output stays byte-identical to the corpus) |
| Node tests | **146 tests, 146 pass** (was 91): +`adapters` 10, +`packaging` 9, +`skills` 32 (port of the 53 Python Skill/template checks, grouped), +`readme` 5 |
| Corpus | 1,844 applicable: 1,831 exact + 13 exempt, 0 failed (unchanged) |
| Python oracle | `sdlc/` untouched; suite 623 passed/10 skipped (one test line in `test_packaging.py` updated for the new install wording) |

Not changed: Windows remains out of scope; user-scope agent discovery remains unverified (project scope is the verified path), as before.

Next: M7.6 (differential run on both agents from the npm install, removal of Python, evidence, sign-off) requires your approval of the parity result.
