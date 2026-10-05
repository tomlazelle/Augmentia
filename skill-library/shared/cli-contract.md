# `sdlc` CLI Contract

The `sdlc` CLI is the deterministic helper runtime for every Skill. Skills invoke it through the host agent's shell capability and must not re-implement its algorithms (ID allocation, map generation, overlap search, validation).

```text
sdlc <command> [arguments] [--root DIR] [--json]
```

Install with `pipx install <package>` (Python 3.11+, PyYAML; development: `pip install -e .` from the skill-library checkout). The console command is `sdlc`; `python -m sdlc` is an exact equivalent wherever the package is importable. Skills and templates always say `sdlc`. `sdlc --version`, `sdlc --help` and `sdlc <command> --help` list version and options.

## Conventions

- **Root.** `--root DIR` names the project root. Without it the root is the nearest ancestor of the current directory that contains `.sdlc/`. `init` falls back to the current directory when no such ancestor exists. Every other command exits `2` if no project is found.
- **Output.** Human-readable by default (diagnostics of `validate` on stdout; other commands write diagnostics to stderr). With `--json`, exactly one JSON document is written to stdout.
- **Writes.** Only `init`, `allocate-id`, `retire-id`, `create-dir`, `update-map` and `publish-apply` write, and only inside the project root (`publish-apply` writes only the `## Publication` section and `updated` of a published Story). **No command contacts an external service except `publish-apply`**, and only after its confirmation check passes (below); `status` and `publish-preview` are offline and read-only. The CLI is single-writer: do not run write commands concurrently against one checkout.
- **Dates.** Ledger dates use today's date; the `SDLC_TODAY` environment variable (`YYYY-MM-DD`) overrides it for reproducible runs and tests.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success. `validate` exits `0` when there are no errors, **even if it reports warnings and coverage notices**. |
| `1` | The operation could not complete or found structural problems in the project's *state*: `validate` errors; a blocked or refused publication; an unknown, retired or already-retired ID; a corrupt ledger; a `map.md` whose generated-region markers are missing (never rewritten). |
| `2` | Usage or environment error: unknown option/category, a missing or non-Story selection for `publish-*`, malformed ID or title argument, no project found, `--root` is not a project, `update-map` given an unmanaged directory. (argparse usage errors also exit `2`.) |

## JSON envelope (`--json`)

```json
{
  "schema_version": 1,
  "command": "validate",
  "ok": true,
  "exit_code": 0,
  "result": { },
  "diagnostics": [
    {"severity": "error", "code": "broken-link", "message": "...", "path": "PR/PR-001-x.md", "id": "PR-001", "line": 12}
  ]
}
```

`ok` is `exit_code == 0`. `result` is command-specific (below). `path` is relative to the project root with `/` separators; `id`, `path`, `line` are `null` when not applicable. Keys are stable within `schema_version`.

**Severities:** `error` (structural; makes `validate` exit `1`), `warning` (worth fixing; exit unaffected), `notice` (coverage information; exit unaffected).

## Commands

### `init [--project-name NAME]`
Idempotently creates `.sdlc/config.md`, `.sdlc/ledger.md`, `BR/`, `PR/`, `Stories/`, `Artifacts/` and a `map.md` in the root and each of those four directories. Existing files are never modified (custom map text, configuration and ledger contents are preserved). Newly created maps are populated from any documents already present. `.sdlc/` gets no `map.md`.
Also installs `AGENTS.md` and `CLAUDE.md` in the project root from the packaged templates (`sdlc/templates/`), **create-if-missing**: if either path already exists (file, symlink, even dangling) it is left byte-for-byte untouched and reported under `existing`; instructions are never read, appended to or overwritten. They carry the narrow guidance to invoke/consult the creating Skill when modifying SDLC-governed documents. They are not authored documents and are ignored by `validate` and the maps.
Result: `{"root", "created": [...], "existing": [...]}`.

### `allocate-id --category BR|PR|US|DES|PLAN|RES|TEST [--title TITLE]`
Reserves the next document ID: one above the highest ID in the ledger **or** on disk for that category (so deleting the newest document never recycles its ID), and records it in the ledger. With `--title`, also returns the target path `<dir>/<ID>-<kebab-title>.md`.
Result: `{"id", "kind": "document", "category", "directory", "path"}` (`path` is `null` without `--title`). The command does not create the document.

