// `validate`: structural errors, warnings, and coverage notices (port of sdlc/validate.py).

import path from "node:path";
import { LEDGER_REL, Ledger, replacedBy } from "./ledger.js";
import { checkMaps, specs } from "./maps.js";
import { extractHrefs, maskRegion } from "./markdown.js";
import { GEN_END, GEN_START, TOP_DIRS, Diagnostic, Outcome, cmpId, ownerOf } from "./model.js";
import * as publication from "./publication.js";
import { type Doc, type Project, loadConfig, scanDocuments } from "./project.js";
import { InvalidEncodingError, cmpTuple, exists, isDir, isFile, readText, resolvePath, sortedStrings } from "./pyfmt.js";
import * as technical from "./technical.js";

function dupDiags(groups: Map<string, Doc[]>, code: string, what: string): Diagnostic[] {
  const out: Diagnostic[] = [];
  for (const [ident, group] of groups) {
    const paths = sortedStrings(new Set(group.map((d) => d.rel)));
    if (paths.length < 2 && group.length < 2) continue;
    for (const d of group) {
      let others = paths.filter((p) => p !== d.rel);
      if (others.length === 0) others = ["(declared more than once in this file)"];
      out.push(new Diagnostic("error", code, `${what} ${ident} is also used by: ${others.join(", ")}`, d.rel, ident));
    }
  }
  return out;
}

function checkLinks(project: Project, docs: Doc[]): Diagnostic[] {
  const diags: Diagnostic[] = [];
  for (const doc of docs) {
    for (const [lineno, href] of doc.parsed.links) {
      if (!exists(path.resolve(path.dirname(doc.path), href))) diags.push(new Diagnostic("error", "broken-link", `link target does not exist: ${href}`, doc.rel, doc.id, lineno));
    }
  }
  for (const spec of specs(project)) {
    if (!isFile(spec.path)) continue;
    let mapText: string;
    try { mapText = readText(spec.path); } catch (exc) { if (exc instanceof InvalidEncodingError) continue; throw exc; } // reported by the map check
    const text = maskRegion(mapText, GEN_START, GEN_END);
    text.split("\n").forEach((line, i) => {
      for (const href of extractHrefs(line)) {
        if (!exists(path.resolve(path.dirname(spec.path), href))) diags.push(new Diagnostic("error", "broken-link", `link target does not exist: ${href}`, project.rel(spec.path), null, i + 1));
      }
    });
  }
  return diags;
}

function pushTo<K, V>(map: Map<K, V[]>, key: K, value: V): void {
  const list = map.get(key);
  if (list) list.push(value); else map.set(key, [value]);
}

function retiredRef(ledger: Ledger, rid: string, doc: Doc, line: number | null): Diagnostic {
  const repl = replacedBy(ledger.entries.get(rid)!);
  const hint = repl ? `; replaced by ${repl}` : "";
  return new Diagnostic("error", "retired-reference", `references retired requirement ${rid}${hint}`, doc.rel, rid, line);
}

