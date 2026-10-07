// ID allocation and retirement against the ledger and on-disk documents (port of sdlc/ids.py).

import { LEDGER_REL, Ledger } from "./ledger.js";
import { DOC_ID_RE, Diagnostic, Outcome, categoryOf, formatDocId, idKind, slugify } from "./model.js";
import { type Project, scanDocuments } from "./project.js";
import { repr, strip, today } from "./pyfmt.js";
import path from "node:path";

function loadLedger(project: Project): [Ledger | null, Diagnostic[]] {
  const [ledger, diags] = Ledger.load(path.join(project.root, LEDGER_REL));
  return [diags.some((d) => d.severity === "error") ? null : ledger, diags];
}

function diskDocIds(project: Project): Set<string> {
  const [docs] = scanDocuments(project);
  const ids = new Set<string>();
  for (const doc of docs) {
    if (doc.nameId) ids.add(doc.nameId);
    const metaId = doc.meta["id"];
    if (typeof metaId === "string" && DOC_ID_RE.test(metaId)) ids.add(metaId);
  }
  return ids;
}

export function allocateDocument(project: Project, category: string, title: string | null): Outcome {
  const [ledger, diags] = loadLedger(project);
  if (ledger === null) return new Outcome(1, {}, diags);
  let slug: string | null = null;
  if (title !== null) {
    slug = slugify(title);
    if (!slug) return new Outcome(2, {}, [new Diagnostic("error", "bad-title", "title has no usable letters or digits")]);
  }
  const numbers = [...ledger.entries.keys(), ...diskDocIds(project)]
    .filter((i) => DOC_ID_RE.test(i) && categoryOf(i) === category)
    .map((i) => parseInt(i.split("-")[1]!, 10));
  const newId = formatDocId(category, Math.max(0, ...numbers) + 1);
  ledger.add(newId, today());
  ledger.save();
  const dir = project.categoryDir(category);
  const p = slug ? project.rel(path.join(dir, `${newId}-${slug}.md`)) : null;
  return new Outcome(0, { id: newId, kind: "document", category, directory: project.rel(dir), path: p }, diags);
}

const reEscape = (s: string): string => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function allocateRequirement(project: Project, docId: string): Outcome {
  if (!DOC_ID_RE.test(docId)) return new Outcome(2, {}, [new Diagnostic("error", "bad-id", `${repr(docId)} is not a valid document ID`)]);
  const [ledger, diags] = loadLedger(project);
  if (ledger === null) return new Outcome(1, {}, diags);
  const entry = ledger.entries.get(docId);
  const [docs] = scanDocuments(project);
  const docFiles = docs.filter((d) => d.id === docId);
  if (entry !== undefined && entry.state === "Retired") return new Outcome(1, {}, [new Diagnostic("error", "retired-id", `${docId} is retired`, null, docId)]);
  if (entry === undefined && docFiles.length === 0) return new Outcome(1, {}, [new Diagnostic("error", "unknown-id", `${docId} is not in the ledger or on disk`, null, docId)]);
  const pattern = new RegExp(`^${reEscape(docId)}-R(\\d+)$`);
  const numbers: number[] = [];
  for (const id of ledger.entries.keys()) { const m = pattern.exec(id); if (m) numbers.push(parseInt(m[1]!, 10)); }
  for (const d of docFiles) for (const r of d.parsed.requirements) { const m = pattern.exec(r.id); if (m) numbers.push(parseInt(m[1]!, 10)); }
  const newId = `${docId}-R${String(Math.max(0, ...numbers) + 1).padStart(3, "0")}`;
  ledger.add(newId, today());
  ledger.save();
  return new Outcome(0, { id: newId, kind: "requirement", document: docId }, diags);
}

export function retire(project: Project, target: string, replacedBy: string | null, note: string | null): Outcome {
  const kind = idKind(target);
  if (kind === null) return new Outcome(2, {}, [new Diagnostic("error", "bad-id", `${repr(target)} is not a valid document or requirement ID`)]);
  if (replacedBy !== null && idKind(replacedBy) !== kind) {
    return new Outcome(2, {}, [new Diagnostic("error", "bad-replacement", `--replaced-by must be a ${kind} ID, got ${repr(replacedBy)}`)]);
  }
  if (replacedBy === target) return new Outcome(2, {}, [new Diagnostic("error", "bad-replacement", "an ID cannot replace itself", null, target)]);
  const [ledger, diags] = loadLedger(project);
  if (ledger === null) return new Outcome(1, {}, diags);
  const [docs] = scanDocuments(project);
  const onDisk = kind === "document" ? diskDocIds(project).has(target) : docs.some((d) => d.parsed.requirements.some((r) => r.id === target));
  const existing = ledger.entries.get(target);
  if (existing === undefined && !onDisk) return new Outcome(1, {}, [new Diagnostic("error", "unknown-id", `${target} is not in the ledger or on disk`, null, target)]);
  if (existing !== undefined && existing.state === "Retired") return new Outcome(1, {}, [new Diagnostic("error", "already-retired", `${target} is already retired`, null, target)]);
  let text = replacedBy ? `Replaced by ${replacedBy}.` : "";
  if (note) text = strip(`${text} ${note}`);
  ledger.retire(target, today(), text);
  ledger.save();
  const out = [...diags];
  if (kind === "document" && onDisk) {
    out.push(new Diagnostic("warning", "retired-still-present", `${target} still has a document on disk; validate reports this until it is removed`, null, target));
  }
  return new Outcome(0, { id: target, kind, state: "Retired", replaced_by: replacedBy, note: text }, out);
}
