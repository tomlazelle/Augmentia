# codex — 01-init

### USER

Use the sdlc-init skill: check whether this project is initialized, initialize it if it is not, and tell me what exists.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 35 s)

The project was already initialized. I reran `sdlc init --project-name "project-codex"`; it reported all existing files and left them untouched.

The project contains:

- `.sdlc/config.md` and `.sdlc/ledger.md`
- Root `map.md`, plus indexes in `BR/`, `PR/`, `Stories/`, and `Artifacts/`
- `AGENTS.md` and `CLAUDE.md`
- No requirement, product, Story, or Artifact documents yet

`sdlc update-map` found all maps unchanged. `sdlc validate` reported **0 errors, 0 warnings, and 0 notices**.

The root `map.md` has a summary paragraph for you to fill in. Authoring Skills create the SDLC documents; `Artifacts/design/`, `Artifacts/plans/`, `Artifacts/research/`, and `Artifacts/tests/` are created when first used.