### `allocate-id --requirement DOC-ID`
Reserves the next requirement ID in a document (`PR-001` → `PR-001-R003`), one above the highest in the ledger or declared in the file. The document must be on disk or allocated in the ledger, and not retired.
Result: `{"id", "kind": "requirement", "document"}`.

### `retire-id ID [--replaced-by ID] [--note TEXT]`
Tombstones a document or requirement ID (state `Retired`); the number is never reissued. `--replaced-by` must be the same kind. The replacement is stored in the ledger note as `Replaced by <ID>.`, and `validate` cites it in retired-reference errors. Retiring a document that still exists on disk succeeds with a `retired-still-present` warning.
Result: `{"id", "kind", "state": "Retired", "replaced_by", "note"}`.

### `create-dir --artifact design|plans|research|tests`
Creates `Artifacts/<name>/` and its `map.md` on first use, then refreshes `Artifacts/map.md` so it links the subdirectory. Safe to repeat. Requires an initialised project.
Result: `{"directory", "directory_created", "<name>_map", "Artifacts_map"}` (map actions: `created|updated|unchanged|blocked`).

### `update-map [DIRECTORY]`
Regenerates only the text between `<!-- sdlc:generated:start -->` and `<!-- sdlc:generated:end -->` in every map (or in the map of one managed directory). Text outside the markers is preserved. A map without exactly one marker pair is left untouched and reported (`map-markers`, exit `1`). Writes only when content changes.
Result: `{"created": [...], "updated": [...], "unchanged": [...], "blocked": [...]}`.

### `list [--category C] [--status S]`
Lists valid documents sorted by category then number. Documents with metadata errors are skipped with a `skipped-invalid` warning.
Result: `{"count", "documents": [{"id","title","category","status","path","purpose"} + "delivery_status" for Stories]}`.

### `references ID`
Outgoing and incoming references for a document or requirement ID. Unknown IDs exit `1`; retired IDs are answered from the ledger (`state: "Retired"`, `replaced_by` when known).
Result: `{"id","kind","state","title","path" | "defined_in", "outgoing": [...], "incoming": [...]}` where each outgoing item is `{"relationship","requirements","href","target":{"id","path"}|null}` and each incoming item is `{"relationship","requirements","source":{"id","path"}}`. Relationships are `Derived From`, `Related To`, `Supporting Artifacts` (from a document's References section) and `Covers` (a Story's `covers` list).

### `find-overlaps --category C --title T [--purpose P] [--covers ID ...]`
**`--covers` is a search hint.** It accepts requirement IDs *and* document IDs (a document ID matches candidates that reference any of its requirements or link it under `Derived From`). This differs from a Story's front matter `covers`, which contains **requirement IDs only**.

Ranks existing documents that a proposed document might duplicate. Advisory only: it never creates, merges or edits anything, and the calling Skill must present candidates to the human. Scoring is lexical: a same-topic document worded differently may score below the threshold, so the creating Skills follow it with a separate, unscored *contextual overlap review* by the agent (see the Skills).
Result: `{"category","title","candidates": [{<list fields>, "score","level","reasons"}], "action": "ask-human"|"none"}`.

**Scoring (deterministic).**
1. Only documents of the same category that are valid and not `Superseded` are considered.
2. *Normalized title tokens:* lowercase, split on non-alphanumerics, drop the stopwords `a an the of for and to in on with or`, strip a trailing plural `s` from words longer than three letters (except `ss`). Purpose text is normalized the same way.
3. `title` = Jaccard similarity of title tokens (`1.0` when the token sets are identical). `purpose` = Jaccard of purpose tokens (used only if `--purpose` is given). `refs` = fraction of `--covers` IDs the candidate is tied to — through its `covers`, requirement IDs in its References lists, or `Derived From` document links; a document ID in `--covers` also matches a candidate that references any requirement of that document (used only if `--covers` is given).
4. `score` = weighted mean of the signals supplied, with weights `title 0.5`, `purpose 0.3`, `refs 0.2`, renormalized over the supplied signals. Identical normalized titles raise the score to at least `0.75`.
5. `score >= 0.75` → `likely`; `0.40 <= score < 0.75` → `possible`; lower scores are omitted. Candidates sort by descending score, then ID. `reasons` lists what matched. `possible` matches are ambiguous and always need human confirmation; so do `likely` ones.

### `validate`
Checks the whole project. It reads only. Exit `1` if any `error` is found.

