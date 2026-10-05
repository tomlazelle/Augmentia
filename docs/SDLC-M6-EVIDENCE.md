# M6 Evidence — End-to-End Validation & Release

Review material for the final M6 human gate. **M6 was approved by the human reviewer and `sdlc-skill-library 1.0.0rc1` was approved for release (recorded in the checklist).** All handoff checklist items now have evidence, including the one real GitHub publication (§6.4, executed after your explicit authorization of the exact preview).

## 1. Environment

| Item | Value |
|---|---|
| OS | Linux 7.0.0-38-generic |
| Python (release baseline) | 3.11.16 (uv-managed CPython) — suite, `pipx` environments, agent shells |
| Python (compatibility run) | 3.14.4 |
| `pipx` | 1.8.0 |
| Package | `sdlc-skill-library` **1.0.0rc1**, built from `skill-library/` |
| Claude Code | 2.1.283 |
| Codex | codex-cli 0.159.3 |
| GitHub CLI | gh 2.46.0 — used for read-only checks (`gh auth status` exit code, `gh issue create --help`, `gh repo view`, `gh repo list`, `gh issue list/view`) and, **once**, by `sdlc publish-apply` to create the single live Issue (§6.4) |
| Other runtime dependency | PyYAML only |

## 2. Packaging and install evidence

**What changed for release (packaging only; no behavior change):**
- `setup.py` build hook copies the canonical `skills/` and `shared/` trees into the built package as `sdlc/library/` (the sources are not forked or moved); `MANIFEST.in` includes them in the sdist; `sdlc/resources.py` finds them (installed package first, source checkout otherwise).
- Adapter logic moved from `install/_link.py` into `sdlc/adapters.py`; `install/claude_code.py` / `install/codex.py` remain thin wrappers (M2 behavior and tests unchanged).
- `pyproject.toml`: version `1.0.0rc1`, README as long description, console scripts `sdlc`, `sdlc-install-claude-code`, `sdlc-install-codex`; `sdlc --version` added. `python -m sdlc` still works.

**Commands and results**

```text
python -m build --outdir dist6 .                       # sdist + wheel, isolated build
  sdlc_skill_library-1.0.0rc1-py3-none-any.whl   140432 bytes  70 entries (36 under `sdlc/library/skills/`, 7 shared docs, templates, adapters)
  sdlc_skill_library-1.0.0rc1.tar.gz             103242 bytes
sha256  2a3b0db4d71e6593cb26a94090e18b30cf152e93dc532ef4a84e144202136332  …-py3-none-any.whl
sha256  d403bfc78cd470cfd0263902e2c842522dd76678cd6ec25045f5ee58bcbedbcf  …-1.0.0rc1.tar.gz
PIPX_HOME=<clean dir> pipx install --python python3.11 <wheel>      # installs sdlc, sdlc-install-claude-code, sdlc-install-codex
sdlc --version   ->  sdlc 1.0.0rc1
sdlc --help      ->  init allocate-id retire-id create-dir update-map list references find-overlaps status publish-preview publish-apply validate
```

Release smoke from the isolated install (automated: `test_release_smoke_sequence_from_the_installed_package`; also run by hand): `sdlc init` (twice), `validate`, `status`, `list`, `allocate-id --category BR --title Overview` all exit 0.

**Build lineage disclosure.** The walkthrough ran against successive release-candidate builds as defects were fixed: `dist1` (project init, merge test), `dist3` (BRD → verify), `dist4` (status re-runs, instruction tests, publish behavior, discovery). The **final** wheel (`dist6`) differs from `dist4` only in `METADATA`/`RECORD` (README text); all runtime code and Skills are byte-identical (`diff -r` of the unpacked wheels). `dist3` → `dist4` differed in exactly two files: `sdlc/technical.py` (defect 2) and the `review-implementation` Skill (defect 3).

**Installed-package independence (automated, opt-in):** the built wheel contains every Skill file, reference, shared doc, both templates and the adapter module; no `tests/` or `install/` paths; the isolated install resolves every Skill's `references/` and `../../shared/` token through the symlink; link targets resolve into the venv's `site-packages` and **not** the source checkout; real directories and foreign links are reported as `conflict` and never removed.

## 3. Automated tests

| Command (in `skill-library/`) | Result |
|---|---|
| `SDLC_TEST_INSTALL=1 <python3.11.16> -m pytest -q` | **532 passed** (final; M5 approved baseline: 493) |
| `<python3.11.16> -m pytest -q` | 524 passed, 8 skipped (the opt-in install/packaging tests) |
| `python3 -m pytest -q` (Python 3.14.4) | 524 passed, 8 skipped |

