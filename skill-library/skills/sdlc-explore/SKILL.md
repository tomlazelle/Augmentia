---
name: sdlc-explore
description: Interactively navigate and summarize the project's SDLC Markdown documents — find what exists, read related documents, follow references, and answer questions about requirements, stories and how they link. Read-only. Use when the user asks what documents exist, what a document says, what is derived from what, or which stories cover a requirement.
---

# sdlc-explore

Answers navigation and context questions about an initialized SDLC project. **Read-only:** never create, edit, allocate, retire or regenerate anything. (For a structured project-wide progress report use `sdlc-status`, released later.)

CLI: `python -m sdlc` (contract: `../../shared/cli-contract.md`). If the project is not initialized (`no .sdlc/` error), suggest `sdlc-init` and stop.

## Steps

1. **Start from the maps.** Read the root `map.md`, then the `map.md` of the directory relevant to the question.
2. **Enumerate with the CLI, not by guessing.** `python -m sdlc list [--category BR|PR|US|DES|PLAN|RES|TEST] [--status Draft|"In Review"|Approved|Superseded]` lists documents (add `--json` when you need to process the output).
3. **Follow the links.** `python -m sdlc references <ID>` shows what a document or requirement (`PR-001-R003`) points to and what points at it, including Stories that `Covers` a requirement. Then read the actual documents involved.
4. **Answer from the documents.** Cite document IDs and give relative Markdown links. Separate what the documents state from what is missing or unknown; do not fill gaps with assumptions, and do not invent approvals or statuses.
5. **Flag trust problems.** If a map looks out of date or a link is broken, say so and suggest `sdlc-validate`; documents are authoritative over maps.

## Rules

- Use only the read commands `list` and `references` (plus `validate` if the user wants a health check). Do not run `init`, `allocate-id`, `retire-id`, `create-dir` or `update-map`.
- When the user wants to create or change a document, say which authoring Skill applies instead of doing it here.
