### USER

Use the create-design skill for US-001. A short design is enough. Decisions: implement slugify in textkit/text.py with the standard library only; export it from textkit/__init__.py; the accented-character question is an open decision. Also add a short optional research note (RES) only if you have real sources to cite from this repository; otherwise skip it. Skip further questions and write now.

### AGENT (claude -p, project skills via install/claude_code.py)

Validation is clean — 0 errors, 0 warnings. The two notices are pre-existing and unrelated to this design (PR-001-R002 is US-002's concern, and US-002 is a standalone story).

**Summary:**
- Created `DES-001` at `Artifacts/design/DES-001-slugify-implementation-for-url-slugs.md`, status `Draft`, derived from US-001 (PR-001-R001).
- **Inspected:** `textkit/text.py`, `textkit/__init__.py`, `tests/test_text.py`, `PR/PR-001-text-utilities.md`. **Not inspected:** no packaging/lint/CI config found.
- **Decision:** implement `slugify` in `textkit/text.py` with `re` (stdlib only) — lowercase, collapse non-keep runs to `-`, strip leading/trailing `-`; export via `textkit/__init__.py`'s existing `__all__` pattern.
- **Left open, as requested:** which characters count as "keep" for accented/non-Latin input — flagged in Open Decisions, matching the Story's own TBD.
- No Research note added — no real citable sources exist in this repo, per your instruction to skip in that case.

