---
name: sdlc-init
description: Initialize (or safely re-run initialization of) the Markdown SDLC structure in the current repository — root map.md, BR/, PR/, Stories/, Artifacts/ with map.md indexes, plus the .sdlc config and ID ledger. Use when the user wants to start SDLC documentation in a repo, set up the SDLC folders, or repair missing maps.
---

# sdlc-init

Creates the standard SDLC project structure by running the `sdlc` CLI. Do not create these files or folders by hand and do not reimplement any of the CLI's logic.

The CLI is `python -m sdlc` (installed with `pip install -e <skill-library>`; contract: `../../shared/cli-contract.md`). If it fails with `No module named sdlc`, tell the user to install the library and stop.

## Steps

1. **Confirm the location.** Initialization applies to the current project root (or the nearest ancestor that already has `.sdlc/`). If the current directory looks like a subfolder of a larger repository or the user has not said where the project lives, ask before continuing.
2. **Initialize.** Run `python -m sdlc init --project-name "<name>"`. Use the repository or product name; ask if it is not obvious. It is safe to run repeatedly: existing documents, maps, configuration and ledger are never modified.
3. **Verify.** Run `python -m sdlc validate`. A fresh structure must report 0 errors.
4. **Report.** Tell the user which files were created and which already existed, and the validate summary. If validate reports errors, show them; do not fix by editing the CLI-managed files unless the user asks.
5. **Instruction files.** `init` also creates `AGENTS.md` and `CLAUDE.md` if they were missing (never overwriting). If either was reported as `existing`, tell the user their file was left untouched and that the SDLC guidance from `sdlc/templates/` can be added by hand.
6. **Offer next steps.** The root `map.md` has a hand-written summary paragraph for the user to fill in. Mention that documents are created by the authoring Skills and that `Artifacts/design|plans|research|tests` appear on first use.

## Rules

- `.sdlc/` is internal: never add a `map.md`, front matter or document IDs there, and do not hand-edit `config.md` or `ledger.md`.
- Never delete or overwrite existing content to make initialization "clean".