The count was 530 before the live publication; the final publication work added 2 tests (live-publication consistency and the authorization-boundary transcript) and no runtime code, so the complete suite was re-run and **532 is the final result**. 39 new tests since M5, none replacing an M1–M5 test: `test_packaging.py` (13: version, console scripts, dependency/baseline, library root, build hook, `python -m sdlc` regression, wheel contents, installed entry point, smoke sequence, adapters, uninstall/conflict), `test_readme.py` (6: every README command/flag/Skill/path/config block matches the released CLI and generated output), `test_m6_fixtures.py` (17), plus one regression test each in `test_skills.py`, `test_status.py` and `test_technical.py`. Stub/live distinction: no automated test contacts GitHub; all publishing tests use the stub `gh`.

## 4. Fresh-repository walkthrough

Repository `tasklog` created from scratch for M6 (**not** seeded from an M1–M5 fixture). Hand-authored: the seed code (`tasklog/store.py`, 3 tests), `pyproject.toml`, and the product persona's answers in each scripted prompt. The agents' `PATH` contained the pipx `sdlc` and a project `.venv` with pytest but no `sdlc` module (as for a real pipx user); the stub `gh` was first on `PATH`. 28 logged agent sessions (15 Claude Code, 13 Codex); every prompt, output and before/after file fingerprint is in `skill-library/tests/fixtures/m6/transcripts/` (`run-log.jsonl` is the raw log); the resulting repository is `tests/fixtures/m6/tasklog-e2e/` (git history in `e2e-git-log.txt`).

| # | Step | Who | Evidence |
|---|---|---|---|
| 1 | `pipx install`, `sdlc --version/--help`, `sdlc-install-claude-code` / `sdlc-install-codex --scope project` (15 links each into the pipx env) | maintainer | §2; discovery by both agents: `transcripts/docs-{claude,codex}-discovery.txt` (clean project) and all walkthrough runs |
| 2 | `sdlc init`; repeat `init` (all `existing`); valid `.sdlc/config.md`; fresh ledger; maps; AGENTS.md/CLAUDE.md; existing `AGENTS.md` left byte-identical in a second scratch project | maintainer | `test_release_smoke…`, `test_documented_layout_matches_what_init_generates`, hand run |
| 3 | BRD (adaptive interview: round 1 questions, answers, recap, write) → BR-001 (1 requirement, Draft) | Claude | `01-product-context.md` |
| 4 | PRD from BR-001 (interview round, answers, write) → PR-001 (R001–R004, Derived From BR-001) | Claude | `01-product-context.md` |
| 5 | Story from PR-001 → US-001 covering all four requirements, 7 acceptance criteria, malformed-due-date TBD kept open | Codex | `01-product-context.md` |
| 6 | **Contextual overlap** (§6.1) | Codex | `02-contextual-overlap-codex.md` |
| 7 | `refine-stories`: checked against the repo, no content invented, `Ready` on the human's explicit declaration (TBD accepted as residual) | Claude | `03-technical-flow.md` |
| 8 | **Research + design** (§6.2): RES-001, DES-001 | Codex | `03-technical-flow.md`; fixture |
| 9 | `plan-implementation` → PLAN-001 (linked to DES-001, RES-001) | Codex | `03-technical-flow.md` |
| 10 | `create-test-plan` → TEST-001 (TS-1…TS-7 per criterion plus boundary cases; TBD kept out of scenarios) | Claude | `03-technical-flow.md` |
| 11 | `implement-story` → Ready → In Progress → Implemented; real change in `tasklog/store.py`, `tasklog/__init__.py`, `tests/test_store.py` (+96/−5 lines, 12 tests pass, re-run independently: 12 passed); not Verified | Claude | transcript + `test_implementation_is_a_real_change_whose_tests_pass_when_rerun` |
| 12 | `review-implementation` → verdict complete, no findings, recorded; explicitly "not verification"; `delivery_status` unchanged | Codex | transcript; review record `RR-1` (see defect 3) |
| 13 | `verify-story` → ran `pytest` (exit 0, 12 passed), VR-1 recorded for AC-1…AC-7, evidence log, **Verified** only then | Claude | transcript; `test_story_reached_verified_only_through_the_recorded_evidence` (tampering with the VR makes `validate` fail) |
| 14 | `sdlc validate`: 0 errors, 1 warning (`verified-with-unresolved-tbd`, expected), 0 notices | maintainer | `test_fixture_validates_with_only_the_expected_tbd_warning` |
| 15 | `sdlc-status` on the final state, both agents, prompted to "fix anything stale"; read-only (fingerprints identical) | Claude, Codex | `04-status.md`; `test_status_reports_the_final_state_…` |
| 16 | Project instructions: human approves US-001 (manual edit + `update-map`); each agent is asked to edit the Approved Story directly, bypassing Skills | Claude, Codex | `05-project-instructions.md` (Claude declined citing CLAUDE.md; Codex followed AGENTS.md: refine-stories, In Review, Ready, VR superseded; diff in `ins-4-diff.patch`, then discarded by the maintainer) |
| 17 | `publish-stories` preview and confirmation behavior with a **stub** target `acme/widgets`: preview shown verbatim, "Looks fine I guess…" / "sounds fine, go for whatever you think is best" not accepted as confirmation, zero `gh` calls | Claude, Codex | `06-publish-behaviour-stub.md` |
| 19 | **Live GitHub publication** of US-001 → `tomlazelle/UsedForPractice#1`, after explicit authorization of the exact preview (§6.4) | maintainer / human | `09-live-github-publication.md`; `live-publication/` |
| 18 | Branch merge with duplicate IDs (real git merge; `validate` → 2× `duplicate-id`, exit 1) | maintainer | `08-branch-merge-duplicate-ids.md` |

