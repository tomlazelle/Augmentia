// Project root discovery, .sdlc/config.md, and authored-document loading (port of sdlc/project.py).

import fs from "node:fs";
import path from "node:path";
import * as frontmatter from "./frontmatter.js";
import { type ParsedBody, parseBody } from "./markdown.js";
import {
  ARTIFACT_SUBDIRS, CATEGORY_LOCATION, DELIVERY_STATUSES, DOC_ID_RE, DOC_STATUSES, Diagnostic, FILENAME_RE, REQ_ID_RE, TOP_DIRS,
  categoryOf, type Severity,
} from "./model.js";
import { InvalidEncodingError, cmpStr, isDir, isRealDate, pyStr, readText, repr, resolvePath, sortedStrings, strip } from "./pyfmt.js";
import { PyDateTime, type PyValue } from "./yaml.js";

export const SCHEMA_VERSION = 1;
export const DEFAULT_DIRECTORIES: Record<string, string> = Object.fromEntries(TOP_DIRS.map((k) => [k, k]));
const REQUIRED_FIELDS = ["id", "title", "purpose", "status", "created", "updated"];
export const EVIDENCE_DIR = "evidence";
const CREDENTIAL_KEY_RE = /token|secret|password|passwd|credential|auth|api[_-]?key/i;

export type Meta = Record<string, PyValue>;
const isDict = (v: unknown): v is Record<string, PyValue> => typeof v === "object" && v !== null && !Array.isArray(v) && Object.getPrototypeOf(v) === Object.prototype;
const blank = (v: unknown): boolean => v === null || v === undefined || v === "";

export function findRoot(start: string): string | null {
  let cur = start;
  for (;;) {
    if (isDir(path.join(cur, ".sdlc"))) return cur;
    const parent = path.dirname(cur);
    if (parent === cur) return null;
    cur = parent;
  }
}

/** Load and validate the minimal .sdlc/config.md schema. */
export function loadConfig(root: string): [Meta | null, Diagnostic[]] {
  const rel = ".sdlc/config.md";
  const file = path.join(root, rel);
  let isF = false;
  try { isF = fs.statSync(file).isFile(); } catch { /* missing */ }
  if (!isF) return [null, [new Diagnostic("error", "missing-config", "configuration file is missing", rel)]];
  let configText: string;
  try { configText = readText(file); }
  catch (exc) { if (exc instanceof InvalidEncodingError) return [null, [new Diagnostic("error", "invalid-encoding", exc.message, rel)]]; throw exc; }
  const [raw] = frontmatter.split(configText);
  if (raw === null) return [null, [new Diagnostic("error", "bad-config", "config.md has no YAML front matter", rel)]];
  let data: Meta;
  try { data = frontmatter.parse(raw); }
  catch (exc) { return [null, [new Diagnostic("error", "bad-config", (exc as Error).message, rel)]]; }

  const diags: Diagnostic[] = [];
  const err = (msg: string) => diags.push(new Diagnostic("error", "bad-config", msg, rel));
  const name = data["project_name"];
  if (typeof name !== "string" || !strip(name)) err("project_name must be a non-empty string");
  if (data["schema_version"] !== SCHEMA_VERSION) err(`schema_version must be ${SCHEMA_VERSION}`);
  const dirs = data["directories"];
  if (!isDict(dirs) || JSON.stringify(sortedStrings(Object.keys(dirs))) !== JSON.stringify(sortedStrings(TOP_DIRS))) {
    err(`directories must be a mapping with exactly the keys ${TOP_DIRS.join(", ")}`);
  } else {
    const values = Object.values(dirs);
    let broke = false;
    for (const value of values) {
      if (typeof value !== "string" || !value || value.includes("/") || value.startsWith(".") || value === "..") {
        err("directories values must be single-segment, non-hidden folder names");
        broke = true;
        break;
      }
    }
    if (!broke && new Set(values).size !== values.length) err("directories values must be unique");
  }
  if ("publishing" in data && !isDict(data["publishing"])) err("publishing must be a mapping when present");
  else if (isDict(data["publishing"])) {
    const secret = sortedStrings(Object.keys(data["publishing"]).filter((k) => CREDENTIAL_KEY_RE.test(k)));
    if (secret.length) err(`publishing must not hold credentials (${secret.join(", ")}); authenticate through the provider's own tooling`);
  }
  const known = new Set(["project_name", "schema_version", "directories", "publishing"]);
  const unknown = Object.keys(data).filter((k) => !known.has(k));
  if (unknown.length) diags.push(new Diagnostic("warning", "unknown-config-key", `unknown keys: ${sortedStrings(unknown).join(", ")}`, rel));
  return [diags.some((d) => d.severity === "error") ? null : data, diags];
}

export class Project {
  directories: Record<string, string> = { ...DEFAULT_DIRECTORIES };
  constructor(public root: string, public config: Meta | null = null) {}

