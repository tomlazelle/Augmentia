"""Minimal Markdown extraction: links, requirement declarations, References sections."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import unquote

from .model import REQ_ID_RE, REQ_TOKEN_RE

FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM_RE = re.compile(r"^\s*[-*+]\s+")
LIST_DECL_RE = re.compile(r"^\s*[-*+]\s+\*\*([^*]+)\*\*\s+—\s+(\S.*)$")
HEAD_DECL_RE = re.compile(r"^#{1,6}\s+\*\*([^*]+)\*\*(?:\s+—\s+(\S.*))?\s*$")
ATTEMPT_RE = re.compile(r"^\s*(?:[-*+]|#{1,6})\s+\**\s*[A-Z]{2,4}-\d+-R")

REF_SECTIONS = ("Derived From", "Related To", "Supporting Artifacts")


@dataclass
class ReqDecl:
    id: str
    line: int
    text: str


@dataclass
class Ref:
    section: str
    line: int
    href: str | None
    req_ids: list[str] = field(default_factory=list)


@dataclass
class ParsedBody:
    requirements: list[ReqDecl] = field(default_factory=list)
    malformed: list[tuple[int, str]] = field(default_factory=list)
    refs: list[Ref] = field(default_factory=list)
    links: list[tuple[int, str]] = field(default_factory=list)


def extract_hrefs(line: str) -> list[str]:
    """Local link targets on a line: fragments/queries removed; external and anchor-only skipped."""
    out = []
    for raw in LINK_RE.findall(INLINE_CODE_RE.sub("", line)):
        href = raw.strip("<>").strip()
        if not href or href.startswith("#") or SCHEME_RE.match(href):
            continue
        href = unquote(href.split("#", 1)[0].split("?", 1)[0])
        if href:
            out.append(href)
    return out


def parse_body(lines: list[str], start: int) -> ParsedBody:
    """Parse body lines (0-based `start` index into the full file) outside code fences."""
    parsed = ParsedBody()
    fence = None
    h2 = ""
    h3 = ""
    for idx in range(start, len(lines)):
        text = lines[idx]
        lineno = idx + 1
        fm = FENCE_RE.match(text)
        if fm:
            fence = None if fence == fm.group(1) else (fence or fm.group(1))
            continue
        if fence:
            continue
        heading = HEADING_RE.match(text)
        if heading:
            level, title = len(heading.group(1)), heading.group(2)
            if level == 2:
                h2, h3 = title, ""
            elif level == 3:
                h3 = title
        in_refs = h2.lower() == "references"

        hrefs = extract_hrefs(text)
        parsed.links.extend((lineno, h) for h in hrefs)

        if in_refs:
            if h3 and LIST_ITEM_RE.match(text):
                reqs = sorted(set(REQ_TOKEN_RE.findall(INLINE_CODE_RE.sub("", text))))
                section = next((s for s in REF_SECTIONS if s.lower() == h3.lower()), h3)
                for href in hrefs:
                    parsed.refs.append(Ref(section, lineno, href, reqs))
                if not hrefs and reqs:
                    parsed.refs.append(Ref(section, lineno, None, reqs))
            continue

        m = LIST_DECL_RE.match(text) or HEAD_DECL_RE.match(text)
        if m and REQ_ID_RE.match(m.group(1).strip()):
            parsed.requirements.append(ReqDecl(m.group(1).strip(), lineno, (m.group(2) or "").strip()))
        elif ATTEMPT_RE.match(text):
            parsed.malformed.append((lineno, text.strip()))
    return parsed


def mask_region(text: str, start_marker: str, end_marker: str) -> str:
    """Blank out a marker-delimited region (used to ignore generated content when checking links)."""
    s = text.find(start_marker)
    e = text.find(end_marker)
    if s == -1 or e == -1 or e < s:
        return text
    return text[:s] + "\n" * text[s:e].count("\n") + text[e + len(end_marker):]
