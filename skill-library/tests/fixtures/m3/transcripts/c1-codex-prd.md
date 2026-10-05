### USER

Use the create-prd skill. Product idea: a mobile app that lets library members reserve study rooms. There is no BRD and I don't want one. Ask me your first round of questions; do not write or allocate anything yet.

### AGENT (codex exec, project skills via install/codex.py)

We’ll develop a standalone PRD for a mobile app that lets library members reserve study rooms. No BRD, files, or IDs will be created at this stage.

1. How do members reserve rooms today, and what is the main problem you want the app to solve?
2. Who should the first release serve—all members or a particular group—and is it for one library location or multiple branches?
3. Walk me through the ideal reservation experience. What does a member choose, and is the booking confirmed immediately or approved by staff?
4. What existing room-booking rules must the app respect—for example, booking duration, advance notice, active reservation limits, or cancellations?
5. What must the first release let members accomplish for you to consider it useful, and what can wait?

Short answers are fine; **TBD** or **not applicable** are welcome.

### USER

1. Today they sign a paper sheet at the desk; double bookings and no-shows are the problem. 2. All library members, one branch for v1; multi-branch TBD. 3. Member picks a room, date and time slot and the booking is confirmed immediately; no staff approval. 4. Max 2 hours per booking, max 1 active reservation per member; cancellation rules TBD. 5. v1: browse available slots, book, cancel. Later: reminders, recurring bookings. Show me the draft with assumptions and open questions first; don't write yet.

### AGENT (codex exec resume --last)

codex
**Draft PRD: Library Study Room Reservations**  
Status: Draft for review; no files written or IDs allocated. Standalone PRD with no BRD.

**Product summary**

A mobile app that lets library members browse available study-room slots, reserve a room, and cancel a reservation at one branch. Today, members sign a paper sheet at the desk; double bookings and no-shows are the reported problems.

**Users and needs**

All library members at the initial branch are the target users. They need to find available rooms and receive immediate booking confirmation without staff approval.

**Primary journey**

1. The member browses available study-room slots.
2. They select a room, date, and time slot.
3. The app confirms an eligible booking immediately.
4. The member can cancel their reservation, subject to cancellation rules still to be decided.

**Scope**

| Included in v1 | Deferred | Undecided |
|---|---|---|
| One branch; all library members | Reminders | Multi-branch support |
| Browse available slots, book, cancel | Recurring bookings | Cancellation rules |

**Product requirements — IDs pending**

- Members can browse available study-room time slots.
- Members can book a selected room, date, and time slot.
- Eligible bookings are confirmed immediately without staff approval.
- Each booking is limited to a maximum of two hours.
- Each member is limited to one active reservation.
- Members can cancel their reservations; permitted timing and consequences are TBD.

**Acceptance expectations**

- A member can complete the browse-to-book journey and receive confirmation without staff intervention.
- A booking longer than two hours is rejected.
- A member with one active reservation cannot create another; the definition of “active” remains TBD.
- A member can cancel a reservation in accordance with the agreed cancellation rules.
- Prevention of conflicting reservations needs an explicit acceptance rule, proposed below.

**Constraints and dependencies**

- Initial release serves one branch.
- Mobile platform coverage—iOS, Android, or both—is TBD.
- Member identification and membership verification are TBD.
- The source of room details, opening hours, and available slots is TBD.
- The transition from the paper sheet to the app is TBD.

**Assumptions and proposals**

No additional product decisions are treated as confirmed.

- **Proposed conflict rule:** Overlapping reservations for the same room cannot both be confirmed, including when members book simultaneously. The unsuccessful member sees that the slot is unavailable.
- **Proposed cancellation behavior:** Cancelling releases the slot for others to book and frees the member to make another reservation.
- **Working assumption:** Members cancel only their own reservations; staff capabilities have not been defined.

**Open questions**

