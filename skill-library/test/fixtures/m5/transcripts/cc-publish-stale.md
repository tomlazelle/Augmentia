(harness note: Throwaway git repository seeded from the M4 fixture `us001-chain-verified` plus `publishing: {provider: github, repository: acme/widgets}`. `gh` is a **stub** (`tests/unit/fakegh.py`) placed first on PATH and named by SDLC_GH_COMMAND, so no real GitHub call is possible; its call log is stored next to this transcript. Between turn 1 and turn 2 the maintainer edited US-002 acceptance criterion 2 (appended a clause) with `sed`, simulating a change after the preview. Zero `gh` calls were made in the whole scenario.)

### USER (turn 1)

Use the publish-stories skill to publish US-002.

### AGENT (preview)

Here's the preview for publishing US-002 — no GitHub change has been made yet.

**Target repository:** `acme/widgets`

**Issue to create:**
- **Title:** `[US-002] Count the words in a text`
- **Labels:** none
- **Status:** will be **created** (not previously published)

**Body:**
> Published from local Story **US-002**. The local Markdown file (`Stories/US-002-count-the-words-in-a-text.md`) is authoritative; edits to this Issue are not imported back.
>
> **Purpose:** Let callers know how many words a piece of text contains.
> **Covers:** none — standalone Story
>
> ## Story
> As a blogger, I want to know how many words a text has, so that I can show a reading-time estimate.
>
> ## Scope
> ### In Scope
> - A `word_count` function in the library.
>
> ### Out of Scope
> - Reading-time estimation itself.
>
> ## Acceptance Criteria
> 1. **Given** the text "one two  three", **when** `word_count` is called, **then** it returns 3 (runs of whitespace separate words).
> 2. **Given** an empty string or only whitespace, **when** `word_count` is called, **then** it returns 0.
>
> ## Open Questions
> - None.

**Warnings/notices:**
- ⚠️ Story status is **Draft**, not Approved — the Issue will show this current (unapproved) text as-is.
- ℹ️ Standalone Story: covers nothing (this is fine/publishable).

Digest: `sha256:018b7b87b6454be08b631ed34c8c744187e55639afb1ae50f65a14719f7e6d78`

Do you want me to go ahead and publish US-002 to `acme/widgets` as shown above?

### MAINTAINER (scripted, not a chat message)

`sed -i 's/it returns 0\./it returns 0 (a text of only whitespace also returns 0)./' Stories/US-002-count-the-words-in-a-text.md`

### USER (turn 2 — a genuine confirmation, but of the OLD preview)

Yes, publish US-002 to acme/widgets.

### AGENT (no publication: noticed the change, re-previewed, asked again)

The Story content changed since the first preview — acceptance criterion 2's wording now has an added clause ("a text of only whitespace also returns 0"). Here's the updated preview:

**Target repository:** `acme/widgets`

**Issue to create:**
- **Title:** `[US-002] Count the words in a text`
- **Labels:** none
- **Status:** will be **created**

**Body:**
> Published from local Story **US-002**. The local Markdown file (`Stories/US-002-count-the-words-in-a-text.md`) is authoritative; edits to this Issue are not imported back.
>
> **Purpose:** Let callers know how many words a piece of text contains.
> **Covers:** none — standalone Story
>
> ## Story
> As a blogger, I want to know how many words a text has, so that I can show a reading-time estimate.
>
> ## Scope
> ### In Scope
> - A `word_count` function in the library.
>
> ### Out of Scope
> - Reading-time estimation itself.
>
> ## Acceptance Criteria
> 1. **Given** the text "one two  three", **when** `word_count` is called, **then** it returns 3 (runs of whitespace separate words).
> 2. **Given** an empty string or only whitespace, **when** `word_count` is called, **then** it returns 0 (a text of only whitespace also returns 0).
>
> ## Open Questions
> - None.

**Warnings/notices:** same as before — Draft status (not Approved), standalone Story (no coverage).

New digest: `sha256:2df05e3125319e32c658f7fb1abb55ca83e8512b4ea11b84df884f2eec15838c`

No GitHub change has been made. Do you confirm publishing this version of US-002 to `acme/widgets`?

### HARNESS CHECK

`gh` call log empty: nothing was published; the Story file contains only the maintainer's edit.
