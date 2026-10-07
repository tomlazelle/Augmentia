// map.md generation: only the marker-delimited generated region is ever rewritten (port of sdlc/maps.py).

import fs from "node:fs";
import path from "node:path";
import { REF_SECTIONS } from "./markdown.js";
import { ARTIFACT_SUBDIRS, Diagnostic, GEN_END, GEN_START, cmpId, idSortKey } from "./model.js";
import { type Doc, type Project, scanDocuments } from "./project.js";
import { InvalidEncodingError, atomicWrite, cmpStr, cmpTuple, exists, isDir, isFile, pyStr, quote, readText, relpath, resolvePath, splitWs } from "./pyfmt.js";

const TOP: Record<string, [string, string, string | null]> = {
  BR: ["Business Requirements", "Business problem, objectives, stakeholders, scope and success measures.", "BR"],
  PR: ["Product Requirements", "Product capabilities, user expectations and release scope.", "PR"],
  Stories: ["User Stories", "User stories with observable acceptance criteria, traceable to requirements.", "US"],
  Artifacts: ["Artifacts", "Supporting design, planning, research and test artifacts.", null],
};
const SUB: Record<string, [string, string]> = {
  design: ["Design", "Technical design documents."],
  plans: ["Plans", "Implementation plans."],
  research: ["Research", "Research findings and supporting evidence."],
  tests: ["Tests", "Test plans and verification reports."],
};
const ROOT_SUMMARY = "Describe this project here. This text is hand-written and is never overwritten.";

export interface MapSpec { kind: "root" | "top" | "sub"; key: string; directory: string; title: string; purpose: string; category: string | null; path: string }

const mk = (kind: MapSpec["kind"], key: string, directory: string, title: string, purpose: string, category: string | null): MapSpec =>
  ({ kind, key, directory, title, purpose, category, path: path.join(directory, "map.md") });

export function specs(project: Project): MapSpec[] {
  const out = [mk("root", "root", project.root, project.name, ROOT_SUMMARY, null)];
  for (const [key, [title, purpose, cat]] of Object.entries(TOP)) out.push(mk("top", key, project.top(key), title, purpose, cat));
  const artifacts = project.top("Artifacts");
  for (const [sub, [title, purpose]] of Object.entries(SUB)) {
    if (isDir(path.join(artifacts, sub))) out.push(mk("sub", sub, path.join(artifacts, sub), title, purpose, ARTIFACT_SUBDIRS[sub]!));
  }
  return out;
}

const cell = (text: unknown): string => splitWs(pyStr(text)).join(" ").replaceAll("|", "\\|");

function link(label: string, target: string, fromDir: string): string {
  const rel = relpath(target, fromDir);
  const l = cell(label).replaceAll("[", "\\[").replaceAll("]", "\\]");
  return `[${l}](${quote(rel)})`;
}

function table(header: string[], rows: string[][]): string[] {
  return [`| ${header.join(" | ")} |`, "|" + header.map(() => "---").join("|") + "|", ...rows.map((r) => `| ${r.join(" | ")} |`)];
}

export function renderRegion(project: Project, spec: MapSpec, docs: Doc[]): string {
  let lines: string[] = [];
  if (spec.kind === "root") {
    const rows = Object.keys(TOP).map((k) => [link(TOP[k]![0], path.join(project.top(k), "map.md"), spec.directory), cell(TOP[k]![1])]);
    lines = ["## Directories", "", ...table(["Directory", "Purpose"], rows)];
  } else if (spec.key === "Artifacts") {
    const subs = specs(project).filter((s) => s.kind === "sub");
    lines = ["## Subdirectories", ""];
    if (subs.length) lines.push(...table(["Directory", "Purpose"], subs.map((s) => [link(`${s.key}/`, s.path, spec.directory), cell(s.purpose)])));
    else lines.push("_No artifact subdirectories yet. They are created on first use._");
  } else {
    const mine = docs.filter((d) => d.locCat === spec.category && d.valid && path.dirname(d.path) === spec.directory).sort((a, b) => cmpId(a.id, b.id));
    const story = spec.category === "US";
    const header = ["ID", "Document", "Purpose", "Status", ...(story ? ["Delivery"] : [])];
    lines.push("## Documents", "");
    if (mine.length) {
      const rows = mine.map((d) => {
        const row = [d.id, link(d.title, d.path, spec.directory), cell(d.meta["purpose"]), cell(d.meta["status"])];
        if (story) row.push(cell(d.meta["delivery_status"]));
        return row;
      });
      lines.push(...table(header, rows));
    } else lines.push("_No documents yet._");
    const relRows: { key: number[]; sec: number; label: string; row: string[] }[] = [];
    const byPath = new Map(docs.map((d) => [resolvePath(d.path), d]));
    for (const d of mine) {
      for (const section of REF_SECTIONS) {
        for (const ref of d.parsed.refs) {
          if (ref.section !== section || !ref.href) continue;
          const target = resolvePath(path.resolve(path.dirname(d.path), ref.href));
          if (!exists(target)) continue;
          const other = byPath.get(target);
          const label = other ? other.id : path.basename(target);
          relRows.push({ key: idSortKey(d.id), sec: REF_SECTIONS.indexOf(section), label, row: [link(d.id, d.path, spec.directory), section, link(label, target, spec.directory)] });
        }
      }
    }
    lines.push("", "## Relationships", "");
    if (relRows.length) {
      const seen = new Set<string>();
      const uniq: string[][] = [];
      for (const item of relRows.sort((a, b) => cmpTuple(a.key, b.key) || a.sec - b.sec || cmpStr(a.label, b.label))) {
        const k = item.row.join("\u0000");
        if (!seen.has(k)) { seen.add(k); uniq.push(item.row); }
      }
      lines.push(...table(["Source", "Relationship", "Target"], uniq));
    } else lines.push("_No relationships declared._");
  }
  return lines.join("\n");
}

