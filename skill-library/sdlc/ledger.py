"""CLI-maintained ID ledger (.sdlc/ledger.md): a Markdown table of allocated/retired IDs."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from .model import Diagnostic, id_kind, id_sort_key

LEDGER_REL = ".sdlc/ledger.md"
HEADER = """# ID Ledger

Maintained by the `sdlc` CLI. Do not edit by hand.
Allocated and retired IDs are recorded here so IDs are never reused within a checkout.

| ID | Kind | State | Date | Note |
|---|---|---|---|---|
"""
_SPLIT = re.compile(r"(?<!\\)\|")
STATES = ("Allocated", "Retired")
KINDS = ("document", "requirement")


@dataclass
class Entry:
    id: str
    kind: str
    state: str
    date: str
    note: str = ""

    @property
    def replaced_by(self) -> str | None:
        m = re.match(r"Replaced by (\S+?)\.?(?:\s|$)", self.note)
        return m.group(1) if m else None


class Ledger:
    def __init__(self, path: Path):
        self.path = path
        self.entries: dict[str, Entry] = {}

    @classmethod
    def load(cls, path: Path) -> tuple["Ledger", list[Diagnostic]]:
        ledger = cls(path)
        diags: list[Diagnostic] = []
        if not path.is_file():
            return ledger, [Diagnostic("error", "missing-ledger", "ledger file is missing", path=LEDGER_REL)]
        in_table = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if not line.startswith("|"):
                continue
            cells = [c.strip().replace("\\|", "|") for c in _SPLIT.split(line.strip())[1:-1]]
            if cells[:1] == ["ID"]:
                in_table = True
                continue
            if not in_table or all(set(c) <= set("-: ") for c in cells):
                continue

            def bad(msg: str) -> None:
                diags.append(Diagnostic("error", "bad-ledger-row", msg, path=LEDGER_REL, line=lineno))

            if len(cells) != 5:
                bad("row must have 5 columns: ID, Kind, State, Date, Note")
                continue
            entry = Entry(*cells)
            if id_kind(entry.id) is None:
                bad(f"{entry.id!r} is not a valid ID")
            elif entry.kind != id_kind(entry.id) or entry.kind not in KINDS:
                bad(f"kind {entry.kind!r} does not match ID {entry.id}")
            elif entry.state not in STATES:
                bad(f"state {entry.state!r} must be Allocated or Retired")
            elif entry.id in ledger.entries:
                diags.append(Diagnostic("error", "duplicate-ledger-id", f"{entry.id} appears more than once in the ledger",
                                        path=LEDGER_REL, id=entry.id, line=lineno))
            else:
                ledger.entries[entry.id] = entry
        if not in_table:
            diags.append(Diagnostic("error", "bad-ledger", "ledger table header not found", path=LEDGER_REL))
        return ledger, diags

    def add(self, id: str, date: str, note: str = "") -> Entry:
        entry = Entry(id, id_kind(id) or "", "Allocated", date, note)
        self.entries[id] = entry
        return entry

    def retire(self, id: str, date: str, note: str = "") -> Entry:
        existing = self.entries.get(id)
        entry = Entry(id, id_kind(id) or "", "Retired", date, note)
        if existing and existing.note and not note:
            entry.note = existing.note
        self.entries[id] = entry
        return entry

    def save(self) -> None:
        rows = []
        for entry in sorted(self.entries.values(), key=lambda e: id_sort_key(e.id)):
            note = entry.note.replace("\n", " ").replace("|", "\\|")
            rows.append(f"| {entry.id} | {entry.kind} | {entry.state} | {entry.date} | {note} |\n")
        atomic_write(self.path, HEADER + "".join(rows))


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
