// Read-only discovery: list, references, find-overlaps (port of sdlc/query.py).

import path from "node:path";
import { LEDGER_REL, Ledger, replacedBy } from "./ledger.js";
import { DOC_ID_RE, Diagnostic, Outcome, REQ_ID_RE, cmpId, idKind, idSortKey, ownerOf } from "./model.js";
import { type Doc, type Project, scanDocuments } from "./project.js";
import { cmpStr, cmpTuple, fixed, pyRound, pyStr, repr, resolvePath, sortedStrings } from "./pyfmt.js";

// --- find-overlaps scoring (documented in shared/cli-contract.md) ---------------------------------
const STOPWORDS = new Set(["a", "an", "the", "of", "for", "and", "to", "in", "on", "with", "or"]);
const WEIGHTS = { title: 0.5, purpose: 0.3, refs: 0.2 } as const;
const LIKELY = 0.75;
const POSSIBLE = 0.4;

export function tokens(text: string): Set<string> {
  const out = new Set<string>();
  for (const m of text.toLowerCase().matchAll(/[a-z0-9]+/g)) {
    let word = m[0];
    if (STOPWORDS.has(word)) continue;
    if (word.length > 3 && word.endsWith("s") && !word.endsWith("ss")) word = word.slice(0, -1);
    out.add(word);
  }
  return out;
}

export function jaccard(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0.0;
  let inter = 0;
  for (const x of a) if (b.has(x)) inter++;
  return inter / (a.size + b.size - inter);
}

/** The weighted mean of the signals supplied (weights renormalised over the supplied signals), as in the oracle. */
export function overlapScore(titleScore: number, purposeScore: number, refsScore: number, hasPurpose: boolean, hasRefs: boolean): number {
  let totalWeight = 0;
  for (const [k, on] of [["title", true], ["purpose", hasPurpose], ["refs", hasRefs]] as const) if (on) totalWeight += WEIGHTS[k];
  return (titleScore * WEIGHTS.title + purposeScore * WEIGHTS.purpose * (hasPurpose ? 1 : 0) + refsScore * WEIGHTS.refs * (hasRefs ? 1 : 0)) / totalWeight;
}

export function docRow(doc: Doc): Record<string, unknown> {
  const row: Record<string, unknown> = { id: doc.id, title: doc.title, category: doc.category, status: doc.meta["status"] ?? null, path: doc.rel, purpose: doc.meta["purpose"] ?? null };
  if (doc.isStory) row["delivery_status"] = doc.meta["delivery_status"] ?? null;
  return row;
}

export function listDocuments(project: Project, category: string | null, status: string | null): Outcome {
  const [docs, diags] = scanDocuments(project);
  const rows: Record<string, unknown>[] = [];
  for (const doc of [...docs].sort((a, b) => cmpId(a.id, b.id))) {
    if (!doc.valid) {
      diags.push(new Diagnostic("warning", "skipped-invalid", "document has metadata errors and is not listed; run validate", doc.rel, doc.id));
      continue;
    }
    if (category && doc.category !== category) continue;
    if (status && doc.meta["status"] !== status) continue;
    rows.push(docRow(doc));
  }
  return new Outcome(0, { count: rows.length, documents: rows }, diags);
}

type Item = { relationship: string; requirements: string[]; href?: string | null; target?: { id: string | null; path: string } | null; source?: { id: string; path: string } };

export function references(project: Project, target: string): Outcome {
  const kind = idKind(target);
  if (kind === null) return new Outcome(2, {}, [new Diagnostic("error", "bad-id", `${repr(target)} is not a valid document or requirement ID`)]);
  const [docs, diags] = scanDocuments(project);
  const [ledger, ledgerDiags] = Ledger.load(path.join(project.root, LEDGER_REL));
  const unreadable = ledgerDiags.filter((d) => d.code === "invalid-encoding");
  if (unreadable.length) return new Outcome(1, {}, unreadable);
  const reqs = new Map<string, Doc>();
  for (const d of docs) for (const r of d.parsed.requirements) reqs.set(r.id, d);
  const byId = new Map<string, Doc>();
  for (const d of docs) byId.set(d.id, d);
  const byPath = new Map<string, Doc>();
  for (const d of docs) byPath.set(resolvePath(d.path), d);
  const entry = ledger.entries.get(target);
  const doc = kind === "document" ? byId.get(target) : undefined;
  const definedIn = kind === "requirement" ? reqs.get(target) : undefined;
  if (doc === undefined && definedIn === undefined && entry === undefined) {
    return new Outcome(1, {}, [new Diagnostic("error", "unknown-id", `${target} not found`, null, target)]);
  }
  const result: Record<string, unknown> = { id: target, kind, state: entry ? entry.state : "Present" };
  const outgoing: Item[] = [];
  const incoming: Item[] = [];
  const link = (d: Doc, href: string): string => resolvePath(path.resolve(path.dirname(d.path), href));

  if (doc !== undefined) {
    result["title"] = doc.title;
    result["path"] = doc.rel;
    for (const ref of doc.parsed.refs) {
      const item: Item = { relationship: ref.section, requirements: ref.reqIds, href: ref.href, target: null };
      if (ref.href) {
        const other = byPath.get(link(doc, ref.href));
        item.target = other ? { id: other.id, path: other.rel } : { id: null, path: ref.href };
      }
      outgoing.push(item);
    }
    if (doc.covers.length) outgoing.push({ relationship: "Covers", requirements: doc.covers, href: null, target: null });
    const mine = new Set(doc.parsed.requirements.map((r) => r.id));
    for (const other of docs) {
      if (other === doc) continue;
      for (const ref of other.parsed.refs) {
        const linked = !!ref.href && link(other, ref.href) === resolvePath(doc.path);
        const shared = sortedStrings(ref.reqIds.filter((x) => mine.has(x)).filter((x, i, a) => a.indexOf(x) === i));
        if (linked || shared.length) incoming.push({ relationship: ref.section, requirements: shared, source: { id: other.id, path: other.rel } });
      }
      const covered = sortedStrings([...new Set(other.covers)].filter((x) => mine.has(x)));
      if (covered.length) incoming.push({ relationship: "Covers", requirements: covered, source: { id: other.id, path: other.rel } });
    }
  } else {
    result["defined_in"] = definedIn !== undefined ? { id: definedIn.id, path: definedIn.rel, title: definedIn.title } : null;
    if (entry && replacedBy(entry)) result["replaced_by"] = replacedBy(entry);
    for (const other of docs) {
      if (other.covers.includes(target)) incoming.push({ relationship: "Covers", requirements: [target], source: { id: other.id, path: other.rel } });
      for (const ref of other.parsed.refs) {
        if (ref.reqIds.includes(target)) incoming.push({ relationship: ref.section, requirements: [target], source: { id: other.id, path: other.rel } });
      }
    }
  }
  const key = (x: Item): string[] => [x.relationship, x.source?.id || "", String(x.href || "")];
  const cmp = (a: Item, b: Item) => cmpTuple(key(a), key(b));
  result["outgoing"] = [...outgoing].sort(cmp);
  result["incoming"] = [...incoming].sort(cmp);
  return new Outcome(0, result, diags);
}

