"""Project root discovery, .sdlc/config.md, and authored-document loading."""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter
from .markdown import ParsedBody, parse_body
from .model import (
    ARTIFACT_SUBDIRS,
    CATEGORY_LOCATION,
    DELIVERY_STATUSES,
    DOC_ID_RE,
    DOC_STATUSES,
    FILENAME_RE,
    REQ_ID_RE,
    TOP_DIRS,
    Diagnostic,
    category_of,
)

SCHEMA_VERSION = 1
DEFAULT_DIRECTORIES = {k: k for k in TOP_DIRS}
REQUIRED_FIELDS = ("id", "title", "purpose", "status", "created", "updated")
EVIDENCE_DIR = "evidence"
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CREDENTIAL_KEY_RE = re.compile(r"token|secret|password|passwd|credential|auth|api[_-]?key", re.I)


def find_root(start: Path) -> Path | None:
    """Nearest ancestor (including `start`) that contains a `.sdlc/` directory."""
    for candidate in [start, *start.parents]:
        if (candidate / ".sdlc").is_dir():
            return candidate
    return None


def load_config(root: Path) -> tuple[dict | None, list[Diagnostic]]:
    """Load and validate the minimal .sdlc/config.md schema."""
    rel = ".sdlc/config.md"
    path = root / rel
    if not path.is_file():
        return None, [Diagnostic("error", "missing-config", "configuration file is missing", path=rel)]
    raw, _ = frontmatter.split(path.read_text(encoding="utf-8"))
    if raw is None:
        return None, [Diagnostic("error", "bad-config", "config.md has no YAML front matter", path=rel)]
    try:
        data = frontmatter.parse(raw)
    except ValueError as exc:
        return None, [Diagnostic("error", "bad-config", str(exc), path=rel)]

    diags: list[Diagnostic] = []

    def err(msg: str) -> None:
        diags.append(Diagnostic("error", "bad-config", msg, path=rel))

    name = data.get("project_name")
    if not isinstance(name, str) or not name.strip():
        err("project_name must be a non-empty string")
    if data.get("schema_version") != SCHEMA_VERSION or isinstance(data.get("schema_version"), bool):
        err(f"schema_version must be {SCHEMA_VERSION}")
    dirs = data.get("directories")
    if not isinstance(dirs, dict) or set(dirs) != set(TOP_DIRS):
        err(f"directories must be a mapping with exactly the keys {', '.join(TOP_DIRS)}")
    else:
        values = list(dirs.values())
        for value in values:
            if not isinstance(value, str) or not value or "/" in value or value.startswith(".") or value == "..":
                err("directories values must be single-segment, non-hidden folder names")
                break
        else:
            if len(set(values)) != len(values):
                err("directories values must be unique")
    if "publishing" in data and not isinstance(data["publishing"], dict):
        err("publishing must be a mapping when present")
    elif isinstance(data.get("publishing"), dict):
        secret_keys = sorted(k for k in data["publishing"] if CREDENTIAL_KEY_RE.search(str(k)))
        if secret_keys:
            err(f"publishing must not hold credentials ({', '.join(secret_keys)}); authenticate through the provider's own tooling")
    unknown = set(data) - {"project_name", "schema_version", "directories", "publishing"}
    if unknown:
        diags.append(Diagnostic("warning", "unknown-config-key", f"unknown keys: {', '.join(sorted(unknown))}", path=rel))
    return (None if any(d.severity == "error" for d in diags) else data), diags


@dataclass
class Project:
    root: Path
    directories: dict = field(default_factory=lambda: dict(DEFAULT_DIRECTORIES))
    config: dict | None = None

    @classmethod
    def open(cls, root: Path) -> "Project":
        root = root.resolve()
        cfg, _ = load_config(root)
        project = cls(root=root, config=cfg)
        if cfg:
            project.directories = dict(cfg["directories"])
        return project

    def top(self, key: str) -> Path:
        return self.root / self.directories[key]

    def category_dir(self, category: str) -> Path:
        key, sub = CATEGORY_LOCATION[category]
        base = self.top(key)
        return base / sub if sub else base

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    @property
    def name(self) -> str:
        return (self.config or {}).get("project_name") or self.root.name