1. What counts as an **active reservation**—a future booking, a booking currently in progress, or both—and when does it stop counting?
2. Can members cancel any time before the booking starts? What happens after the start time?
3. How will members identify themselves, and will the paper sheet remain in use alongside the app?
4. Who maintains rooms and bookable slots, and are slot lengths fixed or chosen by members?
5. Should v1 do anything specifically about no-shows, such as check-in or automatic release, or is that deferred?

**Material tradeoffs**

- Immediate confirmation makes conflict prevention essential; the proposed simultaneous-booking rule needs your agreement.
- Keeping reminders for later limits how directly v1 addresses no-shows. Browse, book, and cancel alone do not establish a no-show policy.
- Keeping paper bookings alongside the app requires a shared way to track availability to avoid conflicting reservations.
tokens used
14,349
**Draft PRD: Library Study Room Reservations**  
Status: Draft for review; no files written or IDs allocated. Standalone PRD with no BRD.

**Product summary**

A mobile app that lets library members browse available study-room slots, reserve a room, and cancel a reservation at one branch. Today, members sign a paper sheet at the desk; double bookings and no-shows are the reported problems.

**Users and needs**

All library members at the initial branch are the target users. They need to find available rooms and receive immediate booking confirmation without staff approval.

**Primary journey**

1. The member browses available study-room slots.
2. They select a room, date, and time slot.
3. The app confirms an eligible booking immediately.
4. The member can cancel their reservation, subject to cancellation rules still to be decided.

**Scope**

| Included in v1 | Deferred | Undecided |
|---|---|---|
| One branch; all library members | Reminders | Multi-branch support |
| Browse available slots, book, cancel | Recurring bookings | Cancellation rules |

**Product requirements — IDs pending**

- Members can browse available study-room time slots.
- Members can book a selected room, date, and time slot.
- Eligible bookings are confirmed immediately without staff approval.
- Each booking is limited to a maximum of two hours.
- Each member is limited to one active reservation.
- Members can cancel their reservations; permitted timing and consequences are TBD.

**Acceptance expectations**

- A member can complete the browse-to-book journey and receive confirmation without staff intervention.
- A booking longer than two hours is rejected.
- A member with one active reservation cannot create another; the definition of “active” remains TBD.
- A member can cancel a reservation in accordance with the agreed cancellation rules.
- Prevention of conflicting reservations needs an explicit acceptance rule, proposed below.

**Constraints and dependencies**

- Initial release serves one branch.
- Mobile platform coverage—iOS, Android, or both—is TBD.
### USER

Agree with the proposed conflict rule and cancellation behavior. Active reservation = a future or in-progress booking. The rest stay as open questions. Write it.

### AGENT (codex exec resume --last)

codex
I’ll write the PRD with the agreed conflict and cancellation rules, keep the remaining questions open, and validate the document and indexes.

exec
/bin/bash -lc 'pwd; ls -la; cat /home/tom/projects/Augmentia/skill-library/shared/cli-contract.md /home/tom/projects/Augmentia/skill-library/shared/document-conventions.md /home/tom/projects/Augmentia/skill-library/shared/map-conventions.md /home/tom/projects/Augmentia/skill-library/shared/reference-conventions.md .agents/skills/create-prd/references/template.md' in /tmp/claude-1000/-home-tom-projects-Augmentia/7ed23ca0-3f6c-4934-ac2a-cd2f20906015/scratchpad/m3/c1
 succeeded in 0ms:
/tmp/claude-1000/-home-tom-projects-Augmentia/7ed23ca0-3f6c-4934-ac2a-cd2f20906015/scratchpad/m3/c1
total 0
drwxrwxr-x  5 tom tom 100 Sep 29 16:43 .
drwxrwxr-x 14 tom tom 320 Sep 29 16:33 ..
drwxrwxr-x  3 tom tom  60 Sep 29 16:33 .agents
dr-xr-xr-x  2 tom tom  40 Sep 29 16:43 .codex
drwxrwxr-x  6 tom tom 180 Sep 29 16:42 .git
# `sdlc` CLI Contract

