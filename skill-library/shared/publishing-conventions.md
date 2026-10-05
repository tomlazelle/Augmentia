# Publishing and Status Conventions (R3)

Shared by `publish-stories` and `sdlc-status`. The CLI (`cli-contract.md`) is the authority for rendering, digests, duplicate detection and record writing; Skills add the conversation and the human gate, never a second implementation.

## 1. Invariants

- **Local Markdown is authoritative.** GitHub is only a publication target. Nothing is imported back; Issue state, edits or closure never change a local Story, and local completion is never inferred from an Issue.
- **No external write without a shown preview and explicit human confirmation.** Preview is offline. Only `publish-apply` mutates, and only with a matching confirmed digest.
- Publishing **never** changes requirements, acceptance criteria, document `status` or Story `delivery_status`.
- **No credentials** in `.sdlc/config.md`, documents, maps, the ledger, fixtures or evidence. Authentication comes from the user's own `gh` login or `GH_TOKEN`/`GITHUB_TOKEN` in the environment. `validate` rejects credential-looking keys under `publishing`.
- GitHub Issues are the only target. No Jira, Projects, labels, milestones, branches, PRs, releases, automatic updates/closure, polling or webhooks.

## 2. Configuration (`.sdlc/config.md`)

```yaml
publishing:
  provider: github
  repository: owner/repository
```

Exactly these two keys. Missing config, an unsupported provider or a malformed repository blocks publication (`publishing-config-missing`, `publishing-unsupported-provider`, `publishing-config-invalid`); it is never reported as success. Ask the human for the repository and add only these two keys (config is a CLI-maintained file: edit nothing else in it).

## 3. Selection and eligibility

The human names the Stories (`US-001 US-002`). Never publish "all". `publish-preview` blocks a Story (`blocked`, preview shows why) when it does not exist, has validation errors of its own (front matter, broken or unknown references, duplicate ID, malformed Publication record), or its `## Publication` section cannot be read (a hidden prior publication would risk a duplicate). It warns, without blocking, about: document status not Approved, unresolved acceptance behavior (TBD), no numbered acceptance criteria, relative links that will not resolve on GitHub. A valid standalone Story (`covers: []`) is publishable; no BRD, PRD, Design, Plan or Test Plan is required.

## 4. Issue representation

- **Title:** `[US-001] <Story title>`. **Labels:** none (labels are never created).
- **Body:** a header (statement that local Markdown is authoritative and names the file, `Purpose`, `Covers` or "none — standalone Story", `Derived From`/`Related To`/`Supporting Artifacts` as document IDs) followed by the Story's own text **verbatim**: Story, Scope, Business Rules, Acceptance Criteria, **Unresolved Acceptance Behavior (TBD)**, Edge Cases, Open Questions. Omitted because they are local or operational: the H1, `## References` (relative links), `## Implementation Record`, `## Review Record`, `## Publication`. Nothing is invented, reworded or hidden.

## 5. Preview digest and confirmation boundary

`publish-preview` returns `digest` = SHA-256 over the canonical form of: provider, repository, and for each selected Story its id, action (`create`/`skip`/`blocked`), exact Issue title, exact Issue body and known publication. The human is shown that content; their confirmation applies to that digest only.

`publish-apply <ids> --confirm-digest <digest>` recomputes the preview from the **current** files and proceeds only if the digests are equal. Any change to Story content, the selection, the repository or publication state changes the digest, so a stale confirmation fails with `preview-stale` and nothing is published; the Skill must re-preview and ask again. A refused apply never prints the current digest. Use only the digest from the preview the human actually saw.

**What counts as confirmation:** an unambiguous affirmative reply to *this* preview ("yes, publish US-001 and US-002 to acme/widgets"). Not confirmation: invoking the Skill, asking for a preview, asking what would happen, silence, "looks good", "maybe", "ok?", a question, or a confirmation of an earlier preview.

## 6. Publication record (identity and duplicate prevention)

After GitHub reports success, `publish-apply` appends to the Story:

```markdown
## Publication

### PUB-1 — 2026-10-04
- **Provider:** github
- **Repository:** acme/widgets
- **Issue:** #7
- **URL:** https://github.com/acme/widgets/issues/7
```

`Provider` (`github`), `Repository` (`owner/name`) and `Issue` (`#N`) are required; `URL` is recorded when returned. Append-only; `validate` checks the format (`publication-invalid`). **Publication identity is Story + provider + repository.** A Story with a valid PUB entry for the *configured* `provider` and `repository` is **known** there: preview shows it, marks the Story `skip`, and `publish-apply` creates nothing for it. PUB entries for a *different* repository (or provider) do not block publication to the configured one: preview lists them as `published-elsewhere` notices (`other_publications`) and the Story is `create`, still requiring the full preview and explicit confirmation. Each repository gets its own entry (`PUB-1` for `org/repo-a`, `PUB-2` for `org/repo-b`). An Issue is never matched to a Story by its title.

**Non-material metadata.** Appending a Publication record, like Implementation/Verification/Review records, does **not** reset an Approved Story to In Review and is never a change to requirements or acceptance criteria. `updated` is set to today; `status`, `delivery_status`, `covers` and every other field are untouched, and maps and the ledger are not affected.

## 7. Failure handling

| Situation | Result |
|---|---|
| Missing/invalid config, unsupported provider | blocked before anything else; nothing contacted |
| `gh` missing, not authenticated, repository not found/inaccessible, Issues disabled | `publish-apply` fails its read-only preflight (`provider-unavailable`, `provider-auth`, `repository-not-found`, `issues-disabled`) before creating anything; nothing recorded |
| API/network failure or rejection on one Story | that Story `failed`, nothing recorded for it; other confirmed Stories still attempted; exit `1` |
| Partial success | reported per Story (`published`, `skipped`, `failed`, `not-attempted`) |
| Story already published | `skipped`, no mutation |
| Story or selection changed after preview | `preview-stale`; re-preview and re-confirm |
| Validation error on a selected Story | that Story is `blocked`; the preview cannot be applied until fixed |
| `gh` exits 0 but returns no Issue URL | `unconfirmed`: an Issue may exist. Stop, do not retry blindly, ask the human to check the repository |
| GitHub succeeded but recording failed | `published-unrecorded` with `record-failed`: report the inconsistency prominently with the Issue URL, stop, do not publish that Story again; add the `PUB-n` entry by hand in the format above |

Success is reported only for outcomes `published`; never from a preview, a plan, or an exit code alone.

## 8. `sdlc-status` report

`sdlc status` (read-only) returns the project health (validation counts, errors, warnings, stale maps, broken references), the document inventory by status for BR, PR, US, DES, PLAN, RES, TEST (an absent optional artifact is not a defect), Story counts by `delivery_status` (Not Started, Ready, In Progress, Implemented, Verified), traceability (uncovered PR requirements, standalone Stories, invalid references, unresolved TBD) and an ordered *needs attention* list: validation errors, failed/blocked/not-run verification evidence, unresolved acceptance behavior, Implemented-awaiting-verification, In Progress, Ready, and documents In Review. Coverage notices stay informational. `status` exits `0` whenever it produces the report; health is in `result.health`.