export function validate(project: Project): Outcome {
  const diags: Diagnostic[] = [];
  const root = project.root;

  const [, cfgDiags] = loadConfig(root);
  diags.push(...cfgDiags);
  const [ledger, ledgerDiags] = Ledger.load(path.join(root, LEDGER_REL));
  diags.push(...ledgerDiags);

  for (const key of TOP_DIRS) {
    const directory = project.top(key);
    if (!isDir(directory)) diags.push(new Diagnostic("error", "missing-directory", "required directory is missing", project.rel(directory)));
  }
  if (!isFile(path.join(root, "map.md"))) diags.push(new Diagnostic("error", "missing-map", "root map.md is missing", "map.md"));
  if (isDir(project.top("Artifacts"))) {
    for (const spec of specs(project)) {
      if (spec.kind === "sub" && !isFile(spec.path)) diags.push(new Diagnostic("error", "missing-map", "directory has no map.md", project.rel(spec.path)));
    }
  }
  // (`.sdlc/` is deliberately exempt from map and authored-document rules.)

  const [docs, scanDiags] = scanDocuments(project);
  diags.push(...scanDiags);
  for (const doc of docs) diags.push(...doc.diags);

  const byName = new Map<string, Doc[]>();
  const byMeta = new Map<string, Doc[]>();
  for (const doc of docs) {
    if (doc.nameId) pushTo(byName, doc.nameId, doc);
    const metaId = doc.meta["id"];
    if (typeof metaId === "string") pushTo(byMeta, metaId, doc);
  }
  const dupDocs = new Map<string, Doc[]>();
  for (const [i, g] of byName) if (g.length > 1) dupDocs.set(i, g);
  for (const [i, g] of byMeta) if (g.length > 1 && !dupDocs.has(i)) dupDocs.set(i, g);
  diags.push(...dupDiags(dupDocs, "duplicate-id", "document ID"));

  const reqDecls = new Map<string, Doc[]>();
  for (const doc of docs) for (const req of doc.parsed.requirements) pushTo(reqDecls, req.id, doc);
  const dupReqs = new Map<string, Doc[]>();
  for (const [i, g] of reqDecls) if (g.length > 1) dupReqs.set(i, g);
  diags.push(...dupDiags(dupReqs, "duplicate-requirement", "requirement ID"));

  // Ledger vs disk
  const ledgerOk = !ledgerDiags.some((d) => d.severity === "error");
  const docIdsOnDisk = new Set([...byName.keys(), ...byMeta.keys()]);
  const retired = new Set([...ledger.entries].filter(([, e]) => e.state === "Retired").map(([i]) => i));
  if (ledgerOk) {
    for (const ident of [...docIdsOnDisk].filter((i) => retired.has(i)).sort(cmpId)) {
      const group = byName.get(ident)?.length ? byName.get(ident)! : (byMeta.get(ident) ?? []);
      for (const d of group) diags.push(new Diagnostic("error", "retired-id-in-use", `${ident} is retired in the ledger but a document still uses it`, d.rel, ident));
    }
    for (const ident of [...reqDecls.keys()].filter((i) => retired.has(i)).sort(cmpId)) {
      for (const d of reqDecls.get(ident)!) {
        const line = d.parsed.requirements.find((r) => r.id === ident)!;
        if (!line.text.toLowerCase().includes("retired")) {
          diags.push(new Diagnostic("error", "retired-id-in-use", `${ident} is retired in the ledger; mark its text *Retired* or remove it`, d.rel, ident, line.line));
        }
      }
    }
    for (const ident of [...new Set([...docIdsOnDisk, ...reqDecls.keys()])].sort(cmpId)) {
      if (!ledger.entries.has(ident)) {
        const paths = byName.get(ident)?.length ? byName.get(ident)! : byMeta.get(ident)?.length ? byMeta.get(ident)! : (reqDecls.get(ident) ?? []);
        diags.push(new Diagnostic("warning", "not-in-ledger", "ID is not recorded in the ledger", paths.length ? paths[0]!.rel : null, ident));
      }
    }
    for (const [ident, entry] of [...ledger.entries].sort((a, b) => cmpId(a[0], b[0]))) {
      if (entry.state === "Allocated" && !docIdsOnDisk.has(ident) && !reqDecls.has(ident)) {
        diags.push(new Diagnostic("warning", "allocated-not-found", "allocated in the ledger but nothing on disk uses it; retire it if it was deleted", LEDGER_REL, ident));
      }
    }
  }

  // Links, references and traceability
  diags.push(...checkLinks(project, docs));
  const knownReqs = new Set(reqDecls.keys());
  const byPath = new Map(docs.map((d) => [resolvePath(d.path), d] as [string, Doc]));
  for (const doc of docs) {
    for (const ref of doc.parsed.refs) {
      for (const rid of ref.reqIds) {
        if (retired.has(rid)) diags.push(retiredRef(ledger, rid, doc, ref.line));
        else if (!knownReqs.has(rid)) diags.push(new Diagnostic("error", "unknown-requirement", `referenced requirement ${rid} does not exist`, doc.rel, rid, ref.line));
      }
    }
    if (doc.isStory) {
      const linked = new Set<string>();
      for (const r of doc.parsed.refs) {
        if (r.section === "Derived From" && r.href) {
          const t = resolvePath(path.resolve(path.dirname(doc.path), r.href));
          const hit = byPath.get(t);
          if (hit) linked.add(hit.id);
        }
      }
      for (const rid of doc.covers) {
        if (retired.has(rid)) diags.push(retiredRef(ledger, rid, doc, null));
        else if (!knownReqs.has(rid)) diags.push(new Diagnostic("error", "covers-unknown", `covers ${rid}, which does not exist`, doc.rel, rid));
        else if (!linked.has(ownerOf(rid))) diags.push(new Diagnostic("error", "covers-source-not-linked", `covers ${rid} but does not link ${ownerOf(rid)} under 'Derived From'`, doc.rel, rid));
      }
    }
  }

  diags.push(...checkTechnical(docs));
  diags.push(...checkMaps(project, docs));

  // Coverage notices (informational)
  const stories = docs.filter((d) => d.isStory && d.valid);
  const covered = new Set(stories.flatMap((s) => s.covers));
  for (const s of [...stories].sort((a, b) => cmpId(a.id, b.id))) {
    if (s.covers.length === 0) diags.push(new Diagnostic("notice", "story-no-coverage", "standalone Story: covers is empty", s.rel, s.id));
  }
  // R1: only PR requirements are expected to be covered by Stories (BR requirements are covered via PRDs).
  for (const rid of [...knownReqs].filter((r) => !retired.has(r)).sort(cmpId)) {
    if (ownerOf(rid).startsWith("PR-") && !covered.has(rid)) diags.push(new Diagnostic("notice", "requirement-uncovered", "no Story covers this requirement", reqDecls.get(rid)![0]!.rel, rid));
  }

  const rank = { error: 0, warning: 1, notice: 2 } as const;
  diags.sort((a, b) => cmpTuple([rank[a.severity], a.path ?? "", a.line ?? 0, a.code, a.id ?? ""], [rank[b.severity], b.path ?? "", b.line ?? 0, b.code, b.id ?? ""]));
  const counts = { error: 0, warning: 0, notice: 0 };
  for (const d of diags) counts[d.severity]++;
  return new Outcome(counts.error ? 1 : 0, { summary: counts, documents: docs.length }, diags);
}

