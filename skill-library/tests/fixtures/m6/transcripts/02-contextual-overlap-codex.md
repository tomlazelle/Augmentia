# Walkthrough 2 — real Codex contextual-overlap run (deferred M3 item)

All human turns are scripted by the maintainer (hand-authored inputs: the product persona's answers). The fresh repository `tasklog` was created from scratch for M6 (not an M1–M5 fixture), with hand-authored seed code (`tasklog/store.py`, 3 tests). `sdlc` was installed with `pipx` from the release-candidate wheel; the agents' `PATH` had the pipx `sdlc` and a project `.venv` with pytest but **no** `sdlc` module. The stub `gh` (`tests/unit/fakegh.py`) was first on `PATH`; no real GitHub call was made in any agent run.

Before the run: `sdlc find-overlaps --category US --title "Surface items whose deadline has gone by"` (title only) returned **no candidates**. The ledger MD5 was recorded before the run and verified **identical** after turn 1 (the decision was put to the human before any ID allocation). Note: the agent's own `find-overlaps` call supplied purpose and `--covers` hints and so scored US-001 `likely`; the agent also gave its separate conceptual-overlap judgement. Attempt `ov-2` failed in the harness (`codex exec` flag order, exit 2; the agent never ran); `ov-2b` is the retry.

### USER (`ov-1`, new session)

Use the create-stories skill to write a Story: developers want a way to surface items whose deadline has already gone by and that nobody has finished yet.

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

The requested behavior is already covered by [US-001 — List overdue tasks](<<scratch>/e2e/tasklog/Stories/US-001-list-overdue-tasks.md>). It covers PR-001-R001 through R004, including excluding completed tasks and ordering overdue tasks.

**CLI overlap candidate** (copied from `sdlc find-overlaps`):

- US-001 — List overdue tasks; level: `likely`; score: `1.0`
  - same normalized title
  - purpose similarity 1.00
  - shares references: PR-001-R001, PR-001-R002, PR-001-R003, PR-001-R004

**Conceptual overlaps (my judgement, not CLI-scored)**

- US-001 — List overdue tasks. Its purpose is to let a developer retrieve open tasks past their due date, ordered by overdue duration.

Would you like me to **revise** US-001, **relate** a new Story to it, or **create a new independent Story**? I haven’t allocated an ID or changed any files.

_Harness: exit 0; file fingerprint before→after: `a77b984e8426d686` → `a77b984e8426d686`; ledger unchanged, no files changed, no ID allocated._

### USER (`ov-2`, cont session)

Revise US-001 rather than creating anything new. If it does not already say so explicitly, add an acceptance criterion that a task due exactly today is not overdue. Do not allocate a new ID.

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

(empty: see note)

_Harness: exit 2; file fingerprint before→after: `a77b984e8426d686` → `a77b984e8426d686`; HARNESS FAILURE, not agent behaviour (flag order); see ov-2b._

### USER (`ov-2b`, cont session)

Revise US-001 rather than creating anything new. If it does not already say so explicitly, add an acceptance criterion that a task due exactly today is not overdue. Do not allocate a new ID.

### AGENT (Codex (`codex exec --sandbox workspace-write`, project skills linked by `sdlc-install-codex` from the pipx install))

US-001 already explicitly says that an open task due today is excluded: acceptance criterion 4 excludes tasks whose due date is “today or in the future.” I left it unchanged and created nothing new.

_Harness: exit 0; file fingerprint before→after: `a77b984e8426d686` → `a77b984e8426d686`; US-001 unchanged: the criterion already existed; no new ID._
