# SDLC-governed documents

This project keeps its requirements as Markdown under `BR/` (business), `PR/` (product), `Stories/` and `Artifacts/`, indexed by `map.md` files and managed with the `sdlc` CLI (`python -m sdlc`).

**Before you create or modify any document in those folders, invoke the matching Skill or, if you cannot invoke it, read its `SKILL.md` and follow its workflow and revision rules:**

| Folder | Skill |
|---|---|
| `BR/` | `create-brd` |
| `PR/` | `create-prd` |
| `Stories/` | `create-stories` (new), `refine-stories` (existing) |
| `Artifacts/design/`, `Artifacts/plans/`, `Artifacts/tests/` | `create-design`, `plan-implementation`, `create-test-plan` |

This applies to small edits too, and especially to documents whose `status` is `Approved`: a material change to an Approved document must set `status: In Review` and be explained to the user, and only the user can approve. The Skill's revision rules cover this; do not bypass them by editing the file directly.

Story delivery: implementing a Story's code is `implement-story`, reviewing it is `review-implementation`, and verifying it is `verify-story`. A Story's `delivery_status` changes only through those Skills (or the human): only `implement-story` sets `Implemented`, only `verify-story` sets `Verified`, and only from tests and checks that were actually run and recorded.

Other rules the Skills rely on: get IDs only from `python -m sdlc allocate-id` / `retire-id`; run `python -m sdlc update-map` then `python -m sdlc validate` after any change; never edit a `map.md`'s generated region or anything under `.sdlc/` by hand.
