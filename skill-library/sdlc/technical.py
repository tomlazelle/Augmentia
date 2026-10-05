"""R2 evidence records: Story Implementation Records and TEST Verification Runs (deterministic schema checks)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .markdown import FENCE_RE, HEADING_RE
from .model import Diagnostic

RESULTS = ("passed", "failed", "blocked", "not-run")
KINDS = ("automated", "manual")
FIELD_RE = re.compile(r"^\s*[-*]\s+\*\*([^*:]+):\*\*\s*(.*?)\s*$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z)?$")
AC_RE = re.compile(r"^AC-([1-9]\d*)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+\S")
RECORD_ID = {"IR": re.compile(r"^(IR-\d+) — (\S+)\s*$"), "VR": re.compile(r"^(VR-\d+) — (\S+)\s*$")}
UNRESOLVED_HEADING = "unresolved acceptance behavior (tbd)"


@dataclass
class Section:
    level: int
    title: str
    line: int
    end: int = 0
    body: list[tuple[int, str]] = field(default_factory=list)


def sections(text: str) -> list[Section]:
    """Headings (levels 1-3) outside code fences. A section's body runs until the next heading of the same or a
    shallower level, so a level-2 body includes its level-3 subsections."""
    lines = text.split("\n")
    heads: list[Section] = []
    fence = None
    for idx, raw in enumerate(lines):
        fm = FENCE_RE.match(raw)
        if fm:
            fence = None if fence == fm.group(1) else (fence or fm.group(1))
            continue
        heading = None if fence else HEADING_RE.match(raw)
        if heading and len(heading.group(1)) <= 3:
            heads.append(Section(len(heading.group(1)), heading.group(2).strip(), idx + 1))
    for k, sec in enumerate(heads):
        end = len(lines)
        for nxt in heads[k + 1:]:
            if nxt.level <= sec.level:
                end = nxt.line - 1
                break
        sec.end = end
        sec.body = [(n + 1, lines[n]) for n in range(sec.line, end)]
    return heads


def find(secs: list[Section], title: str, level: int) -> Section | None:
    return next((s for s in secs if s.level == level and s.title.lower() == title.lower()), None)


def acceptance_criteria_count(secs: list[Section]) -> int:
    sec = find(secs, "Acceptance Criteria", 2)
    if sec is None:
        return 0
    count, stop = 0, False
    for _, line in sec.body:
        if line.startswith("### "):
            stop = True  # subsections such as Unresolved Acceptance Behavior hold no decided criteria
        if not stop and NUMBERED_RE.match(line):
            count += 1
    return count


def unresolved_tbd_bullets(secs: list[Section]) -> int:
    sec = next((s for s in secs if s.level == 3 and s.title.lower() == UNRESOLVED_HEADING), None)
    if sec is None:
        return 0
    return sum(1 for _, line in sec.body if re.match(r"^\s*[-*]\s+\*\*TBD\*\*", line))


@dataclass
class Record:
    id: str
    stamp: str
    line: int
    fields: dict[str, str]
    order: int = 0


def records(secs: list[Section], heading: str, prefix: str) -> tuple[list[Record], list[tuple[int, str]]]:
    """Parse `### <PREFIX>-n — <stamp>` blocks under the `## heading` section. Returns (records, bad heading lines)."""
    parent = find(secs, heading, 2)
    if parent is None:
        return [], []
    recs, bad = [], []
    for sec in secs:
        if sec.level != 3 or not (parent.line < sec.line <= parent.end):
            continue
        m = RECORD_ID[prefix].match(sec.title)
        if not m:
            bad.append((sec.line, sec.title))
            continue
        fields = {}
        for _, line in sec.body:
            fm = FIELD_RE.match(line)
            if fm:
                fields.setdefault(fm.group(1).strip().lower(), fm.group(2))
        recs.append(Record(m.group(1), m.group(2), sec.line, fields, len(recs)))
    return recs, bad


def check_implementation_records(rel: str, doc_id: str, secs: list[Section]) -> tuple[list[Record], list[Diagnostic]]:
    recs, bad = records(secs, "Implementation Record", "IR")
    diags = [Diagnostic("error", "implementation-record-invalid",
                        f"heading must be '### IR-<n> — <YYYY-MM-DD>': {title[:50]}", path=rel, id=doc_id, line=line)
             for line, title in bad]
    seen = set()
    for r in recs:
        if r.id in seen:
            diags.append(Diagnostic("error", "implementation-record-invalid", f"{r.id} appears more than once",
                                    path=rel, id=doc_id, line=r.line))
        seen.add(r.id)
        if not TIMESTAMP_RE.match(r.stamp):
            diags.append(Diagnostic("error", "implementation-record-invalid",
                                    f"{r.id}: date must be YYYY-MM-DD, got {r.stamp!r}", path=rel, id=doc_id, line=r.line))
        for key in ("summary", "files changed"):
            if not r.fields.get(key, "").strip():
                diags.append(Diagnostic("error", "implementation-record-invalid",
                                        f"{r.id}: required field '{key.title()}' is missing or empty",
                                        path=rel, id=doc_id, line=r.line))
    return recs, diags


def check_verification_runs(rel: str, doc_id: str, secs: list[Section], story_ac: dict[str, int | None]
                            ) -> tuple[list[Record], list[Diagnostic]]:
    """Validate Verification Runs of one TEST document. `story_ac` maps Story ID -> criteria count (None if unknown)."""
    recs, bad = records(secs, "Verification Runs", "VR")
    diags = [Diagnostic("error", "verification-bad-heading",
                        f"heading must be '### VR-<n> — <YYYY-MM-DD[THH:MM:SSZ]>': {title[:50]}", path=rel, id=doc_id, line=line)
             for line, title in bad]
    seen = set()

    def err(r: Record, code: str, msg: str) -> None:
        diags.append(Diagnostic("error", code, f"{r.id}: {msg}", path=rel, id=doc_id, line=r.line))

    for r in recs:
        if r.id in seen:
            err(r, "verification-bad-heading", "run ID appears more than once in this document")
        seen.add(r.id)
        if not TIMESTAMP_RE.match(r.stamp):
            err(r, "verification-bad-heading", f"timestamp must be ISO (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ), got {r.stamp!r}")
        f = r.fields
        kind, result = f.get("kind", "").strip(), f.get("result", "").strip()
        for key in ("story", "kind", "result", "criteria", "environment", "performed by", "observed"):
            if not f.get(key, "").strip():
                err(r, "verification-missing-field", f"required field '{key.title()}' is missing or empty")
        if kind and kind not in KINDS:
            err(r, "verification-bad-value", f"Kind must be one of {', '.join(KINDS)}, got {kind!r}")
        if result and result not in RESULTS:
            err(r, "verification-bad-value", f"Result must be one of {', '.join(RESULTS)}, got {result!r}")
        if kind == "automated" and result in ("passed", "failed"):
            for key in ("command", "exit code"):
                if not f.get(key, "").strip():
                    err(r, "verification-missing-field", f"automated {result} run requires '{key.title()}'")
            code = f.get("exit code", "").strip()
            if code:
                if not re.fullmatch(r"-?\d+", code):
                    err(r, "verification-bad-value", f"Exit code must be an integer, got {code!r}")
                elif result == "passed" and int(code) != 0:
                    err(r, "verification-inconsistent", f"marked passed but exit code is {code}")
                elif result == "failed" and int(code) == 0:
                    err(r, "verification-inconsistent", "marked failed but exit code is 0")
        story = f.get("story", "").strip()
        if story:
            if story not in story_ac:
                err(r, "verification-unknown-story", f"Story {story} does not exist")
        for token in [t.strip() for t in f.get("criteria", "").split(",") if t.strip()]:
            if token.lower() == "none":
                continue  # supporting/smoke check that demonstrates no acceptance criterion
            m = AC_RE.match(token)
            if not m:
                err(r, "verification-bad-criteria", f"criterion {token!r} must look like AC-1")
            elif story_ac.get(story) is not None and int(m.group(1)) > story_ac[story]:
                err(r, "verification-bad-criteria", f"{token} does not exist: {story} has {story_ac[story]} acceptance criteria")
    return recs, diags


def is_superseded(rec: Record) -> bool:
    return rec.fields.get("superseded", "").strip().lower().startswith("yes")


def criteria_of(rec: Record) -> list[int]:
    return [int(m.group(1)) for t in rec.fields.get("criteria", "").split(",") if (m := AC_RE.match(t.strip()))]
