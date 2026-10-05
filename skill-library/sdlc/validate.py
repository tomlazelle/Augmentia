"""`validate`: structural errors, warnings, and coverage notices."""

from __future__ import annotations

from collections import defaultdict

from .ledger import LEDGER_REL, Ledger
from .maps import check_maps, specs
from . import technical
from .markdown import extract_hrefs, mask_region
from .model import GEN_END, GEN_START, TOP_DIRS, Diagnostic, Outcome, id_sort_key, owner_of
from .project import Doc, Project, load_config, scan_documents


def _dup_diags(groups: dict[str, list[Doc]], code: str, what: str) -> list[Diagnostic]:
    out = []
    for ident, group in groups.items():
        paths = sorted({d.rel for d in group})
        if len(paths) < 2 and len(group) < 2:
            continue
        for d in group:
            others = [p for p in paths if p != d.rel] or ["(declared more than once in this file)"]
            out.append(Diagnostic("error", code, f"{what} {ident} is also used by: {', '.join(others)}",
                                  path=d.rel, id=ident))
    return out


def _check_links(project: Project, docs: list[Doc]) -> list[Diagnostic]:
    diags = []
    for doc in docs:
        for lineno, href in doc.parsed.links:
            if not (doc.path.parent / href).exists():
                diags.append(Diagnostic("error", "broken-link", f"link target does not exist: {href}",
                                        path=doc.rel, id=doc.id, line=lineno))
    for spec in specs(project):
        if not spec.path.is_file():
            continue
        text = mask_region(spec.path.read_text(encoding="utf-8"), GEN_START, GEN_END)
        for lineno, line in enumerate(text.split("\n"), 1):
            for href in extract_hrefs(line):
                if not (spec.path.parent / href).exists():
                    diags.append(Diagnostic("error", "broken-link", f"link target does not exist: {href}",
                                            path=project.rel(spec.path), line=lineno))
    return diags


