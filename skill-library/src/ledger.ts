// CLI-maintained ID ledger (.sdlc/ledger.md): a Markdown table of allocated/retired IDs (port of sdlc/ledger.py).

import { Diagnostic, cmpId, idKind } from "./model.js";
import { InvalidEncodingError, WS, atomicWrite, isFile, readText, repr, strip } from "./pyfmt.js";

export const LEDGER_REL = ".sdlc/ledger.md";
const HEADER = `# ID Ledger

Maintained by the \`sdlc\` CLI. Do not edit by hand.
Allocated and retired IDs are recorded here so IDs are never reused within a checkout.

| ID | Kind | State | Date | Note |
|---|---|---|---|---|
`;
const SPLIT = /(?<!\\)\|/;
const STATES = ["Allocated", "Retired"];
const KINDS = ["document", "requirement"];

const REPLACED_RE = new RegExp(`^Replaced by ([^${WS}]+?)\\.?(?:[${WS}]|$)`);

/** Entry.replaced_by: the ID named by a "Replaced by X." note, if any. */
export const replacedBy = (entry: { note: string }): string | null => REPLACED_RE.exec(entry.note)?.[1] ?? null;

export interface Entry { id: string; kind: string; state: string; date: string; note: string }

export class Ledger {
  entries = new Map<string, Entry>();
  constructor(public path: string) {}

  static load(file: string): [Ledger, Diagnostic[]] {
    const ledger = new Ledger(file);
    const diags: Diagnostic[] = [];
    if (!isFile(file)) return [ledger, [new Diagnostic("error", "missing-ledger", "ledger file is missing", LEDGER_REL)]];
    let inTable = false;
    let content: string;
    try { content = readText(file); }
    catch (exc) { if (exc instanceof InvalidEncodingError) return [ledger, [new Diagnostic("error", "invalid-encoding", exc.message, LEDGER_REL)]]; throw exc; }
    const lines = content.split("\n");
    for (let i = 0; i < lines.length; i++) {
      const lineno = i + 1;
      const line = lines[i]!;
      if (!line.startsWith("|")) continue;
      const cells = strip(line).split(SPLIT).slice(1, -1).map((c) => strip(c).replaceAll("\\|", "|"));
      if (cells.length > 0 && cells[0] === "ID") { inTable = true; continue; }
      if (!inTable || cells.every((c) => [...c].every((ch) => "-: ".includes(ch)))) continue;
      const bad = (msg: string) => diags.push(new Diagnostic("error", "bad-ledger-row", msg, LEDGER_REL, null, lineno));
      if (cells.length !== 5) { bad("row must have 5 columns: ID, Kind, State, Date, Note"); continue; }
      const [id, kind, state, date, note] = cells as [string, string, string, string, string];
      const entry: Entry = { id, kind, state, date, note };
      if (idKind(id) === null) bad(`${reprId(id)} is not a valid ID`);
      else if (kind !== idKind(id) || !KINDS.includes(kind)) bad(`kind ${reprId(kind)} does not match ID ${id}`);
      else if (!STATES.includes(state)) bad(`state ${reprId(state)} must be Allocated or Retired`);
      else if (ledger.entries.has(id)) diags.push(new Diagnostic("error", "duplicate-ledger-id", `${id} appears more than once in the ledger`, LEDGER_REL, id, lineno));
      else ledger.entries.set(id, entry);
    }
    if (!inTable) diags.push(new Diagnostic("error", "bad-ledger", "ledger table header not found", LEDGER_REL));
    return [ledger, diags];
  }

  add(id: string, date: string, note = ""): Entry {
    const entry: Entry = { id, kind: idKind(id) ?? "", state: "Allocated", date, note };
    this.entries.set(id, entry);
    return entry;
  }

  retire(id: string, date: string, note = ""): Entry {
    const existing = this.entries.get(id);
    const entry: Entry = { id, kind: idKind(id) ?? "", state: "Retired", date, note };
    if (existing && existing.note && !note) entry.note = existing.note;
    this.entries.set(id, entry);
    return entry;
  }

  save(): void {
    const rows = [...this.entries.values()].sort((a, b) => cmpId(a.id, b.id)).map((e) => {
      const note = e.note.replaceAll("\n", " ").replaceAll("|", "\\|");
      return `| ${e.id} | ${e.kind} | ${e.state} | ${e.date} | ${note} |\n`;
    });
    atomicWrite(this.path, HEADER + rows.join(""));
  }
}

const reprId = (s: string): string => repr(s);
