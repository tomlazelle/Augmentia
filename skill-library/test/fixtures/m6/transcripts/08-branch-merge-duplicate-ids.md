# Simulated branch merge with duplicate IDs (original M6 checklist item)

Real git history, no agent, pipx-installed `sdlc 1.0.0rc1`. In a scratch repository (`sdlc init`, one base commit) two branches were each created from `main` and each ran `sdlc allocate-id --category US --title ...` (both received `US-001`), wrote their Story, ran `sdlc update-map`, and committed (`branch-a`: "Export tasks", `branch-b`: "Archive tasks"). `branch-a` merged cleanly. Merging `branch-b` conflicted in `Stories/map.md` (generated region); the maintainer took `--ours` and regenerated it with `sdlc update-map` (the supported fix for map conflicts), then committed the merge.

```text
$ ls Stories
US-001-archive-tasks.md  US-001-export-tasks.md  map.md
$ sdlc validate
error: Stories/US-001-archive-tasks.md: [US-001] document ID US-001 is also used by: Stories/US-001-export-tasks.md (duplicate-id)
error: Stories/US-001-export-tasks.md: [US-001] document ID US-001 is also used by: Stories/US-001-archive-tasks.md (duplicate-id)
notice: Stories/US-001-archive-tasks.md: [US-001] standalone Story: covers is empty (story-no-coverage)
notice: Stories/US-001-export-tasks.md: [US-001] standalone Story: covers is empty (story-no-coverage)
2 document(s): 2 error(s), 0 warning(s), 2 notice(s)
exit=1
```

Result: the post-merge duplicate is detected on both files and `validate` exits `1`. (The `sdlc-validate` Skill's renumbering walkthrough is covered by M2's tests and was not re-run with an agent in M6.)
