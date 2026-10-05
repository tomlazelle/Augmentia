# SDLC Skill Library

A first-party, Markdown-first set of agent Skills plus a small deterministic command-line tool (`sdlc`) for working through a software lifecycle with an AI coding agent: business and product requirements, Stories, technical design and plans, implementation, review, verification, status reporting, and controlled publishing of Stories to GitHub Issues.

- **Markdown is the source of truth.** Everything lives as plain files in your repository (`BR/`, `PR/`, `Stories/`, `Artifacts/`). Nothing is stored in a database or a service.
- **Skills talk to you; the CLI does the bookkeeping.** The Skills run the conversation (interviews, review, judgement). The `sdlc` command allocates IDs, regenerates maps, finds overlaps, validates, reports status, and is the only thing that can publish.
- **Two supported agents:** Claude Code and Codex. The same Skill text is used for both.
- **You approve.** Agents never mark a document `Approved`; evidence of tests comes from tests that were actually run; nothing is published without a preview you have confirmed.

## 1. Install

**Prerequisites:** Python 3.11 or newer, [`pipx`](https://pipx.pypa.io/), and at least one agent: [Claude Code](https://claude.com/claude-code) or [Codex](https://github.com/openai/codex). For publishing you also need the [GitHub CLI](https://cli.github.com/) (`gh`), logged in.

```bash
pipx install --python python3.11 <package>      # <package> = path to the wheel/sdist, or an index name once published
sdlc --version        # -> sdlc 1.0.0rc1
sdlc --help           # lists: init allocate-id retire-id create-dir update-map list references
                      #        find-overlaps status publish-preview publish-apply validate
```

The `pipx` install provides three commands: `sdlc`, `sdlc-install-claude-code` and `sdlc-install-codex`. `python -m sdlc` also works wherever the package is importable (for example in a development checkout).

**Upgrade or reinstall:** `pipx install --force --python python3.11 <new package>`. Skill links you made earlier keep working if the pipx environment path is unchanged; if a link breaks (for example after the Python version of the environment changes), re-run the install commands in section 2 with `--force`.

**Project instruction files are not refreshed on upgrade.** `sdlc init` never overwrites `AGENTS.md`/`CLAUDE.md`, so a project created with an older release keeps the older text. After upgrading, compare them with the template shipped in the package (`AGENTS.md`/`CLAUDE.md` under `sdlc/templates/` inside the installed `sdlc` package) and update by hand, or delete them and run `sdlc init` to regenerate them.

**Uninstall:** remove the Skill links first (`sdlc-install-claude-code --scope project --uninstall`, `sdlc-install-codex --scope project --uninstall`, from the same project), then `pipx uninstall sdlc-skill-library`. Your project files are never touched.

**Verify:** `sdlc --version` prints the version, and `sdlc init` followed by `sdlc validate` in an empty directory reports `0 error(s)`.

## 2. Connect your agent (per project)

Skills are **linked, not copied**: each Skill directory is a symlink into the installed package, so there is one canonical copy.

```bash
cd your-project
sdlc-install-claude-code --scope project     # -> .claude/skills/<skill>   (Claude Code)
sdlc-install-codex       --scope project     # -> .agents/skills/<skill>   (Codex)
```

Both commands accept `--project-dir DIR`, `--skill NAME` (repeatable), `--force` (replace a link that points elsewhere) and `--uninstall`. They never remove a real directory or a link that is not theirs and report it as `conflict`.

**Verify discovery.** You should see 15 Skills, each a link into the pipx environment:

```bash
ls -l .claude/skills .agents/skills
```

Then ask the agent to use one, for example *"Use the sdlc-status skill and tell me where this project stands."* Both agents were verified this way at project scope. `--scope user` (links in `~/.claude/skills` or `~/.agents/skills`) is implemented and unit-tested, but agent discovery from the user directory was **not** verified for this release; use project scope.

Both agent folders are usually kept out of version control (`.claude/`, `.agents/` in `.gitignore`), since the links point into your own pipx environment.

## 3. Start a project

```bash
cd your-project
sdlc init                  # add --project-name NAME to override the directory name
```

`init` is idempotent and never overwrites anything it did not create. It produces:

```text
.sdlc/config.md     configuration (project name, schema version, directory names, optional publishing)
.sdlc/ledger.md     the ID ledger (CLI-maintained; never edit by hand)
BR/   PR/   Stories/   Artifacts/        each with a map.md index
map.md              root index
AGENTS.md           project instructions for Codex and other agents
CLAUDE.md           the same instructions for Claude Code
```

`AGENTS.md` and `CLAUDE.md` are **create-if-missing**: if either file (or a symlink with that name) already exists it is left exactly as it is. In that case add the guidance yourself from the packaged template (`sdlc/templates/AGENTS.md`). They tell the agent to use the matching Skill before changing any governed document, and that only you approve documents.

Commit `.sdlc/`, the four folders, the maps and the two instruction files.

## 4. A typical workflow

You can enter at any step. A BRD or PRD is **not** required, and neither is a Design: a Story can stand alone (`covers: []`).

```text
init → BRD (optional) → PRD (optional) → Stories → refine → Design / Plan / Test Plan (as needed)
     → implement → review → verify → status → publish
```

| Step | Skill | What happens |
|---|---|---|
| Set up | `sdlc-init` | the agent runs `sdlc init` for you (or run it yourself, section 3) |
| Business requirements | `create-brd` | adaptive interview → `BR-NNN` with requirement IDs |
| Product requirements | `create-prd` | with or without a BRD → `PR-NNN` |
| Stories | `create-stories` | `US-NNN` with acceptance criteria and `covers` links |
| Make a Story ready | `refine-stories` | sharpens criteria, never invents; you declare it `Ready` |
| Technical artifacts | `create-design`, `plan-implementation`, `create-test-plan` | `DES-`, `PLAN-`, `TEST-` (and optional `RES-` research) only when useful |
| Build | `implement-story` | real code changes; sets `In Progress`, then `Implemented` |
| Review | `review-implementation` | read-only; never marks anything verified |
| Verify | `verify-story` | runs real tests, records results, sets `Verified` only from passing evidence |
| Progress | `sdlc-status` | read-only snapshot and next actions |
| Publish | `publish-stories` | preview, your confirmation, then GitHub Issues |
| Explore / check | `sdlc-explore`, `sdlc-validate` | navigate documents; validate structure |

Each creating Skill checks for **overlaps** with existing documents (a deterministic CLI check, then the agent's own contextual review) and asks you whether to revise the existing document, relate a new one, or create a new one **before** an ID is allocated.

## 5. Core concepts

- **Document IDs:** `BR-001`, `PR-001`, `US-001`, `DES-001`, `PLAN-001`, `RES-001`, `TEST-001`. Allocated only by `sdlc allocate-id`, recorded in the ledger and never reused (retired IDs stay retired).
- **Requirement IDs:** `PR-001-R001`: scoped to the document that declares them. Stories cite them in `covers` and link the source documents under *Derived From*.
- **Maps:** every managed folder has a `map.md`. Its generated region (between the `sdlc:generated` markers) is produced by `sdlc update-map` from document metadata and relationships. Hand-written text outside the markers is preserved.
- **Relationships:** each document's *References* section (*Derived From*, *Related To*, *Supporting Artifacts*) uses relative Markdown links the validator checks.
- **Document `status`:** `Draft`, `In Review`, `Approved`, `Superseded`. Only you approve: set `status: Approved` yourself, then run `sdlc update-map` (maps show each document's status, so a hand edit leaves them stale until you do; `sdlc validate` reports `stale-map`). A material edit to an Approved document returns it to `In Review`.
- **Story `delivery_status`:** `Not Started`, `Ready`, `In Progress`, `Implemented`, `Verified`: independent of `status`. Only `implement-story` sets `Implemented`; only `verify-story` sets `Verified`, and only when every decided acceptance criterion has a current, passed run recorded in the Test Plan.
- **TBD / unresolved acceptance behavior:** if the outcome is not decided it stays an explicit `TBD` under *Unresolved Acceptance Behavior*; it is never turned into an invented criterion and is never counted as verified.
- **Validation:** `sdlc validate` checks structure, front matter, IDs, ledger, links, traceability, maps and the evidence formats. Errors exit `1`; warnings and notices exit `0`.
- **Coverage notices:** informational only: Stories with `covers: []` and PR requirements no Story covers.
- **Publication records:** a published Story carries a `## Publication` section (`PUB-n`: provider, repository, Issue number, URL). They are operational metadata: they do not change requirements or approval.
- **Markdown authority:** local files are authoritative. GitHub is a one-way publication target: nothing is imported back and Issues are never updated or closed by this tool.

## 6. Publishing Stories to GitHub Issues

1. **Authenticate `gh` yourself:** `gh auth login` (or `GH_TOKEN`/`GITHUB_TOKEN` in your environment). The library never reads, stores or prints a credential, and `validate` rejects credential-looking keys in the config.
2. **Configure the target** in `.sdlc/config.md` front matter (exactly these two keys):

   ```yaml
   publishing:
     provider: github
     repository: owner/repository
   ```

3. **Ask your agent:** *"Use the publish-stories skill to publish US-001."* You name the Stories; nothing is published by default.
4. **Preview.** `sdlc publish-preview US-001` (the Skill runs it) is offline and shows the exact title, the complete body, labels (none), warnings (for example the Story is not Approved, or contains TBDs), and whether the Story is already published. It also prints a digest of exactly that content.
5. **Confirm explicitly.** Only a clear "yes, publish US-001 to owner/repository" counts; a question, "looks good", or silence does not. The Skill then runs `sdlc publish-apply US-001 --confirm-digest <digest>`. The command refuses unless the digest still matches a fresh preview of the current files: if the Story, the selection or the repository changed after you looked, nothing is published and you are shown a new preview.
6. **Result.** The Issue number and URL are reported and recorded as `PUB-n` in the Story. Success is recorded only after GitHub accepts the Issue.

**Duplicate prevention.** Identity is **Story + provider + repository**. A Story already published to the configured repository is shown as already published and skipped. The same Story can be published to a *different* repository (with its own preview and confirmation). Issues are never matched by title.

**Boundaries.** One way only: the library does not update, close, label or sync Issues, and does not read them back. Local Markdown stays authoritative.

## 7. Command reference

`sdlc <command> --help` lists every option. Add `--json` for machine-readable output. The full contract (outputs, exit codes, validator codes) is in `shared/cli-contract.md`, which ships inside the package at `sdlc/library/shared/`.

| Command | Purpose |
|---|---|
| `init`, `create-dir` | create the project layout / an `Artifacts` subfolder |
| `allocate-id`, `retire-id` | reserve or tombstone IDs |
| `update-map` | regenerate the generated region of `map.md` files |
| `list`, `references`, `find-overlaps` | read-only discovery |
| `validate` | check the whole project |
| `status` | read-only progress snapshot |
| `publish-preview`, `publish-apply` | GitHub Issue publication (preview offline; apply only with the confirmed digest) |

## 8. Troubleshooting

- `sdlc: command not found`: run `pipx ensurepath` and open a new shell.
- A Skill says the CLI is missing: the agent's shell cannot see `sdlc`; start the agent from a shell where `sdlc --version` works.
- `conflict` from an install command: a real file or foreign link already occupies the Skill name; remove it or choose `--skill`.
- `stale-map`: run `sdlc update-map`. `duplicate-id` after a merge: the `sdlc-validate` Skill walks you through renumbering.
- Publishing fails with `provider-auth`: run `gh auth login`. Nothing is recorded when publishing fails.