/** R2 evidence rules: Story Implementation Records, TEST Verification Runs, and what `Verified` requires. */
function checkTechnical(docs: Doc[]): Diagnostic[] {
  const diags: Diagnostic[] = [];
  const stories = new Map<string, Doc>();
  for (const d of docs) if (d.isStory) stories.set(d.id, d);
  const secs = new Map<string, technical.Section[]>();
  const acCount = new Map<string, number | null>();
  for (const [sid, d] of stories) { const s = technical.sections(d.text); secs.set(sid, s); acCount.set(sid, technical.acceptanceCriteriaCount(s)); }

  const runs: [technical.Rec, string][] = [];
  for (const doc of docs) {
    if (doc.category === "TEST" && doc.valid) {
      const [recs, d] = technical.checkVerificationRuns(doc.rel, doc.id, technical.sections(doc.text), acCount);
      diags.push(...d);
      for (const r of recs) runs.push([r, doc.rel]);
    }
  }

  for (const [sid, doc] of stories) {
    if (!doc.valid) continue;
    const status = doc.meta["delivery_status"];
    const [recs, d] = technical.checkImplementationRecords(doc.rel, sid, secs.get(sid)!);
    diags.push(...d);
    diags.push(...publication.parse(doc.rel, sid, secs.get(sid)!)[1]);
    const n = acCount.get(sid)!;
    if ((status === "Implemented" || status === "Verified") && recs.length === 0) {
      diags.push(new Diagnostic("error", "implementation-record-missing", `delivery_status ${status} requires an '## Implementation Record' entry (### IR-n — date)`, doc.rel, sid));
    }
    if ((status === "Ready" || status === "In Progress" || status === "Implemented") && n === 0) {
      diags.push(new Diagnostic("warning", "ready-without-criteria", `delivery_status ${status} but the Story has no numbered acceptance criteria`, doc.rel, sid));
    }
    if (status !== "Verified") continue;
    if (n === 0) {
      diags.push(new Diagnostic("error", "verified-no-criteria", "Verified Story has no numbered acceptance criteria to verify", doc.rel, sid));
      continue;
    }
    const mine = runs
      .filter(([r]) => (r.fields["story"] ?? "").trim() === sid && !technical.isSuperseded(r))
      .sort((a, b) => cmpTuple([a[0].stamp, a[1], a[0].order], [b[0].stamp, b[1], b[0].order]));
    const problems: string[] = [];
    for (let ac = 1; ac <= n; ac++) {
      const latest = [...mine].reverse().find(([r]) => technical.criteriaOf(r).includes(ac));
      if (!latest) problems.push(`AC-${ac} (no current run)`);
      else if ((latest[0].fields["result"] ?? "").trim() !== "passed") problems.push(`AC-${ac} (latest run ${latest[0].id} in ${latest[1]} is ${(latest[0].fields["result"] ?? "?").trim()})`);
    }
    if (problems.length) {
      diags.push(new Diagnostic("error", "verified-criteria-unproven",
        `delivery_status Verified requires a current, passed verification run for every acceptance criterion; missing: ${problems.join("; ")}`, doc.rel, sid));
    }
    if (technical.unresolvedTbdBullets(secs.get(sid)!)) {
      diags.push(new Diagnostic("warning", "verified-with-unresolved-tbd", "Verified Story still lists unresolved acceptance behavior (TBD); Verified covers only the decided criteria", doc.rel, sid));
    }
  }
  return diags;
}
