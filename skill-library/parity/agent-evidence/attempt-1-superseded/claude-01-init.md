# claude — 01-init

### USER

Use the sdlc-init skill: check whether this project is initialized, initialize it if it is not, and tell me what exists.

### AGENT (Claude Code (`claude -p`); project skills linked by the installed `sdlc-install-claude-code`; exit 0, 25 s)

The project was already fully initialized — nothing new needed creating.

**Status:**
- Already present: `.sdlc/config.md`, `.sdlc/ledger.md`, `AGENTS.md`, `CLAUDE.md`, root `map.md`, and `map.md` indexes in `BR/`, `PR/`, `Stories/`, `Artifacts/`.
- `sdlc validate` → 0 documents, 0 errors/warnings/notices (no BRs, PRDs, Stories, or Artifacts have been authored yet).
- Root `map.md`'s hand-written summary still says the placeholder "Describe this project here" — named `# tasklog` but otherwise unfilled in.
- `Artifacts/design|plans|research|tests` subfolders don't exist yet; they'll appear on first use.

Next step would be to fill in the project summary in `map.md`, then start authoring with `create-brd` or `create-prd` depending on where you want to begin.

