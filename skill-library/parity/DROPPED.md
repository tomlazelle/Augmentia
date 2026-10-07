# Register of Python code intentionally not ported

Policy (human decision at the M7.1 gate): do not port code proven to have no reachable behavior; classify each omission here with the symbol/path, why it is dead/shadowed/unreachable, and what demonstrated it. Uncertain reachability => port it. Do not use this to redesign reachable internals.

Evidence available for every candidate: the corpus replay under `coverage.py` (branch) and `parity/tools/condition_trace.py` (conditional expressions), both recorded in `docs/SDLC-M7-1-CORPUS-REPORT.md` §5/§5.1.

| Python symbol / location | Status | Why it has no reachable behavior | Evidence | Node milestone |
|---|---|---|---|---|
| `sdlc/publication.py:39` `Publication.number` | **dropped (not ported in M7.3; the parser was ported without it)** | Property is never read anywhere in the package or tests | line never executed; `grep -rn "\.number" sdlc tests` finds no use | M7.4 |
| `sdlc/init_cmd.py:88-89` `create_artifact_dir` `bad-artifact` result | **dropped (done in M7.2)** | argparse `choices=` rejects unknown `--artifact` values (exit 2) before the function runs; the Node CLI validates the same closed set at the CLI layer with identical observable behavior | line never executed; only caller is `cli.run` after parsing | M7.2 |
| `sdlc/publish.py:175-178` `if pub_diags:` blocker `publication-invalid` | **ported as-is (uncertain; done in M7.4)** | Shadowed (believed unreachable, kept until proven): `validate` reports `publication-invalid` on the same path and the Story is blocked at the earlier `mine` check, so the branch cannot execute | branch never executed; `mine` is computed from the same `project_diags` that contain `publication-invalid` | M7.4 |
| `sdlc/publish.py:204-209` `if unrelated:` | **ported as-is (uncertain; done in M7.4)** | Believed always true when reached, but kept until proven | condition_trace: false side never seen | M7.4 |
| `sdlc/validate.py:19-20` `_dup_diags` single-file guard | **ported as-is (uncertain; done in M7.3)** | Believed unreachable; kept until proven | branch never executed | M7.3 |
| `sdlc/frontmatter.py:26` empty-message YAML error fallback | **ported as-is (uncertain; done in M7.2)** | A YAML error always has text in PyYAML; the Node YAML library may differ, so the fallback is kept | condition_trace | M7.2 |
| `sdlc/model.py:73` `Outcome.__post_init__` `diagnostics is None` default | **ported (internal default; done in M7.2)** | Cheap and part of the result type | condition_trace | M7.2 |
| `sdlc/publication.py:94-101` `_bump_updated` no-front-matter / unterminated / no-`updated` fallbacks | **ported as-is (uncertain; done in M7.4)** | Believed unreachable for a valid Story; kept until proven | branches never executed | M7.4 |
| `sdlc/project.py:115-116` `rel()` fallback for paths outside the root | **ported as-is (uncertain; done in M7.2)** | Reachable only via an out-of-tree symlink target | line never executed | M7.2 |
| `sdlc/adapters.py`, `sdlc/resources.py`, `sdlc/__main__.py` | **replaced** | Installer entry points and the `python -m sdlc` shim are replaced by `bin/` launchers (M7.5) | n/a | M7.5 |
