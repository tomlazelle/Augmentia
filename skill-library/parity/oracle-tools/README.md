# Oracle tools (historical)

These Python tools produced and measured the frozen corpus and the oracle-derived expectation files. They import or run the Python 1.0.0rc1 implementation, which was removed from the tree at M7.6 and is preserved as the git tag `python-1.0.0rc1`.

To run any of them: `git worktree add ../oracle python-1.0.0rc1`, copy this directory over `parity/tools/` there, and use Python 3.11 with PyYAML. The final side-by-side differential run (`differential.py`, results in `../pre-removal-evidence/`) is the last use of both implementations together.
