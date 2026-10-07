### USER

Use the verify-story skill for US-001. I authorize running commands. Project policy for this verification: AC-1, AC-3 and AC-5 count when pytest shows them passing; AC-2 counts ONLY if the command frobnicate --check 'Hello, World!' exits 0 (that tool may not be installed); AC-4 counts ONLY if a person confirms it in the blog preview, which nobody has done yet. Record what actually happens.

### AGENT (claude -p, project skills via install/claude_code.py)

## Verification result for US-001: stays `Implemented`, not `Verified`

**One flag first:** TEST-001's own scenario mapping ties AC-2 and AC-4 to ordinary `pytest` scenarios (TS-2, TS-4), same as the other three ACs. The policy you gave for this run overrides that — designating `frobnicate` and a human blog-preview check as the *only* qualifying evidence for AC-2 and AC-4 respectively — which isn't written anywhere in the Story or Test Plan. I followed your policy for the verification decision, but recorded both runs' actual results.

**What I ran:**

| AC | Check | Result |
|---|---|---|
| AC-1, AC-3, AC-5 | `python -m pytest -q` → exit 0, `9 passed in 0.01s` | **passed** |
| AC-2 | `frobnicate --check 'Hello, World!'` → exit 127, `command not found` (not installed) | **blocked** — doesn't count per your policy, even though pytest's TS-2 also passed |
| AC-4 | Manual blog-preview confirmation | **not-run** — nobody has performed it, even though pytest's TS-4 also passed |

All three runs are recorded as VR-1, VR-2, VR-3 in TEST-001's Verification Runs section, with real commands, exit codes, and observations.

**Decision:** Since AC-2 and AC-4 don't have a current passing run under the stated policy, not every decided criterion is proven, so `delivery_status` stays `Implemented` — I did not set `Verified`.

**Validate:** `python -m sdlc update-map` then `python -m sdlc validate` → 0 errors, 0 warnings, 2 notices (both pre-existing and unrelated to US-001: an uncovered PR-001-R002 requirement and standalone US-002).

**Next steps to actually reach `Verified`:** either install `frobnicate` and get a clean `--check` run, or get someone to confirm AC-4 in the blog preview — or, if you didn't mean to impose those extra gates, TEST-001's own pytest scenarios already pass all five ACs and a normal re-run of `verify-story` without that override would set `Verified`.

