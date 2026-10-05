# Test Plan Section Catalog

Audience: implementers, reviewers and whoever verifies the Story. A Test Plan (`TEST-NNN`, `Artifacts/tests/`) maps each **decided acceptance criterion** of a Story to one or more test scenarios, and later holds the append-only **Verification Runs** written by `verify-story`. It works with or without a Design or Plan.

| Section | Core? | Content |
|---|---|---|
| Front matter | Core | `id`, `title`, `purpose` (one sentence), `status: Draft`, `created`, `updated` |
| References | Core | `Derived From`: source Story link(s) with requirement IDs; `Related To`: Design/Plan if any |
| Scope | Core | Story and criteria covered |
| Repository Context | Core | **Inspected** existing tests/code actually opened; **Not inspected / unavailable** |
| Test Scenarios | Core | `### TS-n` per scenario: Criterion (`AC-n` = position in the Story's numbered acceptance criteria), Method (automated/manual), Setup, Steps, Expected result, Evidence to capture |
| Failure, Boundary and Regression Cases | Core | Proportionate to the Story; each with a decided expected result |
| Unresolved Acceptance Behavior (TBD) | Optional | `- **TBD** — …` bullets for undecided behavior |
| Verification Runs | Core | `None recorded.` until `verify-story` appends `### VR-n` runs (format in `../../../shared/technical-conventions.md` §5) |

## Using the template

`template.md` is the exact layout. Replace every `{{PLACEHOLDER}}`, add one `### TS-n` block per scenario, delete what does not apply, leave no `{{...}}` text behind. Source Story links are relative from `Artifacts/tests/` (`../../Stories/US-001-slug.md`).

## Rules

- **Every decided criterion** gets at least one scenario; number them exactly as the Story's numbered list (`AC-1` is the first numbered criterion).
- **TBD is not a test.** Undecided acceptance behavior goes under *Unresolved Acceptance Behavior (TBD)* with no expected result. If the Story has no decided criteria, stop and suggest `refine-stories`.
- Expected results are the Story's decided results, never your guess. Prefer automated scenarios that can be run with the project's real test command; mark manual ones as manual and say who is expected to perform them.
- **A test plan is not a verification.** Never write `Verification Runs` entries, results or a "passed" claim in this Skill; leave `None recorded.` Editing scenarios of an Approved plan is a material change (Approved → In Review); appending runs later is not.
- Do not change the Story's `delivery_status`.