def validate(project: Project) -> Outcome:
    diags: list[Diagnostic] = []
    root = project.root

    _, cfg_diags = load_config(root)
    diags += cfg_diags
    ledger, ledger_diags = Ledger.load(root / LEDGER_REL)
    diags += ledger_diags

    for key in TOP_DIRS:
        directory = project.top(key)
        if not directory.is_dir():
            diags.append(Diagnostic("error", "missing-directory", "required directory is missing", path=project.rel(directory)))
    if not (root / "map.md").is_file():
        diags.append(Diagnostic("error", "missing-map", "root map.md is missing", path="map.md"))
    artifacts = project.top("Artifacts")
    if artifacts.is_dir():
        for spec in specs(project):
            if spec.kind == "sub" and not spec.path.is_file():
                diags.append(Diagnostic("error", "missing-map", "directory has no map.md", path=project.rel(spec.path)))
    # (`.sdlc/` is deliberately exempt from map and authored-document rules.)

    docs, scan_diags = scan_documents(project)
    diags += scan_diags
    for doc in docs:
        diags += doc.diags

    by_name: dict[str, list[Doc]] = defaultdict(list)
    by_meta: dict[str, list[Doc]] = defaultdict(list)
    for doc in docs:
        if doc.name_id:
            by_name[doc.name_id].append(doc)
        if isinstance(doc.meta.get("id"), str):
            by_meta[doc.meta["id"]].append(doc)
    dup_docs = {i: g for i, g in by_name.items() if len(g) > 1}
    for i, g in by_meta.items():
        if len(g) > 1 and i not in dup_docs:
            dup_docs[i] = g
    diags += _dup_diags(dup_docs, "duplicate-id", "document ID")

    req_decls: dict[str, list[Doc]] = defaultdict(list)
    for doc in docs:
        for req in doc.parsed.requirements:
            req_decls[req.id].append(doc)
    diags += _dup_diags({i: g for i, g in req_decls.items() if len(g) > 1}, "duplicate-requirement", "requirement ID")

    # Ledger vs disk
    ledger_ok = not any(d.severity == "error" for d in ledger_diags)
    doc_ids_on_disk = set(by_name) | set(by_meta)
    retired = {i for i, e in ledger.entries.items() if e.state == "Retired"}
    if ledger_ok:
        for ident in sorted(doc_ids_on_disk & retired, key=id_sort_key):
            for d in by_name.get(ident) or by_meta.get(ident, []):
                diags.append(Diagnostic("error", "retired-id-in-use",
                                        f"{ident} is retired in the ledger but a document still uses it", path=d.rel, id=ident))
        for ident in sorted(set(req_decls) & retired, key=id_sort_key):
            for d in req_decls[ident]:
                line = next(r for r in d.parsed.requirements if r.id == ident)
                if "retired" not in line.text.lower():
                    diags.append(Diagnostic(
                        "error", "retired-id-in-use",
                        f"{ident} is retired in the ledger; mark its text *Retired* or remove it",
                        path=d.rel, id=ident, line=line.line))
        for ident in sorted(doc_ids_on_disk | set(req_decls), key=id_sort_key):
            if ident not in ledger.entries:
                paths = by_name.get(ident) or by_meta.get(ident) or req_decls.get(ident, [])
                diags.append(Diagnostic("warning", "not-in-ledger", "ID is not recorded in the ledger",
                                        path=paths[0].rel if paths else None, id=ident))
        for ident, entry in sorted(ledger.entries.items(), key=lambda kv: id_sort_key(kv[0])):
            if entry.state == "Allocated" and ident not in doc_ids_on_disk and ident not in req_decls:
                diags.append(Diagnostic("warning", "allocated-not-found",
                                        "allocated in the ledger but nothing on disk uses it; retire it if it was deleted",
                                        path=LEDGER_REL, id=ident))

    # Links, references and traceability
    diags += _check_links(project, docs)
    known_reqs = set(req_decls)
    by_path = {d.path.resolve(): d for d in docs}
    for doc in docs:
        for ref in doc.parsed.refs:
            for rid in ref.req_ids:
                if rid in retired:
                    diags.append(_retired_ref(ledger, rid, doc, ref.line))
                elif rid not in known_reqs:
                    diags.append(Diagnostic("error", "unknown-requirement", f"referenced requirement {rid} does not exist",
                                            path=doc.rel, id=rid, line=ref.line))
        if doc.is_story:
            linked = {by_path[t].id for r in doc.parsed.refs if r.section == "Derived From" and r.href
                      if (t := (doc.path.parent / r.href).resolve()) in by_path}
            for rid in doc.covers:
                if rid in retired:
                    diags.append(_retired_ref(ledger, rid, doc, None))
                elif rid not in known_reqs:
                    diags.append(Diagnostic("error", "covers-unknown", f"covers {rid}, which does not exist",
                                            path=doc.rel, id=rid))
                elif owner_of(rid) not in linked:
                    diags.append(Diagnostic(
                        "error", "covers-source-not-linked",
                        f"covers {rid} but does not link {owner_of(rid)} under 'Derived From'", path=doc.rel, id=rid))

    diags += _check_technical(docs)

    diags += check_maps(project, docs)

    # Coverage notices (informational)
    stories = [d for d in docs if d.is_story and d.valid]
    covered = {rid for s in stories for rid in s.covers}
    for s in sorted(stories, key=lambda d: id_sort_key(d.id)):
        if not s.covers:
            diags.append(Diagnostic("notice", "story-no-coverage", "standalone Story: covers is empty",
                                    path=s.rel, id=s.id))
    # R1: only PR requirements are expected to be covered by Stories (BR requirements are covered via PRDs).
    for rid in sorted(known_reqs - retired, key=id_sort_key):
        if owner_of(rid).startswith("PR-") and rid not in covered:
            diags.append(Diagnostic("notice", "requirement-uncovered", "no Story covers this requirement",
                                    path=req_decls[rid][0].rel, id=rid))

    rank = {"error": 0, "warning": 1, "notice": 2}
    diags.sort(key=lambda d: (rank[d.severity], d.path or "", d.line or 0, d.code, d.id or ""))
    counts = {s: sum(d.severity == s for d in diags) for s in ("error", "warning", "notice")}
    return Outcome(1 if counts["error"] else 0, {"summary": counts, "documents": len(docs)}, diags)


