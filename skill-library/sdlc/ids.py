"""ID allocation and retirement against the ledger and on-disk documents."""

from __future__ import annotations

import re

from .ledger import LEDGER_REL, Ledger
from .model import (
    DOC_ID_RE,
    Diagnostic,
    Outcome,
    category_of,
    format_doc_id,
    id_kind,
    slugify,
    today,
)
from .project import Project, scan_documents


def _load_ledger(project: Project) -> tuple[Ledger | None, list[Diagnostic]]:
    ledger, diags = Ledger.load(project.root / LEDGER_REL)
    return (None if any(d.severity == "error" for d in diags) else ledger), diags


def _disk_doc_ids(project: Project) -> set[str]:
    docs, _ = scan_documents(project)
    ids = set()
    for doc in docs:
        if doc.name_id:
            ids.add(doc.name_id)
        meta_id = doc.meta.get("id")
        if isinstance(meta_id, str) and DOC_ID_RE.match(meta_id):
            ids.add(meta_id)
    return ids


def allocate_document(project: Project, category: str, title: str | None) -> Outcome:
    ledger, diags = _load_ledger(project)
    if ledger is None:
        return Outcome(1, diagnostics=diags)
    slug = None
    if title is not None:
        slug = slugify(title)
        if not slug:
            return Outcome(2, diagnostics=[Diagnostic("error", "bad-title", "title has no usable letters or digits")])
    numbers = [int(i.split("-")[1]) for i in [*ledger.entries, *_disk_doc_ids(project)]
               if DOC_ID_RE.match(i) and category_of(i) == category]
    new_id = format_doc_id(category, max(numbers, default=0) + 1)
    ledger.add(new_id, today())
    ledger.save()
    path = None
    if slug:
        path = project.rel(project.category_dir(category) / f"{new_id}-{slug}.md")
    return Outcome(0, {"id": new_id, "kind": "document", "category": category,
                       "directory": project.rel(project.category_dir(category)), "path": path}, diags)


def allocate_requirement(project: Project, doc_id: str) -> Outcome:
    if not DOC_ID_RE.match(doc_id):
        return Outcome(2, diagnostics=[Diagnostic("error", "bad-id", f"{doc_id!r} is not a valid document ID")])
    ledger, diags = _load_ledger(project)
    if ledger is None:
        return Outcome(1, diagnostics=diags)
    entry = ledger.entries.get(doc_id)
    docs, _ = scan_documents(project)
    doc_files = [d for d in docs if d.id == doc_id]
    if entry is not None and entry.state == "Retired":
        return Outcome(1, diagnostics=[Diagnostic("error", "retired-id", f"{doc_id} is retired", id=doc_id)])
    if entry is None and not doc_files:
        return Outcome(1, diagnostics=[Diagnostic("error", "unknown-id", f"{doc_id} is not in the ledger or on disk", id=doc_id)])
    pattern = re.compile(rf"^{re.escape(doc_id)}-R(\d+)$")
    numbers = [int(m.group(1)) for i in ledger.entries if (m := pattern.match(i))]
    numbers += [int(m.group(1)) for d in doc_files for r in d.parsed.requirements if (m := pattern.match(r.id))]
    new_id = f"{doc_id}-R{max(numbers, default=0) + 1:03d}"
    ledger.add(new_id, today())
    ledger.save()
    return Outcome(0, {"id": new_id, "kind": "requirement", "document": doc_id}, diags)


def retire(project: Project, target: str, replaced_by: str | None, note: str | None) -> Outcome:
    kind = id_kind(target)
    if kind is None:
        return Outcome(2, diagnostics=[Diagnostic("error", "bad-id", f"{target!r} is not a valid document or requirement ID")])
    if replaced_by is not None and id_kind(replaced_by) != kind:
        return Outcome(2, diagnostics=[Diagnostic(
            "error", "bad-replacement", f"--replaced-by must be a {kind} ID, got {replaced_by!r}")])
    if replaced_by == target:
        return Outcome(2, diagnostics=[Diagnostic("error", "bad-replacement", "an ID cannot replace itself", id=target)])
    ledger, diags = _load_ledger(project)
    if ledger is None:
        return Outcome(1, diagnostics=diags)
    docs, _ = scan_documents(project)
    on_disk = (target in _disk_doc_ids(project)) if kind == "document" else any(
        r.id == target for d in docs for r in d.parsed.requirements)
    existing = ledger.entries.get(target)
    if existing is None and not on_disk:
        return Outcome(1, diagnostics=[Diagnostic("error", "unknown-id", f"{target} is not in the ledger or on disk", id=target)])
    if existing is not None and existing.state == "Retired":
        return Outcome(1, diagnostics=[Diagnostic("error", "already-retired", f"{target} is already retired", id=target)])
    text = f"Replaced by {replaced_by}." if replaced_by else ""
    text = f"{text} {note}".strip() if note else text
    ledger.retire(target, today(), text)
    ledger.save()
    out_diags = list(diags)
    if kind == "document" and on_disk:
        out_diags.append(Diagnostic(
            "warning", "retired-still-present",
            f"{target} still has a document on disk; validate reports this until it is removed", id=target))
    return Outcome(0, {"id": target, "kind": kind, "state": "Retired", "replaced_by": replaced_by, "note": text}, out_diags)

