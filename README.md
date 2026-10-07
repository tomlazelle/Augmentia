# Augmentia

A Markdown-first SDLC toolkit for AI coding agents. It gives **Claude Code** and **Codex** a set of Skills for working through a software lifecycle (business and product requirements, Stories, design, planning, implementation, review, verification, status reporting, and publishing Stories to GitHub Issues) plus a small deterministic command-line tool, `sdlc`, that does the bookkeeping.

Everything lives as plain Markdown in your own repository. The agent runs the conversation; `sdlc` allocates IDs, maintains indexes, validates, reports status and is the only thing that can publish. You stay in charge: agents never approve documents, test evidence comes from tests that were actually run, and nothing is published without a preview you have confirmed.

Release candidate: **`@augmentia/sdlc` 2.0.0-rc.1** (Node.js/TypeScript; M1–M6 behavior approved, M7 migration in progress).

## Install

Prerequisites: Node.js 22+ (with npm), and Claude Code and/or Codex. For publishing you also need the GitHub CLI (`gh`), logged in.

```bash
npm install -g @augmentia/sdlc
sdlc --version          # sdlc 2.0.0-rc.1
```

This installs three commands: `sdlc`, `sdlc-install-claude-code` and `sdlc-install-codex`. To upgrade, run `npm install -g @augmentia/sdlc@<version>`; to remove it, unlink the Skills (below) and run `npm uninstall -g @augmentia/sdlc`.

## Use it in a project

**1. Initialize** (in the repository you want to manage):

```bash
cd your-project
sdlc init
```

This creates `.sdlc/`, `BR/`, `PR/`, `Stories/`, `Artifacts/` (each with a `map.md` index), and `AGENTS.md` / `CLAUDE.md` project instructions. It is idempotent and never overwrites files that already exist, including your own `AGENTS.md` / `CLAUDE.md`.

**2. Connect your agent** (links, not copies, into the installed package; project scope is the verified path):

```bash
sdlc-install-claude-code --scope project     # -> .claude/skills/
sdlc-install-codex       --scope project     # -> .agents/skills/
```

You should see 15 Skills in each folder. Consider adding `.claude/` and `.agents/` to `.gitignore` (the links point into your own npm installation).

**3. Ask your agent to use a Skill.** Start the agent in the project and say, for example:

| You say | What happens |
|---|---|
| "Use the create-brd skill: I want a task-list library that helps people notice overdue tasks." | adaptive interview, then `BR-001` with requirement IDs |
| "Use the create-prd skill for BR-001." | `PR-001` (a BRD is optional) |
| "Use the create-stories skill for PR-001." | `US-001` with acceptance criteria and `covers` links |
| "Use the refine-stories skill on US-001. I declare it Ready." | sharpens criteria without inventing anything |
| "Use the create-design / plan-implementation / create-test-plan skill for US-001." | `DES-` / `PLAN-` / `TEST-` documents (and `RES-` research when useful) |
| "Use the implement-story skill for US-001. I authorize code changes and running the tests." | real code change; `Implemented` |
| "Use the review-implementation skill for US-001." | read-only review; never marks anything verified |
| "Use the verify-story skill for US-001. I authorize running the tests." | runs the tests, records the results, sets `Verified` only from passing evidence |
| "Use the sdlc-status skill." | read-only snapshot and next actions |
| "Use the publish-stories skill to publish US-001." | preview, then publishes only after your explicit confirmation |

You can start at any step: a BRD, PRD or Design is **not** required (a Story can stand alone). Only you approve documents: set `status: Approved` yourself, then run `sdlc update-map`.

**4. Check your work any time:**

```bash
sdlc validate       # structure, front matter, IDs, links, traceability, maps, evidence (errors exit 1)
sdlc status         # read-only progress snapshot
sdlc list           # documents and their statuses
```

## Publish Stories to GitHub Issues

1. Log in to GitHub yourself (`gh auth login`); the tool never reads or stores credentials.
2. Add the target to `.sdlc/config.md`:

   ```yaml
   publishing:
     provider: github
     repository: owner/repository
   ```

3. Ask the agent to use `publish-stories` for the Stories you name. It shows you the exact Issue title and full body first. Reply with a clear "yes, publish US-001 to owner/repository" to confirm; anything vaguer is not confirmation. The tool refuses to publish unless the content you confirmed is still exactly what would be published.
4. The Issue number and URL are recorded in the Story (`## Publication`, `PUB-n`). Publishing the same Story to the same repository again is skipped, not duplicated. Publishing is one-way: Markdown stays authoritative and nothing is imported back.

## Key ideas

- **Markdown is authoritative.** Documents, IDs (`BR-001`, `US-001-…`), requirement IDs (`PR-001-R001`) and relationships are plain files you can read, diff and review.
- **Two separate states.** A document's `status` (Draft, In Review, Approved, Superseded) is about human review; a Story's `delivery_status` (Not Started, Ready, In Progress, Implemented, Verified) is about delivery. Only `implement-story` sets `Implemented`; only `verify-story` sets `Verified`.
- **Unresolved behavior stays visible.** Anything undecided is an explicit `TBD`, never invented and never counted as verified; `sdlc status` and `sdlc validate` keep surfacing it.

## Documentation

- **Full user guide:** [skill-library/README.md](skill-library/README.md) (installation details, agent integration, concepts, publishing, command reference, troubleshooting).
- **Architecture:** [docs/SDLC-SKILL-ARCHITECTURE.md](docs/SDLC-SKILL-ARCHITECTURE.md). **Implementation checklist:** [docs/SDLC-IMPLEMENTATION-CHECKLIST.md](docs/SDLC-IMPLEMENTATION-CHECKLIST.md).
- **Milestone evidence:** `docs/SDLC-M3-EVIDENCE.md` … `docs/SDLC-M6-EVIDENCE.md`.
- **CLI contract:** [skill-library/shared/cli-contract.md](skill-library/shared/cli-contract.md).

## Development

```bash
cd skill-library
npm install
npm test                      # builds, then runs the Node test suite (includes the frozen-corpus replay and the tarball install tests)
npm pack                      # produces augmentia-sdlc-2.0.0-rc.1.tgz
```

The canonical Skills are in `skill-library/skills/`, shared conventions in `skill-library/shared/`, project-instruction templates in `skill-library/templates/`, and the CLI in `skill-library/src/` (TypeScript, compiled to `dist/`). In a source checkout, `node skill-library/bin/sdlc.js` is equivalent to `sdlc`. The frozen behavioral corpus in `skill-library/parity/` is the permanent regression suite for the externally observable behavior of the 1.0 implementation; the Python 1.0.0rc1 implementation that produced it is preserved only as the git tag `python-1.0.0rc1`. Licensed under the [MIT License](LICENSE).