def _retired_ref(ledger: Ledger, rid: str, doc: Doc, line: int | None) -> Diagnostic:
    repl = ledger.entries[rid].replaced_by
    hint = f"; replaced by {repl}" if repl else ""
    return Diagnostic("error", "retired-reference", f"references retired requirement {rid}{hint}",
                      path=doc.rel, id=rid, line=line)


def _check_technical(docs: list[Doc]) -> list[Diagnostic]:
    """R2 evidence rules: Story Implementation Records, TEST Verification Runs, and what `Verified` requires."""
    diags: list[Diagnostic] = []
    stories = {d.id: d for d in docs if d.is_story}
    secs = {d.id: technical.sections(d.text) for d in stories.values()}
    ac_count = {sid: technical.acceptance_criteria_count(s) for sid, s in secs.items()}

    runs: list[tuple[technical.Record, str]] = []
    for doc in docs:
        if doc.category == "TEST" and doc.valid:
            recs, d = technical.check_verification_runs(doc.rel, doc.id, technical.sections(doc.text), ac_count)
            diags += d
            runs += [(r, doc.rel) for r in recs]

    for sid, doc in stories.items():
        if not doc.valid:
            continue
        status = doc.meta.get("delivery_status")
        recs, d = technical.check_implementation_records(doc.rel, sid, secs[sid])
        diags += d
        n = ac_count[sid]
        if status in ("Implemented", "Verified") and not recs:
            diags.append(Diagnostic("error", "implementation-record-missing",
                                    f"delivery_status {status} requires an '## Implementation Record' entry (### IR-n — date)",
                                    path=doc.rel, id=sid))
        if status in ("Ready", "In Progress", "Implemented") and n == 0:
            diags.append(Diagnostic("warning", "ready-without-criteria",
                                    f"delivery_status {status} but the Story has no numbered acceptance criteria", path=doc.rel, id=sid))
        if status != "Verified":
            continue
        if n == 0:
            diags.append(Diagnostic("error", "verified-no-criteria", "Verified Story has no numbered acceptance criteria to verify",
                                    path=doc.rel, id=sid))
            continue
        mine = sorted(((r, rel) for r, rel in runs if r.fields.get("story", "").strip() == sid and not technical.is_superseded(r)),
                      key=lambda item: (item[0].stamp, item[1], item[0].order))
        problems = []
        for ac in range(1, n + 1):
            latest = next(((r, rel) for r, rel in reversed(mine) if ac in technical.criteria_of(r)), None)
            if latest is None:
                problems.append(f"AC-{ac} (no current run)")
            elif latest[0].fields.get("result", "").strip() != "passed":
                problems.append(f"AC-{ac} (latest run {latest[0].id} in {latest[1]} is {latest[0].fields.get('result', '?').strip()})")
        if problems:
            diags.append(Diagnostic("error", "verified-criteria-unproven",
                                    "delivery_status Verified requires a current, passed verification run for every acceptance "
                                    "criterion; missing: " + "; ".join(problems), path=doc.rel, id=sid))
        if technical.unresolved_tbd_bullets(secs[sid]):
            diags.append(Diagnostic("warning", "verified-with-unresolved-tbd",
                                    "Verified Story still lists unresolved acceptance behavior (TBD); Verified covers only the "
                                    "decided criteria", path=doc.rel, id=sid))
    return diags