@dataclass
class Doc:
    path: Path
    rel: str
    loc_cat: str | None
    name_id: str | None
    meta: dict
    parsed: ParsedBody
    diags: list[Diagnostic]
    covers: list[str] = field(default_factory=list)
    text: str = ""

    @property
    def id(self) -> str:
        meta_id = self.meta.get("id")
        return self.name_id or (meta_id if isinstance(meta_id, str) else self.path.stem)

    @property
    def category(self) -> str | None:
        return category_of(self.id) or self.loc_cat

    @property
    def is_story(self) -> bool:
        return self.category == "US"

    @property
    def valid(self) -> bool:
        return not any(d.severity == "error" for d in self.diags)

    @property
    def title(self) -> str:
        return str(self.meta.get("title") or self.id)


def _is_date(value) -> bool:
    if not isinstance(value, str) or not ISO_DATE_RE.match(value):
        return False
    try:
        datetime.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _check_meta(doc: Doc, fields: bool = True) -> None:
    meta = doc.meta
    diags = doc.diags

    def err(code: str, msg: str, sev: str = "error") -> None:
        diags.append(Diagnostic(sev, code, msg, path=doc.rel, id=doc.id))

    if doc.name_id is None:
        err("bad-filename", "filename must match <ID>-<short-kebab-title>.md (e.g. BR-001-business-overview.md)")
    if doc.name_id and doc.loc_cat != category_of(doc.name_id):
        expected = doc.loc_cat or "a managed directory"
        err("wrong-directory", f"{category_of(doc.name_id)} documents do not belong here (directory holds {expected})")
    if doc.name_id is None and doc.loc_cat is None:
        err("misplaced-document", "document is not in a managed directory")
    if fields:
        _check_fields(doc, err)
    _check_body(doc)


def _check_fields(doc: Doc, err) -> None:
    meta = doc.meta
    for key in REQUIRED_FIELDS:
        if meta.get(key) in (None, ""):
            err("missing-field", f"required front matter field '{key}' is missing")
    fm_id = meta.get("id")
    if fm_id not in (None, ""):
        if not isinstance(fm_id, str) or not DOC_ID_RE.match(fm_id):
            err("invalid-id", f"id {fm_id!r} is not a valid document ID (e.g. BR-001)")
        elif doc.name_id and fm_id != doc.name_id:
            err("id-filename-mismatch", f"front matter id {fm_id} does not match filename ID {doc.name_id}")
    for key in ("title", "purpose"):
        value = meta.get(key)
        if value not in (None, "") and (not isinstance(value, str) or not value.strip()):
            err("invalid-field", f"'{key}' must be a non-empty string")
        elif isinstance(value, str) and key == "purpose" and "\n" in value.strip():
            err("invalid-purpose", "'purpose' must be a single line (one sentence)")
    status = meta.get("status")
    if status not in (None, "") and status not in DOC_STATUSES:
        err("invalid-status", f"status {status!r} must be one of {', '.join(DOC_STATUSES)}")
    dates_ok = True
    for key in ("created", "updated"):
        value = meta.get(key)
        if value not in (None, "") and not _is_date(value):
            dates_ok = False
            err("invalid-date", f"'{key}' must be an ISO date YYYY-MM-DD, got {value!r}")
    if dates_ok and _is_date(meta.get("created")) and _is_date(meta.get("updated")) and meta["updated"] < meta["created"]:
        err("date-order", "'updated' is earlier than 'created'", "warning")

    if doc.is_story:
        ds = meta.get("delivery_status")
        if ds in (None, ""):
            err("missing-field", "required Story field 'delivery_status' is missing")
        elif ds not in DELIVERY_STATUSES:
            err("invalid-delivery-status", f"delivery_status {ds!r} must be one of {', '.join(DELIVERY_STATUSES)}")
        if "covers" not in meta or meta["covers"] is None:
            err("missing-covers", "Story must declare 'covers' (use covers: [] for a standalone Story)")
        elif not isinstance(meta["covers"], list) or not all(isinstance(c, str) for c in meta["covers"]):
            err("invalid-covers", "'covers' must be a list of requirement IDs")
        else:
            bad = [c for c in meta["covers"] if not REQ_ID_RE.match(c)]
            if bad:
                err("invalid-covers", f"'covers' contains malformed requirement IDs: {', '.join(bad)}")
            doc.covers = [c for c in meta["covers"] if REQ_ID_RE.match(c)]