export function buildNewMap(project: Project, spec: MapSpec, docs: Doc[]): string {
  const region = renderRegion(project, spec, docs);
  return `# ${spec.title}\n\n${spec.purpose}\n\n${GEN_START}\n${region}\n${GEN_END}\n\n## Open Questions\n\n- None yet.\n`;
}

/** (start, end) offsets of the text between the markers, or null if markers are absent/invalid. */
export function findRegion(text: string): [number, number] | null {
  const count = (needle: string) => text.split(needle).length - 1;
  if (count(GEN_START) !== 1 || count(GEN_END) !== 1) return null;
  const s = text.indexOf(GEN_START) + GEN_START.length;
  const e = text.indexOf(GEN_END);
  return s <= e ? [s, e] : null;
}

export function replaceRegion(text: string, region: string): string | null {
  const bounds = findRegion(text);
  if (bounds === null) return null;
  return text.slice(0, bounds[0]) + `\n${region}\n` + text.slice(bounds[1]);
}

export type MapAction = "created" | "updated" | "unchanged" | "blocked";

/** Create or refresh one map. */
export function syncMap(project: Project, spec: MapSpec, docs: Doc[]): [MapAction, Diagnostic | null] {
  const rel = project.rel(spec.path);
  if (!exists(spec.path)) {
    atomicWrite(spec.path, buildNewMap(project, spec, docs));
    return ["created", null];
  }
  let text: string;
  try { text = readText(spec.path); }
  catch (exc) { if (exc instanceof InvalidEncodingError) return ["blocked", new Diagnostic("error", "invalid-encoding", `${exc.message}; not modified`, rel)]; throw exc; }
  const next = replaceRegion(text, renderRegion(project, spec, docs));
  if (next === null) {
    return ["blocked", new Diagnostic("error", "map-markers", `map has missing or duplicated generated-region markers (${GEN_START} ... ${GEN_END}); not modified`, rel)];
  }
  if (next === text) return ["unchanged", null];
  atomicWrite(spec.path, next);
  return ["updated", null];
}

export function updateMaps(project: Project, only: MapSpec | null = null): [Record<string, string[]>, Diagnostic[]] {
  const [docs] = scanDocuments(project);
  const result: Record<string, string[]> = { created: [], updated: [], unchanged: [], blocked: [] };
  const diags: Diagnostic[] = [];
  for (const spec of only ? [only] : specs(project)) {
    const [action, diag] = syncMap(project, spec, docs);
    result[action]!.push(project.rel(spec.path));
    if (diag) diags.push(diag);
  }
  return [result, diags];
}

/** Validation view: missing maps, unusable markers, stale generated regions. */
export function checkMaps(project: Project, docs: Doc[]): Diagnostic[] {
  const diags: Diagnostic[] = [];
  for (const spec of specs(project)) {
    const rel = project.rel(spec.path);
    if (!isDir(spec.directory)) continue;
    if (!isFile(spec.path)) { diags.push(new Diagnostic("error", "missing-map", "directory has no map.md", rel)); continue; }
    let text: string;
    try { text = readText(spec.path); }
    catch (exc) { if (exc instanceof InvalidEncodingError) { diags.push(new Diagnostic("error", "invalid-encoding", exc.message, rel)); continue; } throw exc; }
    const bounds = findRegion(text);
    if (bounds === null) { diags.push(new Diagnostic("error", "map-markers", "map is missing its generated-region markers", rel)); continue; }
    const strip = (s: string) => s.replace(/^[\s]+|[\s]+$/g, "");
    if (strip(text.slice(bounds[0], bounds[1])) !== strip(renderRegion(project, spec, docs))) {
      diags.push(new Diagnostic("error", "stale-map", "generated region is out of date; run 'sdlc update-map'", rel));
    }
  }
  return diags;
}

export { fs };
