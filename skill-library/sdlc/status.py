"""`status`: a read-only, structured project progress snapshot (R3).

Everything is derived from the current files by the same scanners `list`/`references`/`validate` use. Nothing is
written: no IDs, maps, statuses or evidence.
"""

from __future__ import annotations

from . import technical, validate as validate_mod
from .model import DELIVERY_STATUSES, DOC_CATEGORIES, DOC_STATUSES, Outcome, id_sort_key
from .project import Doc, Project, scan_documents

STRUCTURE_CODES = ("stale-map", "map-markers", "missing-map", "missing-directory", "broken-link")
REFERENCE_CODES = ("broken-link", "unknown-requirement", "covers-unknown", "retired-reference",
                   "covers-source-not-linked", "retired-id-in-use")


def _brief(d) -> dict:
    return {"code": d.code, "message": d.message, "path": d.path, "id": d.id, "line": d.line}


def _current_runs(docs: list[Doc]) -> dict[str, list[technical.Record]]:
    """Current (non-superseded) verification runs per Story ID."""
    out: dict[str, list[technical.Record]] = {}
    ac = {d.id: technical.acceptance_criteria_count(technical.sections(d.text)) for d in docs if d.is_story}
    for doc in docs:
        if doc.category != "TEST" or not doc.valid:
            continue
        recs, _ = technical.check_verification_runs(doc.rel, doc.id, technical.sections(doc.text), ac)
        for r in recs:
            if not technical.is_superseded(r):
                out.setdefault(r.fields.get("story", "").strip(), []).append(r)
    return out


def build_status(project: Project) -> Outcome:
    docs, _ = scan_documents(project)
    check = validate_mod.validate(project)
    diags = check.diagnostics
    valid = [d for d in docs if d.valid]
    by_sev = {s: [d for d in diags if d.severity == s] for s in ("error", "warning", "notice")}

    health = {
        "ok": not by_sev["error"],
        "summary": check.result["summary"],
        "documents": check.result["documents"],
        "errors": [_brief(d) for d in by_sev["error"]],
        "warnings": [_brief(d) for d in by_sev["warning"]],
        "stale_maps": sorted({d.path for d in diags if d.code in ("stale-map", "map-markers", "missing-map")}),
        "broken_references": [_brief(d) for d in by_sev["error"] if d.code in REFERENCE_CODES],
    }

    inventory = {}
    for cat in DOC_CATEGORIES:
        mine = [d for d in valid if d.category == cat]
        inventory[cat] = {
            "total": len(mine) + sum(1 for d in docs if not d.valid and d.category == cat),
            "by_status": {s: sum(d.meta.get("status") == s for d in mine) for s in DOC_STATUSES},
            "invalid": sum(1 for d in docs if not d.valid and d.category == cat),
        }

    stories = sorted((d for d in valid if d.is_story), key=lambda d: id_sort_key(d.id))
    delivery = {s: [] for s in DELIVERY_STATUSES}
    for st in stories:
        delivery[st.meta.get("delivery_status")].append({"id": st.id, "title": st.title, "status": st.meta.get("status"), "path": st.rel})

    traceability = {
        "uncovered_requirements": [d.id for d in by_sev["notice"] if d.code == "requirement-uncovered"],
        "standalone_stories": [d.id for d in by_sev["notice"] if d.code == "story-no-coverage"],
        "invalid_references": [_brief(d) for d in by_sev["error"] if d.code in REFERENCE_CODES],
        "unresolved_tbd": [st.id for st in stories if technical.unresolved_tbd_bullets(technical.sections(st.text))],
    }

    runs = _current_runs(docs)
    attention: list[dict] = []

    def add(kind: str, sid: str | None, message: str, path: str | None = None) -> None:
        attention.append({"kind": kind, "id": sid, "message": message, "path": path})

    for d in by_sev["error"]:
        add("validation-error", d.id, f"{d.message} ({d.code})", d.path)
    for sid in traceability["unresolved_tbd"]:
        add("unresolved-acceptance", sid, "has unresolved acceptance behavior (TBD) — decide it or accept the residual explicitly",
            next(s.rel for s in stories if s.id == sid))
    for st in stories:
        ds = st.meta.get("delivery_status")
        if ds == "Ready":
            add("ready-to-implement", st.id, "Ready — can be implemented (implement-story)", st.rel)
        elif ds == "In Progress":
            add("in-progress", st.id, "In Progress — implementation underway", st.rel)
        elif ds == "Implemented":
            mine = runs.get(st.id, [])
            bad = sorted({(r.id, r.fields.get("result", "?").strip()) for r in mine
                          if r.fields.get("result", "").strip() in ("failed", "blocked", "not-run")})
            if bad:
                add("verification-problem", st.id,
                    "current verification run(s) not passed: " + ", ".join(f"{i} {res}" for i, res in bad)
                    + " — rework (implement-story) or resolve, then re-verify", st.rel)
            add("awaiting-verification", st.id, "Implemented — awaiting verification (verify-story)", st.rel)
    for d in sorted((d for d in valid if d.meta.get("status") == "In Review"), key=lambda d: id_sort_key(d.id)):
        add("in-review", d.id, f"{d.category} document is In Review — awaiting a human decision", d.rel)
    rank = {"validation-error": 0, "verification-problem": 1, "unresolved-acceptance": 2, "awaiting-verification": 3,
            "in-progress": 4, "ready-to-implement": 5, "in-review": 6}
    attention.sort(key=lambda a: (rank[a["kind"]], id_sort_key(a["id"]) if a["id"] else (99, 0, 0)))

    result = {"health": health, "inventory": inventory, "delivery": delivery, "traceability": traceability,
              "attention": attention, "empty": not docs}
    return Outcome(0, result, [])