def _check_body(doc: Doc) -> None:
    diags = doc.diags
    for lineno, text in doc.parsed.malformed:
        diags.append(Diagnostic(
            "error", "malformed-requirement",
            f"malformed requirement declaration; use '- **PR-001-R001** — text': {text[:60]}",
            path=doc.rel, id=doc.id, line=lineno))
    for req in doc.parsed.requirements:
        if req.id.rsplit("-R", 1)[0] != doc.id:
            diags.append(Diagnostic(
                "error", "requirement-wrong-document",
                f"requirement {req.id} is declared in {doc.id}; requirement IDs are scoped to their document",
                path=doc.rel, id=req.id, line=req.line))


def load_doc(project: Project, path: Path, loc_cat: str | None) -> Doc:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    m = FILENAME_RE.match(path.name)
    diags: list[Diagnostic] = []
    raw, body_start = frontmatter.split(text)
    meta: dict = {}
    rel = project.rel(path)
    if raw is None:
        diags.append(Diagnostic("error", "bad-front-matter", "document has no YAML front matter block", path=rel))
    else:
        try:
            meta = frontmatter.parse(raw)
        except ValueError as exc:
            diags.append(Diagnostic("error", "bad-front-matter", str(exc), path=rel))
    doc = Doc(path=path, rel=rel, loc_cat=loc_cat, name_id=m.group(1) if m else None,
              meta=meta, parsed=parse_body(lines, body_start), diags=diags, text=text)
    _check_meta(doc, fields=not diags)  # field checks need usable front matter
    return doc


def scan_documents(project: Project) -> tuple[list[Doc], list[Diagnostic]]:
    docs: list[Doc] = []
    diags: list[Diagnostic] = []

    def scan(directory: Path, loc_cat: str | None) -> None:
        for child in sorted(directory.iterdir()):
            if child.name.startswith("."):
                continue
            if loc_cat == "TEST" and child.is_dir() and child.name == EVIDENCE_DIR:
                continue  # Artifacts/tests/evidence/ holds verification logs, not documents
            if child.is_dir():
                diags.append(Diagnostic("warning", "unexpected-directory",
                                        "directory is not part of the managed layout and is ignored",
                                        path=project.rel(child)))
            elif child.suffix == ".md" and child.name != "map.md":
                docs.append(load_doc(project, child, loc_cat))

    for key in ("BR", "PR", "Stories"):
        directory = project.top(key)
        if directory.is_dir():
            scan(directory, {"BR": "BR", "PR": "PR", "Stories": "US"}[key])
    artifacts = project.top("Artifacts")
    if artifacts.is_dir():
        for child in sorted(artifacts.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                if child.name in ARTIFACT_SUBDIRS:
                    scan(child, ARTIFACT_SUBDIRS[child.name])
                else:
                    diags.append(Diagnostic("warning", "unexpected-directory",
                                            "not a recognised Artifacts subdirectory (design, plans, research, tests); ignored",
                                            path=project.rel(child)))
            elif child.suffix == ".md" and child.name != "map.md":
                docs.append(load_doc(project, child, None))
    return docs, diags
