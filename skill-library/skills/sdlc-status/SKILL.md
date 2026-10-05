---
name: sdlc-status
description: Produce a concise, structured, read-only snapshot of an SDLC project — validation health, document inventory by status, Story delivery states, traceability gaps, and what needs attention next. Use when the user asks for project status, progress, what is outstanding, what is ready to implement or verify, or a status report. Never edits anything.
---

# sdlc-status

Answers: **What is the current project state, what needs attention, and what is ready next?** Audience: the human deciding what to do next. It is a repeatable snapshot; for ad-hoc navigation ("what does this say, what links to it") use `sdlc-explore`.

Rules and report contents: `../../shared/publishing-conventions.md` §8. CLI: `sdlc` (`../../shared/cli-contract.md`). If it fails with `command not found: sdlc`, tell the user to install the library and stop. If the project is not initialized (`no .sdlc/` error), suggest `sdlc-init` and stop.

## Steps

1. **Always derive state from the files now**, never from conversation memory or an earlier report. Run `sdlc status` (add `--json` if you need to process it; the human form is already the report layout).
2. **Present the report** in this order, concisely: *Project health* (validation result, errors/warnings/notices, stale maps, broken references), *Document inventory* (BR, PR, US, DES, PLAN, RES, TEST by status), *Story delivery* (Not Started, Ready, In Progress, Implemented, Verified), *Traceability*, *Needs attention / next actions*.
3. **Interpret carefully.**
   - Coverage notices (uncovered PR requirements, standalone Stories with `covers: []`) are **informational**, not failures.
   - A missing optional DES, PLAN, RES or TEST is **not a defect**.
   - Keep `Ready`, `In Progress`, `Implemented` (awaiting verification) and `Verified` distinct; `Implemented` is not `Verified`.
   - Documents `In Review` are waiting on a human decision; do not suggest approving them yourself.
   - Report failed/blocked/not-run verification evidence and unresolved TBD plainly.
4. **Suggest next actions as options**, naming the Skill that would do each (`sdlc-validate`, `refine-stories`, `implement-story`, `verify-story`, `publish-stories`, …). Do not perform them.

## Rules

- **Read-only.** Run only `sdlc status` (and `list`/`references`/`validate` if you need more detail). Never run `init`, `allocate-id`, `retire-id`, `create-dir` or `update-map`; never edit files, change `status` or `delivery_status`, publish, implement or verify.
- If the report shows stale maps, say so and point to `sdlc-validate`; do not regenerate them here.
- Do not invent counts, statuses or progress the command did not report.