/** Requirement and source-document IDs a document is tied to (for overlap matching). */
function refIds(doc: Doc): Set<string> {
  const ids = new Set(doc.covers);
  const byPathIds = new Set<string>();
  for (const ref of doc.parsed.refs) {
    for (const r of ref.reqIds) ids.add(r);
    if (ref.href && ref.section === "Derived From") {
      const m = /^((?:BR|PR|US|DES|PLAN|RES|TEST)-[0-9]{3,})-/.exec(ref.href.slice(ref.href.lastIndexOf("/") + 1));
      if (m) byPathIds.add(m[1]!);
    }
  }
  return new Set([...ids, ...byPathIds]);
}

export function findOverlaps(project: Project, category: string, title: string, purpose: string | null, covers: string[]): Outcome {
  for (const value of covers) {
    if (idKind(value) === null) return new Outcome(2, {}, [new Diagnostic("error", "bad-id", `--covers value ${repr(value)} is not a valid ID`)]);
  }
  const [docs, diags] = scanDocuments(project);
  const wantTitle = tokens(title);
  const wantPurpose = purpose ? tokens(purpose) : new Set<string>();
  const wantRefs = new Set(covers);
  const signals = { title: true, purpose: wantPurpose.size > 0, refs: wantRefs.size > 0 };
  const candidates: Record<string, unknown>[] = [];
  const same = (a: Set<string>, b: Set<string>) => a.size === b.size && [...a].every((x) => b.has(x));
  for (const doc of docs) {
    if (!doc.valid || doc.category !== category || doc.meta["status"] === "Superseded") continue;
    const reasons: string[] = [];
    const titleScore = same(tokens(doc.title), wantTitle) && wantTitle.size > 0 ? 1.0 : jaccard(wantTitle, tokens(doc.title));
    if (titleScore === 1.0) reasons.push("same normalized title");
    else if (titleScore > 0) reasons.push(`title similarity ${fixed(titleScore, 2)}`);
    const purposeScore = signals.purpose ? jaccard(wantPurpose, tokens(pyStrPurpose(doc.meta["purpose"]))) : 0.0;
    if (purposeScore > 0) reasons.push(`purpose similarity ${fixed(purposeScore, 2)}`);
    let refsScore = 0.0;
    if (signals.refs) {
      const have = refIds(doc);
      const haveOwners = new Set([...have].filter((i) => REQ_ID_RE.test(i)).map(ownerOf));
      const shared = sortedStrings([...wantRefs].filter((i) => have.has(i) || (DOC_ID_RE.test(i) && haveOwners.has(i))));
      refsScore = shared.length / wantRefs.size;
      if (shared.length) reasons.push(`shares references: ${shared.join(", ")}`);
    }
    let score = overlapScore(titleScore, purposeScore, refsScore, signals.purpose, signals.refs);
    if (titleScore === 1.0) score = Math.max(score, LIKELY);
    if (score < POSSIBLE) continue;
    const level = score >= LIKELY ? "likely" : "possible";
    candidates.push({ ...docRow(doc), score: pyRound(score, 3), level, reasons });
  }
  candidates.sort((a, b) => ((b["score"] as number) - (a["score"] as number)) || cmpTuple(idSortKey(a["id"] as string), idSortKey(b["id"] as string)));
  return new Outcome(0, { category, title, candidates, action: candidates.length ? "ask-human" : "none" }, diags);
}

const pyStrPurpose = (v: unknown): string => (typeof v === "string" ? v : v === undefined ? "" : pyStr(v));
export { cmpStr };