**Manual interventions and hand-authored steps (all disclosed in the transcripts):** seed code and persona answers; `sdlc init` run by hand; `AGENTS.md`/`CLAUDE.md` deleted and regenerated by `sdlc init` after the first `implement-story` attempt stopped (the project had been initialized with an earlier build whose template still said `python -m sdlc`); `status: Approved` set on US-001 by hand followed by `sdlc update-map`; `git checkout` to discard the agent edit in step 16 (diff retained); the publishing config block added by hand; a `git commit` between phases to give each step a clean fingerprint baseline.

**Harness/agent failures, retained rather than hidden:** `ov-2` (Codex `resume` flag order, exit 2, agent never ran; `ov-2b` is the retry); the first misconfigured publish chain (config edit failed; I stopped the agent processes before they logged, and re-ran the four runs correctly); `ins-1` (Claude paused on content, inconclusive); `ins-3` (Codex made no tool call and claimed a read-only workspace, which is not true of the sandbox; inconclusive, replaced by `ins-4`); the first Codex discovery run in the clean project wrote an empty output with exit 0 for an unknown reason and the immediate retry succeeded.

## 5. Documentation validation (handoff §8)

`skill-library/README.md` (installation, agent integration, `sdlc init` and generated structure, create-if-missing, workflow, core concepts, GitHub publishing, command reference, troubleshooting). Validated by following it literally in a **clean environment** (fresh `PIPX_HOME`, fresh project, final wheel): `pipx install --python python3.11 <wheel>` → `sdlc --version`/`--help` → both `sdlc-install-*` commands (15 links each; `ls -l` shows pipx targets) → `sdlc init`/`validate` → **Claude Code and Codex each used `sdlc-status` from those links** → upgrade (`pipx install --force …`: version unchanged, links still resolve, `validate` clean) → uninstall in the documented order (30 links removed; project files intact) → `sdlc` command gone. Automated checks (`test_readme.py`) tie the README to the CLI: every command and flag it names exists, every Skill is documented, the layout block equals `init` output, and the publishing config block and confirmation behavior match `publish-preview` / `publish-apply`. The README does **not** claim user-scope discovery: `--scope user` is documented as implemented and unit-tested but not verified with the agents (not exercised, to avoid modifying the maintainer's real `~/.claude` and `~/.agents`).

## 6. Deferred-item closure

### 6.1 Real Codex contextual-overlap run — **CLOSED**
`02-contextual-overlap-codex.md`. After US-001 existed, a real Codex session was asked for a Story about "items whose deadline has already gone by and that nobody has finished yet" (no shared vocabulary with "List overdue tasks"). A bare-title `find-overlaps` check returned no candidates. Codex ran the CLI check itself (with purpose/`--covers` hints, so it scored US-001 `likely` 1.0 — disclosed) **and** gave the separate "Conceptual overlaps (my judgement, not CLI-scored)" section, then asked whether to revise, relate or create new. **Before the decision the ledger was byte-identical** (MD5 recorded before/after) and no file changed: no ID was allocated. On "revise US-001" Codex found the requested criterion already present (AC-4) and created nothing.

### 6.2 Live-agent RES exercise — **CLOSED**
Codex (create-design) created `RES-001` for a real decision question (how `Task` should represent an optional due date given stdlib-only Python 3.11). ID allocated by the CLI; `Artifacts/research/RES-001-…md`; front matter and `Derived From` link to US-001 with the requirements it serves; `Question`/`Sources`/`Findings`/`Conclusion` sections; findings are **observed experiments** (`date` vs ISO string raises `TypeError`; `date` vs `datetime` raises `TypeError`; `fromisoformat('not-a-date')` raises `ValueError`; `date.today()` is a `date`) with the explicit statement that they do not decide the malformed-input TBD; no invented external sources; `Artifacts/research/map.md` lists it; `validate` clean; DES-001 cites RES-001 and its decision (`datetime.date | None`) is what PLAN-001, the implementation and the tests then use. Asserted by `test_live_agent_research_artifact_is_real_and_used`.

### 6.3 Clean-repository end-to-end walkthrough — **CLOSED** (see §4 for disclosures)
Both agents took part at meaningful points (Claude: BRD, PRD, refine, test plan, implement, verify; Codex: Stories, overlap, research/design, plan, review). The live-publication step of the handoff walkthrough is the open item below.

### 6.4 Real GitHub publication — **CLOSED**

| Item | Result |
|---|---|
| Target repository | `tomlazelle/UsedForPractice` (https://github.com/tomlazelle/UsedForPractice), designated by you; read-only check: **public**, Issues enabled, not archived, no existing Issues |
| Published Story | `US-001` ("List overdue tasks", `status: Approved`, `delivery_status: Verified`) from the fresh `tasklog` walkthrough repository |
| GitHub Issue | **#1** — https://github.com/tomlazelle/UsedForPractice/issues/1 — `[US-001] List overdue tasks`, no labels, state OPEN, created 2026-10-05T20:15:19Z |
| Exact preview authorized before publication | **Yes.** Sequence: (1) you answered "use local for now" (read as deferral; nothing created); (2) you designated `tomlazelle/Augmentia`; I showed its full preview and made **no** publication; (3) you asked "What do you want to do exactly?" and I explained and waited; (4) you re-designated `UsedForPractice` ("You can publish here …"); I did **not** treat that as authorization: I checked the repo, regenerated and showed the preview for it (digest `sha256:befd69bfd947b43bd85d4cc7e4a1c133e5c0a3bde1b822fdf2f6ab36dd5f158b`; body byte-identical to the one already shown, verified by `diff`) and asked you to confirm that specific preview; (5) you replied "do it", and only then I ran `sdlc publish-apply US-001 --confirm-digest sha256:befd69bf…`. Result: `US-001: published …/issues/1`, `External mutations: 1`. |
| Issue content | Read back with `gh issue view 1 --repo tomlazelle/UsedForPractice`: title and body equal the previewed title and body (checked programmatically); no labels; author `tomlazelle`. |
| Resulting record | `### PUB-1 — 2026-10-05` · Provider `github` · Repository `tomlazelle/UsedForPractice` · Issue `#1` · URL `https://github.com/tomlazelle/UsedForPractice/issues/1` appended to the Story's `## Publication` section. `status: Approved` and `delivery_status: Verified` unchanged; only `updated` moved; the Story file was the only file changed (9 lines added). |
| Same-repository duplicate prevention | `sdlc publish-preview US-001` → `=== US-001 — SKIP ===`, notice `already-published … tomlazelle/UsedForPractice#1`, `Will create: nothing`; `sdlc publish-apply US-001 --confirm-digest <that digest>` → `US-001: skipped already published`, `External mutations: 0`; `gh issue list --repo tomlazelle/UsedForPractice --state all` afterwards: exactly **one** Issue (#1). No second Issue was created. |
| Final `sdlc validate` | `7 document(s): 0 error(s), 1 warning(s), 0 notice(s)`, exit 0 (the one warning is the expected `verified-with-unresolved-tbd`). |
| Cleanup | The Issue was **not** closed, edited or deleted, and I will not do so unless you ask. No credential appears in any artifact (`gh` used your existing login; tests scan the fixtures). |

Artifacts: transcript `tests/fixtures/m6/transcripts/09-live-github-publication.md`; snapshot `tests/fixtures/m6/live-publication/` (`US-001-list-overdue-tasks.md` with the PUB-1 record, `config.md`, `issue.json`, `issue-body.md`, `issues-after-duplicate-attempt.json`); asserted by `test_live_publication_record_issue_and_body_are_consistent` (record parses; status/delivery unchanged; `validate` clean; the same-repository preview skips; the Story still renders to exactly what GitHub holds). Disclosed: the walkthrough repository's `publishing` config was pointed at the live repository by hand (commits `MANUAL: point publishing …` and `MANUAL: human re-designated …`); the live apply was run by me directly through the CLI (not through an agent session) with the real `gh` and the stub removed from `PATH`; the Issue lives in a **public** repository you designated for this purpose.

## 7. Cross-agent release matrix

| Capability | Claude Code | Codex |
|---|---|---|
| Discover installed Skills | **new** — every run; clean-project run (`docs-claude-discovery.txt`) | **new** — every run; clean-project run (`docs-codex-discovery.txt`) |
| Create/use governed docs | **new** — BRD, PRD, refine, test plan | **new** — Story, research, design, plan |
| Respect project instructions | **new** — `ins-2` declined the direct edit citing CLAUDE.md | **new** — `ins-4` followed AGENTS.md (In Review / Ready / VR superseded); `ins-3` inconclusive |
| Contextual overlap decision | reused — M3 evidence (`tests/fixtures/m3`) | **new live run** — §6.1 |
| Technical Skill execution | **new** — refine, test plan, implement, verify | **new** — design (+RES), plan, review |
| `sdlc-status` | **new** — `st-1`, `st-3`, discovery | **new** — `st-2`, `st-4`, discovery |
| `publish-stories` preview / confirmation behavior | **new** (stub) — `pub-c1`, `pub-c2`; confirmed-publication path reused from M5 (stub) | **new** (stub) — `pub-x1`, `pub-x2`; confirmed-publication path reused from M5 (stub) |
| Real GitHub publication | **new** — one live Issue via `sdlc publish-apply` (§6.4); the CLI path is agent-independent. The agent-driven confirmation behavior is shown with the stub (rows above) and reused from M5 | same |

## 8. Defects found during M6

| # | Observed | Expected | Correction | Regression test | Contract changed? |
|---|---|---|---|---|---|
| 1 | Under a pipx install the Skills and project templates told agents to run `python -m sdlc …`, which fails for the user's python. A real agent silently used `sdlc` but reported `python -m sdlc validate` (`07-defect-probes.md`). | Skills name a command that exists in the release install | All Skills, shared docs, templates and the CLI docstring now say `sdlc`; `cli-contract.md` states `python -m sdlc` remains an exact equivalent; failure sentence reads `command not found: sdlc` | `test_skills_and_templates_use_the_installed_command_not_python_dash_m`; `test_only_real_cli_commands_and_flags_are_used` retargeted to `sdlc <cmd>` | No — spelling of the invocation only |
| 2 | A real Codex-authored Story wrote the TBD heading at level 2 (`## Unresolved Acceptance Behavior (TBD)`); the detector only accepted level 3, so `validate` and `status` hid the TBD and both agents reported "no unresolved TBD" (`04-status.md`, `st-1`/`st-2`). | An unresolved TBD is always surfaced | `technical.unresolved_tbd_bullets` accepts the heading title at level 2 **or** 3 | `test_unresolved_tbd_is_found_whether_its_heading_is_level_two_or_three`; `test_verified_story_with_level_two_tbd_heading_still_warns` | No — the heading *title* was already the contract; this restores the approved behavior (reviewer may note the recognized levels) |
| 3 | A real Codex review wrote `### RR-1` instead of the contract's `### RV-n`. Review Records are not parsed by `validate`, so nothing flagged it. | `### RV-<n> — <date>` | `review-implementation` Skill now names the exact heading ("RV, not RR"); the e2e Story keeps the original `RR-1` for attribution | `test_review_skill_names_the_exact_review_record_heading` | No (no validator rule added; adding one would be a new semantic) |
| 4 | README gaps: `sdlc-init` was not documented; a hand approval (`status: Approved`) leaves `map.md` stale until `sdlc update-map` (found when the walkthrough's `validate` failed with `stale-map`); instruction files from an older build are not refreshed by `init` (found when `implement-story` stopped on stale text) | The user guide covers each | README updated (workflow table, `status` concept, upgrade note) | `test_every_skill_is_documented_and_every_documented_skill_exists` | No |

Not product defects (process issues disclosed above): the stale instruction files in the walkthrough project (created by an earlier build; `create-if-missing` correctly never overwrote them), the `ov-2` harness flag order, the misconfigured first publish chain.

## 9. Limitations

- **Only one live publication was executed** (one Issue, public repository, run directly through the CLI rather than through an agent session). Live failure modes (permissions, rate limits, scopes) remain covered only by M5's stub tests.
- **User-scope Skill links** (`--scope user`) are not verified with the agents; project scope is.
- **Upgrade:** `init` never refreshes existing `AGENTS.md`/`CLAUDE.md` (approved create-if-missing behavior), so a project created with an older release keeps older instruction text; documented in the README.
- **Symlink adapters point into the pipx environment**: a pipx reinstall that changes the environment path (for example a different Python version) breaks the links until the install command is re-run with `--force`.
- Single-sample agent runs: each agent behavior is one observation, not a statistic. The Codex `ins-3` and first discovery attempts were inconclusive/unexplained; only the later successful retries count.
- The walkthrough's review found nothing (a valid outcome, but the review→rework loop was not exercised in M6; M4 covers rework).
- The agent-driven publishing-behavior runs in the walkthrough used the stub; M5's carried-over limitations stand (the digest gate cannot prove human intent; single-writer; non-transactional crash window; relative links; Codex was not run for every M5 scenario).
- The `sdlc-validate` Skill's duplicate-ID renumbering flow was not re-run with an agent in M6 (CLI detection of a real merge duplicate was).
- Windows/macOS were not tested (Linux only); the package is pure Python.

## 10. Release candidate result

**The release candidate is ready for human sign-off.** Every handoff checklist item has evidence: package build and `pipx` install, documentation validated in a clean environment, both agents' discovery and use, the clean-repository walkthrough through Verified, the three deferred acceptance items (Codex contextual overlap, live-agent RES, clean E2E) and the one real GitHub publication with duplicate prevention. Final automated result: **532 passed** on Python 3.11.16 with `SDLC_TEST_INSTALL=1` (524 passed + 8 opt-in skipped by default; Python 3.14.4 the same). The four defects found (§8) were fixed narrowly with regression tests and none changed an approved contract. Remaining limitations are in §9. Release approval is yours; this document does not grant it.

## 11. Handoff release checklist status

All items ✓: M5 approval recorded · package builds · pipx clean install · `sdlc` entry point · runtime package data complete · install docs validated clean · Claude Code install/discovery · Codex install/discovery · fresh repo initialized · init idempotent · BRD/PRD/Story chain · real Codex overlap before allocation · technical flow · live-agent RES · real implementation · review · real verification, Verified · `validate` passes (0 errors) · `sdlc-status` accurate and read-only · **live GitHub preview shown · explicit human authorization obtained for the exact preview · one real Issue created (#1) · publication record validated (PUB-1) · same-repository duplicate demonstrated without a second Issue** · cross-agent matrix · Python 3.11 suite with install tests (532) · documentation walkthrough · this document · limitations documented · presented for human sign-off (final sign-off pending: yours).

## 12. Files touched in M6

New: `setup.py`, `MANIFEST.in`, `README.md`, `sdlc/resources.py`, `sdlc/adapters.py` (moved from `install/_link.py`), `tests/unit/{test_packaging,test_readme,test_m6_fixtures}.py`, `tests/fixtures/m6/` (including `live-publication/` and transcript `09`), `docs/SDLC-M6-EVIDENCE.md`. Modified: `pyproject.toml` (version, scripts, readme), `sdlc/{__init__,cli,technical}.py`, `install/{claude_code,codex}.py`, all `skills/**` and `shared/**` text that named `python -m sdlc`, `skills/review-implementation/SKILL.md`, `sdlc/templates/{AGENTS,CLAUDE}.md`, `.gitignore`, `tests/unit/{test_skills,test_status,test_technical}.py`, `docs/SDLC-IMPLEMENTATION-CHECKLIST.md`.

## 13. Release-note item

The verified walkthrough Story (`US-001`) still contains one explicitly unresolved acceptance item (how a malformed due date should be reported). The reviewer recorded it as not a release blocker and worth preserving in the release notes: it is surfaced rather than hidden (`sdlc-status` traceability, the `verified-with-unresolved-tbd` validator warning, and the published Issue body), which shows the difference between structural/verifiable completion and unresolved product behavior. (No separate release-notes file exists in the repository; this section and the checklist carry the item.)
