### USER

Use the create-test-plan skill for US-001. Reuse the plan's validation commands; the project's test command is python -m pytest -q. No further questions: write the Test Plan now.

### AGENT (claude -p, project skills via install/claude_code.py)

No errors or warnings — the two notices are pre-existing (unrelated to US-002/PR-001-R002, not touched by this plan).

**TEST-001** created at `Artifacts/tests/TEST-001-test-plan-for-turning-a-title-into-a-url-slug.md`, status `Draft`, derived from US-001 (PR-001-R001), related to DES-001 and PLAN-001.

- **Inspected:** `textkit/text.py`, `textkit/__init__.py`, `tests/test_text.py`, `pyproject.toml`, `README.md`, US-001, PR-001, DES-001, PLAN-001. `slugify` doesn't exist yet — all scenarios are proposed, not yet run.
- **Scenarios:** TS-1–TS-5 map 1:1 to AC-1–AC-5, all automated via `python -m pytest -q` (reused per your instruction). Added two regression cases: public export via `textkit` root, and the existing `truncate` tests must keep passing.
- **TBD carried forward:** accented/non-Latin character handling — no scenario invented for it.
- **Validate:** 0 errors, 0 warnings, 2 pre-existing notices unrelated to this change (US-002 coverage, PR-001-R002 coverage).

Approval is up to you — let me know if you want to review/amend before setting it to `Approved`.