The `sdlc` CLI is the deterministic helper runtime for every Skill. Skills invoke it through the host agent's shell capability and must not re-implement its algorithms (ID allocation, map generation, overlap search, validation).

```text
python -m sdlc <command> [arguments] [--root DIR] [--json]
```

Install from the repository root of the skill library with `pip install -e .` (Python 3.11+, PyYAML). `python -m sdlc --help` and `python -m sdlc <command> --help` list options.

## Conventions

- **Root.** `--root DIR` names the project root. Without it the root is the nearest ancestor of the current directory that contains `.sdlc/`. `init` falls back to the current directory when no such ancestor exists. Every other command exits `2` if no project is found.
- **Output.** Human-readable by default (diagnostics of `validate` on stdout; other commands write diagnostics to stderr). With `--json`, exactly one JSON document is written to stdout.
- **Writes.** Only `init`, `allocate-id`, `retire-id`, `create-dir` and `update-map` write, and only inside the project root. No command contacts external services. The CLI is single-writer: do not run write commands concurrently against one checkout.
- **Dates.** Ledger dates use today's date; the `SDLC_TODAY` environment variable (`YYYY-MM-DD`) overrides it for reproducible runs and tests.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success. `validate` exits `0` when there are no errors, **even if it reports warnings and coverage notices**. |
| `1` | The operation could not complete or found structural problems in the project's *state*: `validate` errors; an unknown, retired or already-retired ID; a corrupt ledger; a `map.md` whose generated-region markers are missing (never rewritten). |
| `2` | Usage or environment error: unknown option/category, malformed ID or title argument, no project found, `--root` is not a project, `update-map` given an unmanaged directory. (argparse usage errors also exit `2`.) |

## JSON envelope (`--json`)


(note: the previous run above was cut off when its output pipe was closed by the harness; project state afterwards: PR-001 allocated in the ledger, no document written)

### USER

Your previous run was interrupted part-way. Check the project state with the CLI and finish writing the PRD as agreed (conflict rule and cancellation behavior accepted; active reservation = future or in-progress booking; the rest stay open questions).

### AGENT (codex exec resume --last)

+- How do members identify themselves and prove membership?
+- Will the paper sheet remain in use alongside the app? If so, how will availability reflect paper bookings?
+- Who maintains room details, opening hours and bookable slots? Are slot lengths fixed or selected by members?
+- Should v1 address no-shows through check-in, automatic release or another policy, or is this deferred?
+- What cancellation permissions and staff capabilities are needed?
+- Which mobile platforms must v1 support?
+- Will multi-branch support be pursued after v1?
+- Owners and resolution dates for these questions: Unknown.
+
+### Material Tradeoffs
+
+- Immediate confirmation requires reliable conflict prevention, including simultaneous booking attempts; the observable conflict rule is agreed.
+- Reminders are deferred. Browse, book and cancel alone do not establish a no-show policy, which remains open.
+- Continuing paper bookings alongside the app would require a shared way to track availability to prevent conflicting reservations; the transition approach remains open.

tokens used
29,015
Created [PR-001 — Library Study Room Reservations](/tmp/claude-1000/-home-tom-projects-Augmentia/7ed23ca0-3f6c-4934-ac2a-cd2f20906015/scratchpad/m3/c1/PR/PR-001-library-study-room-reservations.md) as **Draft**, reusing the previously allocated ID.

- Recorded agreed rules in requirements **PR-001-R001–R010**.
- Kept cancellation policy, membership verification, paper transition, slot management, no-shows, platforms and future branches open.
- Updated indexes; no BRD created.
- Validation: **0 errors, 0 warnings**, 10 expected coverage notices because stories do not exist yet.

The `create-stories` skill can derive stories when you’re ready.
