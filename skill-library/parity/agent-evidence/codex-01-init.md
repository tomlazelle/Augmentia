# codex — 01-init

### USER

Use the sdlc-init skill: check whether this project is initialized, initialize it if it is not, and tell me what exists.

### AGENT (Codex (`codex exec --sandbox workspace-write`); project skills linked by the installed `sdlc-install-codex`; exit 0, 17 s)

The project was already initialized. `sdlc init --project-name "project-codex"` found all standard initialization files in place and left them unchanged:

- `.sdlc/config.md` and `.sdlc/ledger.md`
- Root `map.md` and maps under `BR/`, `PR/`, `Stories/`, and `Artifacts/`
- `AGENTS.md` and `CLAUDE.md`

Validation passed: **0 errors, 0 warnings, 0 notices**. No files were created. The `BR/`, `PR/`, `Stories/`, and `Artifacts/` folders currently contain only their maps; detailed documents and `Artifacts/design`, `plans`, `research`, and `tests` are added when their authoring Skills are used. The root `map.md` has a summary paragraph for you to fill in.