  static open(root: string): Project {
    const resolved = resolvePath(root);
    const [cfg] = loadConfig(resolved);
    const project = new Project(resolved, cfg);
    if (cfg) project.directories = { ...(cfg["directories"] as Record<string, string>) };
    return project;
  }

  top(key: string): string { return path.join(this.root, this.directories[key]!); }

  categoryDir(category: string): string {
    const [key, sub] = CATEGORY_LOCATION[category]!;
    const base = this.top(key);
    return sub ? path.join(base, sub) : base;
  }

  rel(p: string): string {
    const resolved = resolvePath(p);
    if (resolved === this.root) return ".";
    if (resolved.startsWith(this.root + path.sep)) return resolved.slice(this.root.length + 1).split(path.sep).join("/");
    return p.split(path.sep).join("/");
  }

  get name(): string {
    const n = this.config?.["project_name"];
    return (typeof n === "string" && n) ? n : path.basename(this.root);
  }
}

const pySuffix = (name: string): string => {
  const i = name.lastIndexOf(".");
  return i <= 0 || i === name.length - 1 ? "" : name.slice(i);
};
const pyStem = (name: string): string => {
  const s = pySuffix(name);
  return s ? name.slice(0, name.length - s.length) : name;
};
const cut = (s: string, n: number): string => [...s].slice(0, n).join("");

export class Doc {
  covers: string[] = [];
  constructor(
    public path: string, public rel: string, public locCat: string | null, public nameId: string | null,
    public meta: Meta, public parsed: ParsedBody, public diags: Diagnostic[], public text = "",
  ) {}
  get id(): string {
    const metaId = this.meta["id"];
    return this.nameId || (typeof metaId === "string" ? metaId : pyStem(path.basename(this.path)));
  }
  get category(): string | null { return categoryOf(this.id) ?? this.locCat; }
  get isStory(): boolean { return this.category === "US"; }
  get valid(): boolean { return !this.diags.some((d) => d.severity === "error"); }
  get title(): string {
    const t = this.meta["title"];
    return t === null || t === undefined || t === "" || t === false || t === 0 || (Array.isArray(t) && t.length === 0) ? this.id : pyStr(t);
  }
}

const isDate = (value: unknown): boolean => typeof value === "string" && isRealDate(value);

function checkMeta(doc: Doc, fields: boolean): void {
  const err = (code: string, msg: string, sev: Severity = "error") => doc.diags.push(new Diagnostic(sev, code, msg, doc.rel, doc.id));
  if (doc.nameId === null) err("bad-filename", "filename must match <ID>-<short-kebab-title>.md (e.g. BR-001-business-overview.md)");
  if (doc.nameId && doc.locCat !== categoryOf(doc.nameId)) {
    err("wrong-directory", `${categoryOf(doc.nameId)} documents do not belong here (directory holds ${doc.locCat || "a managed directory"})`);
  }
  if (doc.nameId === null && doc.locCat === null) err("misplaced-document", "document is not in a managed directory");
  if (fields) checkFields(doc, err);
  checkBody(doc);
}

function checkFields(doc: Doc, err: (code: string, msg: string, sev?: Severity) => void): void {
  const meta = doc.meta;
  for (const key of REQUIRED_FIELDS) if (blank(meta[key])) err("missing-field", `required front matter field '${key}' is missing`);
  const fmId = meta["id"];
  if (!blank(fmId)) {
    if (typeof fmId !== "string" || !DOC_ID_RE.test(fmId)) err("invalid-id", `id ${repr(fmId)} is not a valid document ID (e.g. BR-001)`);
    else if (doc.nameId && fmId !== doc.nameId) err("id-filename-mismatch", `front matter id ${fmId} does not match filename ID ${doc.nameId}`);
  }
  for (const key of ["title", "purpose"]) {
    const value = meta[key];
    if (!blank(value) && (typeof value !== "string" || !strip(value))) err("invalid-field", `'${key}' must be a non-empty string`);
    else if (typeof value === "string" && key === "purpose" && strip(value).includes("\n")) err("invalid-purpose", "'purpose' must be a single line (one sentence)");
  }
  const status = meta["status"];
  if (!blank(status) && !(DOC_STATUSES as readonly unknown[]).includes(status)) err("invalid-status", `status ${repr(status)} must be one of ${DOC_STATUSES.join(", ")}`);
  let datesOk = true;
  for (const key of ["created", "updated"]) {
    const value = meta[key];
    if (!blank(value) && !isDate(value)) { datesOk = false; err("invalid-date", `'${key}' must be an ISO date YYYY-MM-DD, got ${repr(value)}`); }
  }
  if (datesOk && isDate(meta["created"]) && isDate(meta["updated"]) && (meta["updated"] as string) < (meta["created"] as string)) {
    err("date-order", "'updated' is earlier than 'created'", "warning");
  }
  if (doc.isStory) {
    const ds = meta["delivery_status"];
    if (blank(ds)) err("missing-field", "required Story field 'delivery_status' is missing");
    else if (!(DELIVERY_STATUSES as readonly unknown[]).includes(ds)) err("invalid-delivery-status", `delivery_status ${repr(ds)} must be one of ${DELIVERY_STATUSES.join(", ")}`);
    const covers = meta["covers"];
    if (!("covers" in meta) || covers === null || covers === undefined) err("missing-covers", "Story must declare 'covers' (use covers: [] for a standalone Story)");
    else if (!Array.isArray(covers) || !covers.every((c) => typeof c === "string")) err("invalid-covers", "'covers' must be a list of requirement IDs");
    else {
      const bad = (covers as string[]).filter((c) => !REQ_ID_RE.test(c));
      if (bad.length) err("invalid-covers", `'covers' contains malformed requirement IDs: ${bad.join(", ")}`);
      doc.covers = (covers as string[]).filter((c) => REQ_ID_RE.test(c));
    }
  }
}