| Code | Severity | Meaning |
|---|---|---|
| `missing-config`, `bad-config` | error | `.sdlc/config.md` missing or violates the minimal schema |
| `unknown-config-key` | warning | unrecognised configuration key |
| `missing-ledger`, `bad-ledger`, `bad-ledger-row`, `duplicate-ledger-id` | error | ledger unreadable or inconsistent |
| `missing-directory`, `missing-map` | error | required directory / `map.md` missing |
| `map-markers` | error | map lacks its generated-region markers |
| `stale-map` | error | generated region differs from what `update-map` would write |
| `unexpected-directory` | warning | folder outside the managed layout (ignored) |
| `bad-front-matter`, `missing-field`, `invalid-field`, `invalid-purpose`, `invalid-id`, `invalid-status`, `invalid-date`, `invalid-delivery-status`, `missing-covers`, `invalid-covers` | error | front matter problems |
| `date-order` | warning | `updated` earlier than `created` |
| `bad-filename`, `id-filename-mismatch`, `wrong-directory`, `misplaced-document` | error | filename/ID/location problems |
| `malformed-requirement`, `requirement-wrong-document` | error | requirement declaration problems |
| `duplicate-id`, `duplicate-requirement` | error | an ID used more than once (reported on every involved file; catches post-merge collisions) |
| `retired-id-in-use` | error | a retired ID still used by a document or by an unmarked requirement |
| `not-in-ledger`, `allocated-not-found` | warning | ledger and disk disagree |
| `broken-link` | error | relative Markdown link target does not exist (documents, and hand-written text of maps) |
| `unknown-requirement`, `covers-unknown` | error | referenced / covered requirement ID does not exist |
| `retired-reference` | error | reference or `covers` points at a retired ID (message names the replacement when recorded) |
| `covers-source-not-linked` | error | a Story covers a requirement whose document is not linked under `Derived From` |
| `implementation-record-missing` | error | Story is `Implemented`/`Verified` but has no `### IR-n` entry under `## Implementation Record` |
| `implementation-record-invalid` | error | malformed IR heading/date, duplicate ID, missing `Summary` or `Files changed` |
| `verification-bad-heading`, `verification-missing-field`, `verification-bad-value`, `verification-inconsistent`, `verification-bad-criteria`, `verification-unknown-story` | error | malformed `### VR-n` run in a TEST document (missing fields; `Result` not `passed/failed/blocked/not-run`; `Kind` not `automated/manual`; non-integer or contradictory exit code; `AC-n` out of range; unknown Story) |
| `verified-no-criteria`, `verified-criteria-unproven` | error | a `Verified` Story has no numbered acceptance criteria, or some criterion lacks a current (non-superseded, latest) `passed` run |
| `verified-with-unresolved-tbd` | warning | a `Verified` Story still lists `### Unresolved Acceptance Behavior (TBD)` bullets |
| `ready-without-criteria` | warning | `Ready`, `In Progress` or `Implemented` Story with no numbered acceptance criteria |
| `publication-invalid` | error | malformed `### PUB-n` entry in a Story's `## Publication` section (heading, duplicate ID, `Provider` not `github`, `Repository` not `owner/name`, `Issue` not `#N`) |
| `story-no-coverage` | notice | Story with `covers: []` |
| `requirement-uncovered` | notice | PR requirement that no Story covers (R1 restricts this notice to `PR-` requirements; BR requirements are covered through PRDs) |

The R2 rows above enforce the evidence formats in `technical-conventions.md` §5 and never change exit-code semantics (errors ⇒ `1`). `Artifacts/tests/evidence/` is ignored by the directory scan (verification logs, not documents).

The R3 row `publication-invalid` enforces the Publication record format in `publishing-conventions.md` §6. Credential-looking keys under `publishing` in `.sdlc/config.md` are a `bad-config` error.

Result: `{"summary": {"error","warning","notice"}, "documents"}`. `.sdlc/` is exempt from map and authored-document rules. Coverage notices never affect the exit code.

### `status`
Read-only progress snapshot built from the same scanners as `list`/`references`/`validate`. Writes nothing and contacts nothing. Exits `0` whenever the report is produced (an unhealthy project is reported in `result.health`, not through the exit code); `2` if no project is found. The human form is the report layout (health, inventory, delivery, traceability, needs attention).
Result: `{"health": {"ok","summary","documents","errors","warnings","stale_maps","broken_references"}, "inventory": {<BR|PR|US|DES|PLAN|RES|TEST>: {"total","by_status":{Draft,In Review,Approved,Superseded},"invalid"}}, "delivery": {<Not Started|Ready|In Progress|Implemented|Verified>: [{"id","title","status","path"}]}, "traceability": {"uncovered_requirements","standalone_stories","invalid_references","unresolved_tbd"}, "attention": [{"kind","id","message","path"}], "empty"}`. `attention.kind` is one of `validation-error`, `verification-problem`, `unresolved-acceptance`, `awaiting-verification`, `in-progress`, `ready-to-implement`, `in-review`, in that priority order. Coverage notices (uncovered PR requirements, standalone Stories) stay informational and never produce attention items; absent DES/PLAN/RES/TEST documents are not defects.

