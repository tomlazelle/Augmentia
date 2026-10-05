"""Shared constants, ID grammar and the diagnostic record."""

from __future__ import annotations

import datetime
import os
import re
from dataclasses import asdict, dataclass

DOC_CATEGORIES = ("BR", "PR", "US", "DES", "PLAN", "RES", "TEST")
_CATS = "|".join(DOC_CATEGORIES)

DOC_ID_RE = re.compile(rf"^({_CATS})-(\d{{3,}})$")
REQ_ID_RE = re.compile(rf"^(({_CATS})-\d{{3,}})-R(\d{{3,}})$")
REQ_TOKEN_RE = re.compile(rf"\b(?:{_CATS})-\d{{3,}}-R\d{{3,}}\b")
FILENAME_RE = re.compile(rf"^(({_CATS})-\d{{3,}})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")

DOC_STATUSES = ("Draft", "In Review", "Approved", "Superseded")
DELIVERY_STATUSES = ("Not Started", "Ready", "In Progress", "Implemented", "Verified")

# category -> (top-level directory key, Artifacts subdirectory or None)
CATEGORY_LOCATION = {
    "BR": ("BR", None),
    "PR": ("PR", None),
    "US": ("Stories", None),
    "DES": ("Artifacts", "design"),
    "PLAN": ("Artifacts", "plans"),
    "RES": ("Artifacts", "research"),
    "TEST": ("Artifacts", "tests"),
}
ARTIFACT_SUBDIRS = {"design": "DES", "plans": "PLAN", "research": "RES", "tests": "TEST"}
TOP_DIRS = ("BR", "PR", "Stories", "Artifacts")

GEN_START = "<!-- sdlc:generated:start -->"
GEN_END = "<!-- sdlc:generated:end -->"


@dataclass
class Diagnostic:
    severity: str  # error | warning | notice
    code: str
    message: str
    path: str | None = None
    id: str | None = None
    line: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    def human(self) -> str:
        where = self.path or ""
        if where and self.line:
            where += f":{self.line}"
        parts = [f"{self.severity}:"]
        if where:
            parts.append(f"{where}:")
        if self.id:
            parts.append(f"[{self.id}]")
        parts.append(f"{self.message} ({self.code})")
        return " ".join(parts)


@dataclass
class Outcome:
    """Result of a command: exit code, JSON-able result, diagnostics."""

    exit_code: int = 0
    result: dict | None = None
    diagnostics: list | None = None

    def __post_init__(self):
        self.result = self.result if self.result is not None else {}
        self.diagnostics = self.diagnostics if self.diagnostics is not None else []


def id_kind(value: str) -> str | None:
    if DOC_ID_RE.match(value):
        return "document"
    if REQ_ID_RE.match(value):
        return "requirement"
    return None


def category_of(value: str) -> str | None:
    return value.split("-", 1)[0] if id_kind(value) else None


def owner_of(req_id: str) -> str:
    m = REQ_ID_RE.match(req_id)
    assert m
    return m.group(1)


def id_sort_key(value: str) -> tuple:
    m = REQ_ID_RE.match(value)
    if m:
        cat, num = m.group(1).split("-")
        return (DOC_CATEGORIES.index(cat), int(num), int(m.group(3)))
    m = DOC_ID_RE.match(value)
    if m:
        return (DOC_CATEGORIES.index(m.group(1)), int(m.group(2)), 0)
    return (len(DOC_CATEGORIES), 0, 0)


def format_doc_id(category: str, number: int) -> str:
    return f"{category}-{number:03d}"


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def today() -> str:
    """ISO date; SDLC_TODAY overrides it so tests and reproducible runs are deterministic."""
    return os.environ.get("SDLC_TODAY") or datetime.date.today().isoformat()
