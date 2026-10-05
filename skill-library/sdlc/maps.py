"""map.md generation: only the marker-delimited generated region is ever rewritten."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .ledger import atomic_write
from .markdown import REF_SECTIONS
from .model import ARTIFACT_SUBDIRS, GEN_END, GEN_START, Diagnostic, id_sort_key
from .project import Doc, Project, scan_documents

_TOP = {
    "BR": ("Business Requirements", "Business problem, objectives, stakeholders, scope and success measures.", "BR"),
    "PR": ("Product Requirements", "Product capabilities, user expectations and release scope.", "PR"),
    "Stories": ("User Stories", "User stories with observable acceptance criteria, traceable to requirements.", "US"),
    "Artifacts": ("Artifacts", "Supporting design, planning, research and test artifacts.", None),
}
_SUB = {
    "design": ("Design", "Technical design documents."),
    "plans": ("Plans", "Implementation plans."),
    "research": ("Research", "Research findings and supporting evidence."),
    "tests": ("Tests", "Test plans and verification reports."),
}
ROOT_SUMMARY = "Describe this project here. This text is hand-written and is never overwritten."


@dataclass
class MapSpec:
    kind: str  # root | top | sub
    key: str
    directory: Path
    title: str
    purpose: str
    category: str | None

    @property
    def path(self) -> Path:
        return self.directory / "map.md"


def specs(project: Project) -> list[MapSpec]:
    out = [MapSpec("root", "root", project.root, project.name, ROOT_SUMMARY, None)]
    for key, (title, purpose, cat) in _TOP.items():
        out.append(MapSpec("top", key, project.top(key), title, purpose, cat))
    artifacts = project.top("Artifacts")
    for sub, (title, purpose) in _SUB.items():
        if (artifacts / sub).is_dir():
            out.append(MapSpec("sub", sub, artifacts / sub, title, purpose, ARTIFACT_SUBDIRS[sub]))
    return out


def _cell(text: str) -> str:
    return " ".join(str(text).split()).replace("|", "\\|")


def _link(label: str, target: Path, from_dir: Path) -> str:
    rel = posixpath.relpath(target.as_posix(), from_dir.as_posix())
    label = _cell(label).replace("[", "\\[").replace("]", "\\]")
    return f"[{label}]({quote(rel)})"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return lines


def render_region(project: Project, spec: MapSpec, docs: list[Doc]) -> str:
    lines: list[str] = []
    if spec.kind == "root":
        rows = [[_link(_TOP[k][0], project.top(k) / "map.md", spec.directory), _cell(_TOP[k][1])] for k in _TOP]
        lines += ["## Directories", ""] + _table(["Directory", "Purpose"], rows)
    elif spec.key == "Artifacts":
        subs = [s for s in specs(project) if s.kind == "sub"]
        lines += ["## Subdirectories", ""]
        if subs:
            lines += _table(["Directory", "Purpose"], [
                [_link(f"{s.key}/", s.path, spec.directory), _cell(s.purpose)] for s in subs])
        else:
            lines.append("_No artifact subdirectories yet. They are created on first use._")
    else:
        mine = sorted((d for d in docs if d.loc_cat == spec.category and d.valid and d.path.parent == spec.directory),
                      key=lambda d: id_sort_key(d.id))
        story = spec.category == "US"
        header = ["ID", "Document", "Purpose", "Status"] + (["Delivery"] if story else [])
        lines += ["## Documents", ""]
        if mine:
            rows = []
            for d in mine:
                row = [d.id, _link(d.title, d.path, spec.directory), _cell(d.meta["purpose"]), _cell(d.meta["status"])]
                if story:
                    row.append(_cell(d.meta["delivery_status"]))
                rows.append(row)
            lines += _table(header, rows)
        else:
            lines.append("_No documents yet._")
        rel_rows = []
        by_path = {d.path.resolve(): d for d in docs}
        for d in mine:
            for section in REF_SECTIONS:
                for ref in d.parsed.refs:
                    if ref.section != section or not ref.href:
                        continue
                    target = (d.path.parent / ref.href).resolve()
                    if not target.exists():
                        continue
                    other = by_path.get(target)
                    label = other.id if other else target.name
                    rel_rows.append((id_sort_key(d.id), REF_SECTIONS.index(section), label,
                                     [_link(d.id, d.path, spec.directory), section, _link(label, target, spec.directory)]))
        lines += ["", "## Relationships", ""]
        if rel_rows:
            seen, uniq = set(), []
            for item in sorted(rel_rows, key=lambda r: r[:3]):
                if tuple(item[3]) not in seen:
                    seen.add(tuple(item[3]))
                    uniq.append(item[3])
            lines += _table(["Source", "Relationship", "Target"], uniq)
        else:
            lines.append("_No relationships declared._")
    return "\n".join(lines)


def build_new_map(project: Project, spec: MapSpec, docs: list[Doc]) -> str:
    region = render_region(project, spec, docs)
    return f"# {spec.title}\n\n{spec.purpose}\n\n{GEN_START}\n{region}\n{GEN_END}\n\n## Open Questions\n\n- None yet.\n"


def find_region(text: str) -> tuple[int, int] | None:
    """(start, end) offsets of the text between the markers, or None if markers are absent/invalid."""
    if text.count(GEN_START) != 1 or text.count(GEN_END) != 1:
        return None
    s = text.index(GEN_START) + len(GEN_START)
    e = text.index(GEN_END)
    return (s, e) if s <= e else None


def replace_region(text: str, region: str) -> str | None:
    bounds = find_region(text)
    if bounds is None:
        return None
    return text[:bounds[0]] + f"\n{region}\n" + text[bounds[1]:]


def sync_map(project: Project, spec: MapSpec, docs: list[Doc]) -> tuple[str, Diagnostic | None]:
    """Create or refresh one map. Returns (action: created|updated|unchanged|blocked, diagnostic)."""
    rel = project.rel(spec.path)
    if not spec.path.exists():
        atomic_write(spec.path, build_new_map(project, spec, docs))
        return "created", None
    text = spec.path.read_text(encoding="utf-8")
    new = replace_region(text, render_region(project, spec, docs))
    if new is None:
        return "blocked", Diagnostic("error", "map-markers", f"map has missing or duplicated generated-region markers "
                                     f"({GEN_START} ... {GEN_END}); not modified", path=rel)
    if new == text:
        return "unchanged", None
    atomic_write(spec.path, new)
    return "updated", None


def update_maps(project: Project, only: MapSpec | None = None) -> tuple[dict, list[Diagnostic]]:
    docs, _ = scan_documents(project)
    result: dict[str, list[str]] = {"created": [], "updated": [], "unchanged": [], "blocked": []}
    diags: list[Diagnostic] = []
    for spec in ([only] if only else specs(project)):
        action, diag = sync_map(project, spec, docs)
        result[action].append(project.rel(spec.path))
        if diag:
            diags.append(diag)
    return result, diags


def check_maps(project: Project, docs: list[Doc]) -> list[Diagnostic]:
    """Validation view: missing maps, unusable markers, stale generated regions."""
    diags: list[Diagnostic] = []
    for spec in specs(project):
        rel = project.rel(spec.path)
        if not spec.directory.is_dir():
            continue  # missing directories are reported by the structure check
        if not spec.path.is_file():
            diags.append(Diagnostic("error", "missing-map", "directory has no map.md", path=rel))
            continue
        text = spec.path.read_text(encoding="utf-8")
        bounds = find_region(text)
        if bounds is None:
            diags.append(Diagnostic("error", "map-markers", "map is missing its generated-region markers", path=rel))
            continue
        if text[bounds[0]:bounds[1]].strip() != render_region(project, spec, docs).strip():
            diags.append(Diagnostic("error", "stale-map", "generated region is out of date; run 'sdlc update-map'", path=rel))
    return diags
