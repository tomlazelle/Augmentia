// Shared constants, ID grammar and the diagnostic/outcome records (port of sdlc/model.py).

import { cmpTuple } from "./pyfmt.js";

export const DOC_CATEGORIES = ["BR", "PR", "US", "DES", "PLAN", "RES", "TEST"] as const;
export type Category = (typeof DOC_CATEGORIES)[number];
const CATS = DOC_CATEGORIES.join("|");

export const DOC_ID_RE = new RegExp(`^(${CATS})-([0-9]{3,})$`);
export const REQ_ID_RE = new RegExp(`^((${CATS})-[0-9]{3,})-R([0-9]{3,})$`);
export const REQ_TOKEN_RE = new RegExp(`\\b(?:${CATS})-[0-9]{3,}-R[0-9]{3,}\\b`, "g");
export const FILENAME_RE = new RegExp(`^((${CATS})-[0-9]{3,})-([a-z0-9]+(?:-[a-z0-9]+)*)\\.md$`);

export const DOC_STATUSES = ["Draft", "In Review", "Approved", "Superseded"] as const;
export const DELIVERY_STATUSES = ["Not Started", "Ready", "In Progress", "Implemented", "Verified"] as const;

/** category -> [top-level directory key, Artifacts subdirectory or null] */
export const CATEGORY_LOCATION: Record<string, [string, string | null]> = {
  BR: ["BR", null],
  PR: ["PR", null],
  US: ["Stories", null],
  DES: ["Artifacts", "design"],
  PLAN: ["Artifacts", "plans"],
  RES: ["Artifacts", "research"],
  TEST: ["Artifacts", "tests"],
};
export const ARTIFACT_SUBDIRS: Record<string, string> = { design: "DES", plans: "PLAN", research: "RES", tests: "TEST" };
export const TOP_DIRS = ["BR", "PR", "Stories", "Artifacts"] as const;

export const GEN_START = "<!-- sdlc:generated:start -->";
export const GEN_END = "<!-- sdlc:generated:end -->";

export type Severity = "error" | "warning" | "notice";

export class Diagnostic {
  constructor(
    public severity: Severity,
    public code: string,
    public message: string,
    public path: string | null = null,
    public id: string | null = null,
    public line: number | null = null,
  ) {}

  toDict(): Record<string, unknown> {
    return { severity: this.severity, code: this.code, message: this.message, path: this.path, id: this.id, line: this.line };
  }

  human(): string {
    let where = this.path ?? "";
    if (where && this.line) where += `:${this.line}`;
    const parts = [`${this.severity}:`];
    if (where) parts.push(`${where}:`);
    if (this.id) parts.push(`[${this.id}]`);
    parts.push(`${this.message} (${this.code})`);
    return parts.join(" ");
  }
}

export class Outcome {
  result: Record<string, unknown>;
  diagnostics: Diagnostic[];
  constructor(public exitCode = 0, result?: Record<string, unknown>, diagnostics?: Diagnostic[]) {
    this.result = result ?? {};
    this.diagnostics = diagnostics ?? [];
  }
}

export function idKind(value: string): "document" | "requirement" | null {
  if (DOC_ID_RE.test(value)) return "document";
  if (REQ_ID_RE.test(value)) return "requirement";
  return null;
}

export function categoryOf(value: string): string | null {
  return idKind(value) ? value.split("-", 1)[0]! : null;
}

export function ownerOf(reqId: string): string {
  return REQ_ID_RE.exec(reqId)![1]!;
}

export function idSortKey(value: string): number[] {
  let m = REQ_ID_RE.exec(value);
  if (m) {
    const [cat, num] = m[1]!.split("-");
    return [DOC_CATEGORIES.indexOf(cat as Category), parseInt(num!, 10), parseInt(m[3]!, 10)];
  }
  m = DOC_ID_RE.exec(value);
  if (m) return [DOC_CATEGORIES.indexOf(m[1] as Category), parseInt(m[2]!, 10), 0];
  return [DOC_CATEGORIES.length, 0, 0];
}

export const cmpId = (a: string, b: string): number => cmpTuple(idSortKey(a), idSortKey(b));

export function formatDocId(category: string, number: number): string {
  return `${category}-${String(number).padStart(3, "0")}`;
}

export function slugify(title: string): string {
  return title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
