"""Read-only discovery: list, references, find-overlaps."""

from __future__ import annotations

import re

from .ledger import LEDGER_REL, Ledger
from .model import DOC_ID_RE, REQ_ID_RE, Diagnostic, Outcome, id_kind, id_sort_key, owner_of
from .project import Doc, Project, scan_documents

# --- find-overlaps scoring (documented in shared/cli-contract.md) -------------------------------
STOPWORDS = {"a", "an", "the", "of", "for", "and", "to", "in", "on", "with", "or"}
WEIGHTS = {"title": 0.5, "purpose": 0.3, "refs": 0.2}
LIKELY = 0.75
POSSIBLE = 0.40


def tokens(text: str) -> set[str]:
    out = set()
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOPWORDS:
            continue
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        out.add(word)
    return out


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def _doc_row(doc: Doc) -> dict:
    row = {"id": doc.id, "title": doc.title, "category": doc.category, "status": doc.meta.get("status"),
           "path": doc.rel, "purpose": doc.meta.get("purpose")}
    if doc.is_story:
        row["delivery_status"] = doc.meta.get("delivery_status")
    return row


def list_documents(project: Project, category: str | None, status: str | None) -> Outcome:
    docs, diags = scan_documents(project)
    rows = []
    for doc in sorted(docs, key=lambda d: id_sort_key(d.id)):
        if not doc.valid:
            diags.append(Diagnostic("warning", "skipped-invalid", "document has metadata errors and is not listed; run validate",
                                    path=doc.rel, id=doc.id))
            continue
        if category and doc.category != category:
            continue
        if status and doc.meta.get("status") != status:
            continue
        rows.append(_doc_row(doc))
    return Outcome(0, {"count": len(rows), "documents": rows}, diags)


def _requirement_index(docs: list[Doc]) -> dict[str, Doc]:
    return {r.id: d for d in docs for r in d.parsed.requirements}


def references(project: Project, target: str) -> Outcome:
    kind = id_kind(target)
    if kind is None:
        return Outcome(2, diagnostics=[Diagnostic("error", "bad-id", f"{target!r} is not a valid document or requirement ID")])
    docs, diags = scan_documents(project)
    ledger, _ = Ledger.load(project.root / LEDGER_REL)
    reqs = _requirement_index(docs)
    by_id = {d.id: d for d in docs}
    by_path = {d.path.resolve(): d for d in docs}
    entry = ledger.entries.get(target)
    doc = by_id.get(target) if kind == "document" else None
    defined_in = reqs.get(target) if kind == "requirement" else None
    if doc is None and defined_in is None and entry is None:
        return Outcome(1, diagnostics=[Diagnostic("error", "unknown-id", f"{target} not found", id=target)])

    result: dict = {"id": target, "kind": kind, "state": entry.state if entry else "Present"}
    outgoing: list[dict] = []
    incoming: list[dict] = []

    def own_reqs(d: Doc) -> set[str]:
        return {r.id for r in d.parsed.requirements}

    if doc is not None:
        result.update(title=doc.title, path=doc.rel)
        for ref in doc.parsed.refs:
            item = {"relationship": ref.section, "requirements": ref.req_ids, "href": ref.href, "target": None}
            if ref.href:
                other = by_path.get((doc.path.parent / ref.href).resolve())
                item["target"] = {"id": other.id, "path": other.rel} if other else {"id": None, "path": ref.href}
            outgoing.append(item)
        if doc.covers:
            outgoing.append({"relationship": "Covers", "requirements": doc.covers, "href": None, "target": None})
        mine = own_reqs(doc)
        for other in docs:
            if other is doc:
                continue
            for ref in other.parsed.refs:
                linked = ref.href and (other.path.parent / ref.href).resolve() == doc.path.resolve()
                shared = sorted(mine & set(ref.req_ids))
                if linked or shared:
                    incoming.append({"relationship": ref.section, "requirements": shared, "source": {"id": other.id, "path": other.rel}})
            covered = sorted(mine & set(other.covers))
            if covered:
                incoming.append({"relationship": "Covers", "requirements": covered, "source": {"id": other.id, "path": other.rel}})
    else:
        if defined_in is not None:
            result.update(defined_in={"id": defined_in.id, "path": defined_in.rel, "title": defined_in.title})
        else:
            result.update(defined_in=None)
        if entry and entry.replaced_by:
            result["replaced_by"] = entry.replaced_by
        for other in docs:
            if target in other.covers:
                incoming.append({"relationship": "Covers", "requirements": [target], "source": {"id": other.id, "path": other.rel}})
            for ref in other.parsed.refs:
                if target in ref.req_ids:
                    incoming.append({"relationship": ref.section, "requirements": [target], "source": {"id": other.id, "path": other.rel}})
    key = lambda x: (x["relationship"], (x.get("source") or {}).get("id") or "", str(x.get("href") or ""))
    result["outgoing"] = sorted(outgoing, key=key)
    result["incoming"] = sorted(incoming, key=key)
    return Outcome(0, result, diags)


