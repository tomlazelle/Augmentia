# claude — 01-init

### USER

Use the sdlc-init skill: check whether this project is initialized, initialize it if it is not, and tell me what exists.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 17 s)

The project was already initialized — re-running `sdlc init` touched nothing (everything reported `existing`), and `sdlc validate` passes clean: **0 errors, 0 warnings, 0 notices**.

What's there:
- `.sdlc/config.md`, `.sdlc/ledger.md` — internal config and ID ledger
- `AGENTS.md`, `CLAUDE.md` — SDLC guidance files
- Root `map.md` — project name "tasklog", with the hand-written summary still blank ("Describe this project here...") and no open questions recorded
- `BR/`, `PR/`, `Stories/`, `Artifacts/` — each has only an empty `map.md` index, no documents yet

So the scaffolding is in place but no actual BRD, PRD, Stories, or Artifacts have been authored yet. Next steps would be filling in the root `map.md` summary, and using `create-brd` or `create-prd` to start the first real document.