### `publish-preview STORY-ID [STORY-ID ...]`
**Offline and read-only** (zero external calls, zero writes). Renders the exact GitHub Issue for each named Story and a `digest` over it. Nothing is selected by default: no IDs is a usage error (`no-selection`, exit `2`); a non-Story ID is `bad-selection` (`2`). Requires `.sdlc/config.md` `publishing: {provider: github, repository: owner/name}`; otherwise `publishing-config-missing`, `publishing-unsupported-provider` or `publishing-config-invalid` (exit `1`, nothing else done). Exit `1` also when any selected Story is `blocked`: it does not exist (`story-not-found`), has validation errors of its own (`story-invalid`), or its Publication record is unreadable. Warnings never block: `story-not-approved`, `unresolved-acceptance`, `no-acceptance-criteria`, `relative-links`; notices: `story-no-coverage` (a standalone Story is publishable), `already-published`. A project-wide `project-has-errors` warning is given when unrelated validation errors exist.
Result: `{"provider","repository","stories": [{"id","path","title","issue_title","issue_body","labels": [],"known_publication"|null,"action": "create"|"skip"|"blocked","blockers","warnings"}], "will_create","blocked","can_apply","digest","mutations": 0,"access_checked": false}`. `digest` is `sha256:` over the canonical JSON of provider, repository and, per Story sorted by ID, `{id, action, title, body, known}`; it is independent of selection order and changes with any change to Story content, selection, repository or publication state. Issue format: `publishing-conventions.md` §4.

### `publish-apply STORY-ID [STORY-ID ...] --confirm-digest DIGEST`
The only command that contacts an external service and the only one that may create Issues. Recomputes the preview from the **current** files and proceeds only when `DIGEST` equals its digest. Otherwise it creates nothing: `confirmation-missing` (no digest) or `preview-stale` (mismatch), exit `1`; the refusal result never contains the current digest or Issue bodies. If any Story is `blocked`, nothing is published. Before creating anything it runs a read-only preflight through the provider (`gh auth status`, `gh repo view`): `provider-unavailable`, `provider-auth`, `repository-not-found`, `issues-disabled` or `provider-failed` abort with no mutation. It then creates one Issue per `create` Story with exactly the previewed title and body (no labels, assignees, milestones or projects) and, **only after the provider reports success**, appends the Publication record to that Story. Stories with a known publication **in the configured repository** (identity = Story + provider + repository) are `skipped`, never recreated; a publication in another repository does not block (preview notice `published-elsewhere`).
Per-Story `outcome`: `published` (`issue`, `url`, `record`), `skipped`, `failed` (provider error; nothing recorded; other Stories are still attempted), `unconfirmed` (provider exited 0 without an Issue URL; code `provider-ambiguous`; later Stories `not-attempted`), `published-unrecorded` (Issue created but the local record could not be written; error `record-failed` flagged `INCONSISTENCY`; later Stories `not-attempted`; never retried), `not-attempted`. Exit `0` only if every created/skipped outcome succeeded; `1` otherwise.
Result: the preview fields plus `"mutations"` (Issues actually created), `"published"`, `"outcomes"`.
Provider boundary: `sdlc/github_provider.py` shells out to `gh` (`SDLC_GH_COMMAND` overrides the executable; tests use a stub). Authentication is whatever `gh` already has (`gh auth login`, `GH_TOKEN`, `GITHUB_TOKEN`); the CLI never reads, stores or prints a credential, and scrubs token-shaped strings from provider output.

## Configuration schema (`.sdlc/config.md`)

YAML front matter only: `project_name` (non-empty string), `schema_version` (`1`), `directories` (mapping of exactly `BR`, `PR`, `Stories`, `Artifacts` to distinct single-segment folder names; default: each maps to itself), optional `publishing` (mapping). R3 reads exactly `provider: github` and `repository: owner/name` from it; any key that looks like a credential (`token`, `secret`, `password`, `auth`, `api_key`, …) is a `bad-config` error.
