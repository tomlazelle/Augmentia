"""`publish-preview` / `publish-apply`: GitHub Issues publication with a mandatory preview-and-confirm gate (R3).

* `build_preview` is **offline and read-only**: it renders exactly what would be published and returns a
  `digest` over that content. It never contacts a provider and never writes.
* `apply_publication` mutates only when the supplied digest equals the digest of a fresh preview of the
  *current* files (so changed Story content, selection, repository or known-publication state invalidates a
  confirmation), then publishes exactly the previewed content through the provider boundary.
* Local Markdown stays authoritative: publishing appends a non-material `## Publication` record to the Story
  and changes nothing else (no requirements, `status`, `delivery_status`, maps or ledger).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import frontmatter, publication, technical, validate as validate_mod
from .github_provider import AmbiguousResult, GitHubCli, ProviderError, redact
from .markdown import REF_SECTIONS
from .model import FILENAME_RE, Diagnostic, Outcome, id_sort_key, id_kind, category_of, today
from .project import Doc, Project, scan_documents

EXCLUDED_SECTIONS = ("references", "implementation record", "review record", "publication")
ALLOWED_KEYS = {"provider", "repository"}


# --- configuration ------------------------------------------------------------------------------

def load_publishing(project: Project) -> tuple[dict | None, list[Diagnostic]]:
    rel = ".sdlc/config.md"
    cfg = (project.config or {}).get("publishing")
    if not cfg:
        return None, [Diagnostic("error", "publishing-config-missing",
                                 "no publishing configuration: add 'publishing: {provider: github, repository: owner/name}' "
                                 "to .sdlc/config.md (never put credentials there)", path=rel)]
    diags: list[Diagnostic] = []
    provider = cfg.get("provider")
    repository = cfg.get("repository")
    if provider != "github":
        diags.append(Diagnostic("error", "publishing-unsupported-provider",
                                f"publishing.provider must be 'github' (got {provider!r}); other providers are not supported", path=rel))
    if not isinstance(repository, str) or not publication.REPO_RE.match(repository):
        diags.append(Diagnostic("error", "publishing-config-invalid",
                                f"publishing.repository must be 'owner/name' (got {repository!r})", path=rel))
    unknown = sorted(set(cfg) - ALLOWED_KEYS)
    if unknown:
        diags.append(Diagnostic("warning", "unknown-publishing-key", f"ignored publishing keys: {', '.join(unknown)}", path=rel))
    if any(d.severity == "error" for d in diags):
        return None, diags
    return {"provider": provider, "repository": repository}, diags


# --- Issue rendering ----------------------------------------------------------------------------

def _ref_label(href: str) -> str:
    name = Path(href).name
    m = FILENAME_RE.match(name)
    return m.group(1) if m else name


def render_issue(doc: Doc) -> tuple[str, str]:
    """(title, body) for a Story. The body is the Story's own text, verbatim, minus the sections that are local
    or operational (References, Implementation/Review/Publication records) and the H1; TBDs are never dropped."""
    text = doc.text.replace("\r\n", "\n")
    lines = text.split("\n")
    _, body_start = frontmatter.split(text)
    drop = set(range(0, body_start))
    for sec in technical.sections(text):
        if sec.level == 2 and sec.title.lower() in EXCLUDED_SECTIONS:
            drop.update(range(sec.line - 1, sec.end))
        elif sec.level == 1:
            drop.add(sec.line - 1)
    kept = "\n".join(ln for i, ln in enumerate(lines) if i not in drop).strip("\n")
    kept = re.sub(r"\n{3,}", "\n\n", kept)

    head = [f"> Published from local Story **{doc.id}**. The local Markdown file (`{doc.rel}`) is authoritative; "
            "edits to this Issue are not imported back.", ""]
    head.append(f"**Purpose:** {doc.meta.get('purpose')}")
    covers = ", ".join(f"`{c}`" for c in doc.covers) if doc.covers else "none — standalone Story"
    head.append(f"**Covers:** {covers}")
    for section in REF_SECTIONS:
        labels = sorted({_ref_label(r.href) for r in doc.parsed.refs if r.section == section and r.href}, key=id_sort_key)
        if labels:
            head.append(f"**{section}:** {', '.join(labels)}")
    return f"[{doc.id}] {doc.title}", "\n".join(head) + ("\n\n" + kept if kept else "") + "\n"


def _warnings_for(doc: Doc, secs: list[technical.Section]) -> list[Diagnostic]:
    out: list[Diagnostic] = []

    def warn(sev: str, code: str, msg: str) -> None:
        out.append(Diagnostic(sev, code, msg, path=doc.rel, id=doc.id))

    status = doc.meta.get("status")
    if status != "Approved":
        warn("warning", "story-not-approved", f"document status is {status}, not Approved; the Issue will show the current text")
    tbd = technical.unresolved_tbd_bullets(secs)
    if tbd:
        warn("warning", "unresolved-acceptance", f"{tbd} unresolved acceptance behavior (TBD) item(s); they are included in the Issue as written")
    if technical.acceptance_criteria_count(secs) == 0:
        warn("warning", "no-acceptance-criteria", "the Story has no numbered acceptance criteria")
    excluded_lines: set[int] = set()
    for sec in secs:
        if sec.level == 2 and sec.title.lower() in EXCLUDED_SECTIONS:
            excluded_lines.update(range(sec.line, sec.end + 1))
    relative = sorted({href for line, href in doc.parsed.links if line not in excluded_lines})
    if relative:
        warn("warning", "relative-links", f"body contains relative link(s) that will not resolve on GitHub: {', '.join(relative[:5])}")
    if not doc.covers:
        warn("notice", "story-no-coverage", "standalone Story: covers is empty (publishable)")
    return out


# --- preview ------------------------------------------------------------------------------------

def _digest(provider: str, repository: str, stories: list[dict]) -> str:
    payload = {"provider": provider, "repository": repository,
               "stories": [{"id": s["id"], "action": s["action"], "title": s["issue_title"], "body": s["issue_body"],
                            "known": s["known_publication"]} for s in stories]}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalise_selection(raw: list[str]) -> tuple[list[str], list[Diagnostic]]:
    diags: list[Diagnostic] = []
    out: list[str] = []
    for item in raw:
        if id_kind(item) != "document" or category_of(item) != "US":
            diags.append(Diagnostic("error", "bad-selection", f"{item!r} is not a Story ID (expected e.g. US-001)", id=item))
        elif item not in out:
            out.append(item)
    if not raw:
        diags.append(Diagnostic("error", "no-selection", "name the Stories to publish; nothing is published by default"))
    return sorted(out, key=id_sort_key), diags


def build_preview(project: Project, selection: list[str]) -> Outcome:
    ids, diags = _normalise_selection(selection)
    config, cfg_diags = load_publishing(project)
    diags += cfg_diags
    if config is None or any(d.severity == "error" for d in diags):
        return Outcome(2 if any(d.code in ("bad-selection", "no-selection") for d in diags) else 1, {}, diags)

    docs, scan_diags = scan_documents(project)
    by_id: dict[str, list[Doc]] = {}
    for d in docs:
        by_id.setdefault(d.id, []).append(d)
    project_diags = validate_mod.validate(project).diagnostics
    other_errors = [d for d in project_diags if d.severity == "error"]

    stories: list[dict] = []
    for sid in ids:
        matches = [d for d in by_id.get(sid, []) if d.is_story]
        item: dict = {"id": sid, "path": None, "title": None, "issue_title": None, "issue_body": None, "labels": [],
                      "known_publication": None, "other_publications": [], "action": "blocked", "blockers": [], "warnings": []}
        stories.append(item)
        if not matches:
            diags.append(Diagnostic("error", "story-not-found", f"no Story {sid} exists", id=sid))
            item["blockers"].append("story-not-found")
            continue
        doc = matches[0]
        item.update(path=doc.rel, title=doc.title)
        mine = [d for d in project_diags if d.severity == "error" and d.path == doc.rel]
        if len(matches) > 1:
            mine.append(Diagnostic("error", "duplicate-id", f"{sid} is used by more than one document", path=doc.rel, id=sid))
        if mine:
            for d in mine:
                diags.append(Diagnostic("error", "story-invalid", f"{d.message} ({d.code})", path=doc.rel, id=sid, line=d.line))
                item["blockers"].append(d.code)
            continue
        secs = technical.sections(doc.text)
        pubs, pub_diags = publication.parse(doc.rel, sid, secs)
        if pub_diags:  # an unreadable record could hide a prior publication: block rather than risk a duplicate
            diags += [Diagnostic("error", "story-invalid", d.message, path=doc.rel, id=sid, line=d.line) for d in pub_diags]
            item["blockers"].append("publication-invalid")
            continue
        title, body = render_issue(doc)
        item.update(issue_title=title, issue_body=body)
        for w in _warnings_for(doc, secs):
            diags.append(w)
            item["warnings"].append(w.code)
        same = [p for p in pubs if (p.provider, p.repository) == (config["provider"], config["repository"])]
        elsewhere = [p for p in pubs if p not in same]
        item["other_publications"] = [p.to_dict() for p in elsewhere]
        for p in elsewhere:
            diags.append(Diagnostic("notice", "published-elsewhere",
                                    f"also published to {p.provider}:{p.repository}{p.issue}; that does not affect publication "
                                    f"to {config['repository']}", path=doc.rel, id=sid))
        pubs = same
        if pubs:
            item["known_publication"] = pubs[-1].to_dict()
            item["action"] = "skip"
            diags.append(Diagnostic("notice", "already-published",
                                    f"already published as {pubs[-1].repository}{pubs[-1].issue}; nothing will be created "
                                    "(M5 does not update existing Issues)", path=doc.rel, id=sid))
        else:
            item["action"] = "create"

    blocked = [s["id"] for s in stories if s["action"] == "blocked"]
    creating = [s["id"] for s in stories if s["action"] == "create"]
    if other_errors and not blocked:
        unrelated = [d for d in other_errors if d.path not in {s["path"] for s in stories}]
        if unrelated:
            diags.append(Diagnostic("warning", "project-has-errors",
                                    f"the project has {len(unrelated)} other validation error(s) unrelated to the selected "
                                    "Stories; run validate", path=None))
    result = {
        "provider": config["provider"], "repository": config["repository"], "stories": stories,
        "will_create": creating, "blocked": blocked,
        "can_apply": bool(creating) and not blocked,
        "digest": _digest(config["provider"], config["repository"], stories),
        "mutations": 0,
        "access_checked": False,
    }
    return Outcome(1 if blocked else 0, result, sorted(diags, key=lambda d: ({"error": 0, "warning": 1, "notice": 2}[d.severity], d.id or "", d.code)))


# --- apply --------------------------------------------------------------------------------------

def default_provider() -> GitHubCli:
    return GitHubCli()


def _refusal(preview: dict) -> dict:
    """Result of an apply that made no mutation. Deliberately omits the digest and Issue bodies."""
    return {"provider": preview["provider"], "repository": preview["repository"], "stories": [],
            "will_create": [], "blocked": preview["blocked"], "can_apply": False, "mutations": 0,
            "outcomes": [], "published": 0, "access_checked": False}


def apply_publication(project: Project, selection: list[str], confirm_digest: str | None, provider=None) -> Outcome:
    """Publish the previewed set iff `confirm_digest` matches a fresh preview of the current files."""
    preview = build_preview(project, selection)
    if not preview.result:
        return preview
    if not confirm_digest or confirm_digest != preview.result["digest"]:
        if confirm_digest:
            code, msg = "preview-stale", ("the confirmed digest does not match the current proposed publication (Story content, "
                                          "selection, configuration or publication state changed); nothing was published — run "
                                          "publish-preview, show it to the human, and ask again")
        else:
            code, msg = "confirmation-missing", ("no confirmed digest supplied; nothing was published — run publish-preview "
                                                 "and obtain explicit human confirmation")
        diags = [d for d in preview.diagnostics if d.severity == "error"] + [Diagnostic("error", code, msg)]
        return Outcome(1, _refusal(preview.result), diags)  # no digest echoed: the human must see a new preview first
    if preview.result["blocked"]:
        return Outcome(1, _refusal(preview.result), preview.diagnostics)

    provider = provider or default_provider()
    repository = preview.result["repository"]
    diags = list(preview.diagnostics)
    outcomes: list[dict] = []
    todo = [s for s in preview.result["stories"] if s["action"] == "create"]

    if todo:
        try:
            provider.check_access(repository)
        except ProviderError as exc:
            diags.append(Diagnostic("error", exc.code, str(exc)))
            return Outcome(1, _refusal(preview.result), diags)

    mutations = 0
    stop = False
    for story in preview.result["stories"]:
        sid = story["id"]
        if story["action"] == "skip":
            outcomes.append({"id": sid, "outcome": "skipped", "reason": "already published",
                             "publication": story["known_publication"]})
            continue
        if stop:
            outcomes.append({"id": sid, "outcome": "not-attempted", "reason": "stopped after an earlier inconsistency"})
            continue
        try:
            ref = provider.create_issue(repository, story["issue_title"], story["issue_body"])
        except AmbiguousResult as exc:
            diags.append(Diagnostic("error", exc.code, f"{sid}: {exc}", path=story["path"], id=sid))
            outcomes.append({"id": sid, "outcome": "unconfirmed", "error": str(exc)})
            stop = True  # an Issue may exist: do not create more or retry blindly
            continue
        except ProviderError as exc:
            diags.append(Diagnostic("error", exc.code, f"{sid}: {exc}", path=story["path"], id=sid))
            outcomes.append({"id": sid, "outcome": "failed", "error": str(exc)})
            continue
        except Exception as exc:  # defensive: an unexpected provider failure must never read as success
            diags.append(Diagnostic("error", "provider-failed", f"{sid}: {redact(str(exc))}", path=story["path"], id=sid))
            outcomes.append({"id": sid, "outcome": "failed", "error": redact(str(exc))})
            continue
        mutations += 1
        try:
            pub_id = publication.append_record(project.root / story["path"], today(), "github", repository, ref.number, ref.url)
        except Exception as exc:
            where = ref.url or f"{repository}#{ref.number}"
            diags.append(Diagnostic(
                "error", "record-failed",
                f"INCONSISTENCY: {sid} WAS published as {where} but recording it in {story['path']} failed ({exc}); "
                "do not publish this Story again — add the PUB record by hand (see publishing-conventions.md) so a "
                "duplicate is not created", path=story["path"], id=sid))
            outcomes.append({"id": sid, "outcome": "published-unrecorded", "issue": f"#{ref.number}", "url": ref.url,
                             "error": str(exc)})
            stop = True
            continue
        outcomes.append({"id": sid, "outcome": "published", "issue": f"#{ref.number}", "url": ref.url, "record": pub_id})

    published = sum(o["outcome"] in ("published", "published-unrecorded") for o in outcomes)
    failed = any(o["outcome"] in ("failed", "unconfirmed", "published-unrecorded", "not-attempted") for o in outcomes)
    result = dict(preview.result, mutations=mutations, outcomes=outcomes, published=published)
    return Outcome(1 if failed else 0, result, diags)
