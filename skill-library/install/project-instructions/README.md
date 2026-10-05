# Project instruction templates

The canonical texts live in `sdlc/templates/AGENTS.md` (Codex and other agents) and `sdlc/templates/CLAUDE.md` (Claude Code); they are packaged with the CLI. `python -m sdlc init` copies each into the project root **only if that path does not already exist**: an existing `AGENTS.md`/`CLAUDE.md` (file or symlink) is never read, appended to or overwritten. If a project already has its own instructions, add the guidance from the template by hand.

The guidance is narrow: when modifying an SDLC-governed document, invoke or consult the relevant creating Skill and follow its revision rules, including the Approved → In Review rule. It is guidance only: no runtime mechanism, hashing or state. Keep the two templates' text identical.