function checkBody(doc: Doc): void {
  for (const [lineno, text] of doc.parsed.malformed) {
    doc.diags.push(new Diagnostic("error", "malformed-requirement", `malformed requirement declaration; use '- **PR-001-R001** — text': ${cut(text, 60)}`, doc.rel, doc.id, lineno));
  }
  for (const req of doc.parsed.requirements) {
    if (req.id.slice(0, req.id.lastIndexOf("-R")) !== doc.id) {
      doc.diags.push(new Diagnostic("error", "requirement-wrong-document", `requirement ${req.id} is declared in ${doc.id}; requirement IDs are scoped to their document`, doc.rel, req.id, req.line));
    }
  }
}

export function loadDoc(project: Project, file: string, locCat: string | null): Doc {
  const rel = project.rel(file);
  const diags: Diagnostic[] = [];
  let text = "";
  let undecodable = false;
  try { text = readText(file); }
  catch (exc) { if (!(exc instanceof InvalidEncodingError)) throw exc; undecodable = true; diags.push(new Diagnostic("error", "invalid-encoding", exc.message, rel)); }
  const lines = text.split("\n");
  const base = path.basename(file);
  const m = FILENAME_RE.exec(base);
  const [raw, bodyStart] = undecodable ? [null, 0] as [null, number] : frontmatter.split(text);
  let meta: Meta = {};
  if (undecodable) { /* reported above; nothing else can be said about the document */ }
  else if (raw === null) diags.push(new Diagnostic("error", "bad-front-matter", "document has no YAML front matter block", rel));
  else {
    try { meta = frontmatter.parse(raw); }
    catch (exc) { diags.push(new Diagnostic("error", "bad-front-matter", (exc as Error).message, rel)); }
  }
  const doc = new Doc(file, rel, locCat, m ? m[1]! : null, meta, parseBody(lines, bodyStart), diags, text);
  checkMeta(doc, diags.length === 0); // field checks need usable front matter
  return doc;
}

export function scanDocuments(project: Project): [Doc[], Diagnostic[]] {
  const docs: Doc[] = [];
  const diags: Diagnostic[] = [];
  const children = (dir: string): string[] => fs.readdirSync(dir).sort(cmpStr);

  const scan = (directory: string, locCat: string | null): void => {
    for (const name of children(directory)) {
      if (name.startsWith(".")) continue;
      const child = path.join(directory, name);
      if (locCat === "TEST" && isDir(child) && name === EVIDENCE_DIR) continue; // verification logs, not documents
      if (isDir(child)) {
        diags.push(new Diagnostic("warning", "unexpected-directory", "directory is not part of the managed layout and is ignored", project.rel(child)));
      } else if (pySuffix(name) === ".md" && name !== "map.md") docs.push(loadDoc(project, child, locCat));
    }
  };

  const top: [string, string][] = [["BR", "BR"], ["PR", "PR"], ["Stories", "US"]];
  for (const [key, cat] of top) {
    const dir = project.top(key);
    if (isDir(dir)) scan(dir, cat);
  }
  const artifacts = project.top("Artifacts");
  if (isDir(artifacts)) {
    for (const name of children(artifacts)) {
      if (name.startsWith(".")) continue;
      const child = path.join(artifacts, name);
      if (isDir(child)) {
        if (name in ARTIFACT_SUBDIRS) scan(child, ARTIFACT_SUBDIRS[name]!);
        else diags.push(new Diagnostic("warning", "unexpected-directory", "not a recognised Artifacts subdirectory (design, plans, research, tests); ignored", project.rel(child)));
      } else if (pySuffix(name) === ".md" && name !== "map.md") docs.push(loadDoc(project, child, null));
    }
  }
  return [docs, diags];
}

export { PyDateTime };