def _ref_ids(doc: Doc) -> set[str]:
    """Requirement and source-document IDs a document is tied to (for overlap matching)."""
    ids = set(doc.covers)
    by_path_ids: set[str] = set()
    for ref in doc.parsed.refs:
        ids.update(ref.req_ids)
        if ref.href and ref.section == "Derived From":
            m = re.match(r"^((?:BR|PR|US|DES|PLAN|RES|TEST)-\d{3,})-", ref.href.rsplit("/", 1)[-1])
            if m:
                by_path_ids.add(m.group(1))
    return ids | by_path_ids


def find_overlaps(project: Project, category: str, title: str, purpose: str | None, covers: list[str]) -> Outcome:
    for value in covers:
        if id_kind(value) is None:
            return Outcome(2, diagnostics=[Diagnostic("error", "bad-id", f"--covers value {value!r} is not a valid ID")])
    docs, diags = scan_documents(project)
    want_title = tokens(title)
    want_purpose = tokens(purpose) if purpose else set()
    want_refs = set(covers)
    signals = {"title": True, "purpose": bool(want_purpose), "refs": bool(want_refs)}
    total_weight = sum(w for k, w in WEIGHTS.items() if signals[k])
    candidates = []
    for doc in docs:
        if not doc.valid or doc.category != category or doc.meta.get("status") == "Superseded":
            continue
        reasons = []
        title_score = 1.0 if tokens(doc.title) == want_title and want_title else jaccard(want_title, tokens(doc.title))
        if title_score == 1.0:
            reasons.append("same normalized title")
        elif title_score > 0:
            reasons.append(f"title similarity {title_score:.2f}")
        purpose_score = jaccard(want_purpose, tokens(str(doc.meta.get("purpose", "")))) if signals["purpose"] else 0.0
        if purpose_score > 0:
            reasons.append(f"purpose similarity {purpose_score:.2f}")
        refs_score = 0.0
        if signals["refs"]:
            have = _ref_ids(doc)
            have_owners = {owner_of(i) for i in have if REQ_ID_RE.match(i)}
            shared = sorted(i for i in want_refs if i in have or (DOC_ID_RE.match(i) and i in have_owners))
            refs_score = len(shared) / len(want_refs)
            if shared:
                reasons.append(f"shares references: {', '.join(shared)}")
        score = (title_score * WEIGHTS["title"] + purpose_score * WEIGHTS["purpose"] * signals["purpose"]
                 + refs_score * WEIGHTS["refs"] * signals["refs"]) / total_weight
        if title_score == 1.0:
            score = max(score, LIKELY)
        if score < POSSIBLE:
            continue
        level = "likely" if score >= LIKELY else "possible"
        candidates.append({**_doc_row(doc), "score": round(score, 3), "level": level, "reasons": reasons})
    candidates.sort(key=lambda c: (-c["score"], id_sort_key(c["id"])))
    return Outcome(0, {"category": category, "title": title, "candidates": candidates,
                       "action": "ask-human" if candidates else "none"}, diags)

