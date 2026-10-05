"""Publication records: the durable, Markdown-resident identity of a published Story (R3).

A Story that has been published carries a `## Publication` section with append-only
`### PUB-n — <YYYY-MM-DD>` entries. This module parses and checks them (used by `validate` and by the
duplicate check in `publish-preview`) and appends new entries. It never talks to a provider.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from . import technical
from .model import Diagnostic

HEADING = "Publication"
PROVIDERS = ("github",)
ISSUE_RE = re.compile(r"^#(\d+)$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

EMPTY_SECTION_TEXT = "None recorded."


@dataclass
class Publication:
    id: str
    date: str
    provider: str
    repository: str
    issue: str  # "#42"
    url: str | None
    line: int

    @property
    def number(self) -> int:
        return int(self.issue[1:])

    def to_dict(self) -> dict:
        return {"id": self.id, "date": self.date, "provider": self.provider, "repository": self.repository,
                "issue": self.issue, "url": self.url}


def parse(rel: str, doc_id: str, secs: list[technical.Section]) -> tuple[list[Publication], list[Diagnostic]]:
    """Publications recorded in a Story, plus `publication-invalid` errors for anything malformed."""
    recs, bad = technical.records(secs, HEADING, "PUB")
    diags = [Diagnostic("error", "publication-invalid", f"heading must be '### PUB-<n> — <YYYY-MM-DD>': {title[:50]}",
                        path=rel, id=doc_id, line=line) for line, title in bad]
    out: list[Publication] = []
    seen: set[str] = set()

    for r in recs:
        def err(msg: str) -> None:
            diags.append(Diagnostic("error", "publication-invalid", f"{r.id}: {msg}", path=rel, id=doc_id, line=r.line))

        if r.id in seen:
            err("appears more than once")
        seen.add(r.id)
        if not DATE_RE.match(r.stamp):
            err(f"date must be YYYY-MM-DD, got {r.stamp!r}")
        provider = r.fields.get("provider", "").strip()
        repository = r.fields.get("repository", "").strip()
        issue = r.fields.get("issue", "").strip()
        url = r.fields.get("url", "").strip() or None
        ok = True
        if provider not in PROVIDERS:
            err(f"Provider must be one of {', '.join(PROVIDERS)}, got {provider!r}")
            ok = False
        if not REPO_RE.match(repository):
            err(f"Repository must be 'owner/name', got {repository!r}")
            ok = False
        if not ISSUE_RE.match(issue):
            err(f"Issue must look like '#42', got {issue!r}")
            ok = False
        if ok:
            out.append(Publication(r.id, r.stamp, provider, repository, issue, url, r.line))
    return out, diags


def render_entry(number: int, date: str, provider: str, repository: str, issue_number: int, url: str | None) -> str:
    lines = [f"### PUB-{number} — {date}",
             f"- **Provider:** {provider}",
             f"- **Repository:** {repository}",
             f"- **Issue:** #{issue_number}"]
    if url:
        lines.append(f"- **URL:** {url}")
    lines.append(f"- **Recorded by:** `sdlc publish-apply` (publication is non-material; local Markdown stays authoritative)")
    return "\n".join(lines) + "\n"


def _bump_updated(text: str, today: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head, rest = text[:end], text[end:]
    head, n = re.subn(r"(?m)^updated:.*$", f"updated: {today}", head, count=1)
    return head + rest if n else text


def append_record(path: Path, date: str, provider: str, repository: str, issue_number: int, url: str | None) -> str:
    """Append a PUB entry to the Story file and set `updated`. Does not touch `status` or `delivery_status`.

    Returns the new PUB id. The write is atomic (temp file + rename), so a failure leaves the Story unchanged.
    """
    text = path.read_text(encoding="utf-8")
    secs = technical.sections(text)
    existing, _ = technical.records(secs, HEADING, "PUB")
    number = max((int(r.id.split("-")[1]) for r in existing), default=0) + 1
    entry = render_entry(number, date, provider, repository, issue_number, url).rstrip("\n")
    section = technical.find(secs, HEADING, 2)
    if section is None:
        new = text.rstrip("\n") + f"\n\n## {HEADING}\n\n{entry}\n"
    else:
        lines = text.split("\n")
        head = "\n".join(lines[:section.line])
        body = "\n".join(ln for ln in lines[section.line:section.end] if ln.strip() != EMPTY_SECTION_TEXT).strip("\n")
        tail = "\n".join(lines[section.end:]).strip("\n")
        new = head + "\n\n" + (body + "\n\n" if body else "") + entry + "\n" + ("\n" + tail + "\n" if tail else "")
    new = _bump_updated(new, date)
    tmp = path.with_name(f".{path.name}.sdlc-tmp")
    tmp.write_text(new, encoding="utf-8")
    os.replace(tmp, path)
    return f"PUB-{number}"
