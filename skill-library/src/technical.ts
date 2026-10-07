// R2 evidence records: Story Implementation Records and TEST Verification Runs (port of sdlc/technical.py).

import { FENCE_RE, HEADING_RE } from "./markdown.js";
import { Diagnostic } from "./model.js";
import { repr, strip, WS } from "./pyfmt.js";

const S = `[${WS}]`;
export const RESULTS = ["passed", "failed", "blocked", "not-run"];
export const KINDS = ["automated", "manual"];
const FIELD_RE = new RegExp(`^${S}*[-*]${S}+\\*\\*([^*:]+):\\*\\*${S}*([^\\n]*?)${S}*$`);
const TIMESTAMP_RE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}(?:T[0-9]{2}:[0-9]{2}:[0-9]{2}Z)?$/;
const AC_RE = /^AC-([1-9][0-9]*)$/;
const NUMBERED_RE = new RegExp(`^[0-9]+\\.${S}+[^${WS}]`);
const TBD_RE = new RegExp(`^${S}*[-*]${S}+\\*\\*TBD\\*\\*`);
export const RECORD_ID: Record<string, RegExp> = {
  IR: new RegExp(`^(IR-[0-9]+) — ([^${WS}]+)${S}*$`),
  VR: new RegExp(`^(VR-[0-9]+) — ([^${WS}]+)${S}*$`),
  PUB: new RegExp(`^(PUB-[0-9]+) — ([^${WS}]+)${S}*$`),
};
const UNRESOLVED_HEADING = "unresolved acceptance behavior (tbd)";
const cut = (s: string, n: number): string => [...s].slice(0, n).join("");

export interface Section { level: number; title: string; line: number; end: number; body: [number, string][] }

/** Headings (levels 1-3) outside code fences; a section's body runs until the next heading of the same or shallower level. */
export function sections(text: string): Section[] {
  const lines = text.split("\n");
  const heads: Section[] = [];
  let fence: string | null = null;
  lines.forEach((raw, idx) => {
    const fm = FENCE_RE.exec(raw);
    if (fm) { fence = fence === fm[1] ? null : (fence ?? fm[1]!); return; }
    const heading = fence ? null : HEADING_RE.exec(raw);
    if (heading && heading[1]!.length <= 3) heads.push({ level: heading[1]!.length, title: strip(heading[2]!), line: idx + 1, end: 0, body: [] });
  });
  heads.forEach((sec, k) => {
    let end = lines.length;
    for (const nxt of heads.slice(k + 1)) if (nxt.level <= sec.level) { end = nxt.line - 1; break; }
    sec.end = end;
    sec.body = [];
    for (let n = sec.line; n < end; n++) sec.body.push([n + 1, lines[n]!]);
  });
  return heads;
}

export const find = (secs: Section[], title: string, level: number): Section | undefined =>
  secs.find((s) => s.level === level && s.title.toLowerCase() === title.toLowerCase());

export function acceptanceCriteriaCount(secs: Section[]): number {
  const sec = find(secs, "Acceptance Criteria", 2);
  if (!sec) return 0;
  let count = 0, stop = false;
  for (const [, line] of sec.body) {
    if (line.startsWith("### ")) stop = true; // subsections such as Unresolved Acceptance Behavior hold no decided criteria
    if (!stop && NUMBERED_RE.test(line)) count++;
  }
  return count;
}

export function unresolvedTbdBullets(secs: Section[]): number {
  // The heading *title* is the contract; agents have written it at level 2 as well as the template's level 3.
  const sec = secs.find((s) => (s.level === 2 || s.level === 3) && s.title.toLowerCase() === UNRESOLVED_HEADING);
  if (!sec) return 0;
  return sec.body.filter(([, line]) => TBD_RE.test(line)).length;
}

export interface Rec { id: string; stamp: string; line: number; fields: Record<string, string>; order: number }

/** Parse `### <PREFIX>-n — <stamp>` blocks under the `## heading` section. Returns [records, bad heading lines]. */
export function records(secs: Section[], heading: string, prefix: string): [Rec[], [number, string][]] {
  const parent = find(secs, heading, 2);
  if (!parent) return [[], []];
  const recs: Rec[] = [];
  const bad: [number, string][] = [];
  for (const sec of secs) {
    if (sec.level !== 3 || !(parent.line < sec.line && sec.line <= parent.end)) continue;
    const m = RECORD_ID[prefix]!.exec(sec.title);
    if (!m) { bad.push([sec.line, sec.title]); continue; }
    const fields: Record<string, string> = {};
    for (const [, line] of sec.body) {
      const fm = FIELD_RE.exec(line);
      if (fm) { const key = strip(fm[1]!).toLowerCase(); if (!(key in fields)) fields[key] = fm[2]!; }
    }
    recs.push({ id: m[1]!, stamp: m[2]!, line: sec.line, fields, order: recs.length });
  }
  return [recs, bad];
}

const get = (r: Rec, key: string): string => r.fields[key] ?? "";
const titleCase = (key: string): string => key.split(" ").map((w) => w[0]!.toUpperCase() + w.slice(1).toLowerCase()).join(" ");

export function checkImplementationRecords(rel: string, docId: string, secs: Section[]): [Rec[], Diagnostic[]] {
  const [recs, bad] = records(secs, "Implementation Record", "IR");
  const diags = bad.map(([line, title]) => new Diagnostic("error", "implementation-record-invalid", `heading must be '### IR-<n> — <YYYY-MM-DD>': ${cut(title, 50)}`, rel, docId, line));
  const seen = new Set<string>();
  for (const r of recs) {
    if (seen.has(r.id)) diags.push(new Diagnostic("error", "implementation-record-invalid", `${r.id} appears more than once`, rel, docId, r.line));
    seen.add(r.id);
    if (!TIMESTAMP_RE.test(r.stamp)) diags.push(new Diagnostic("error", "implementation-record-invalid", `${r.id}: date must be YYYY-MM-DD, got ${repr(r.stamp)}`, rel, docId, r.line));
    for (const key of ["summary", "files changed"]) {
      if (!strip(get(r, key))) diags.push(new Diagnostic("error", "implementation-record-invalid", `${r.id}: required field '${titleCase(key)}' is missing or empty`, rel, docId, r.line));
    }
  }
  return [recs, diags];
}

/** Validate Verification Runs of one TEST document. `storyAc` maps Story ID -> criteria count. */
export function checkVerificationRuns(rel: string, docId: string, secs: Section[], storyAc: Map<string, number | null>): [Rec[], Diagnostic[]] {
  const [recs, bad] = records(secs, "Verification Runs", "VR");
  const diags = bad.map(([line, title]) => new Diagnostic("error", "verification-bad-heading", `heading must be '### VR-<n> — <YYYY-MM-DD[THH:MM:SSZ]>': ${cut(title, 50)}`, rel, docId, line));
  const seen = new Set<string>();
  const err = (r: Rec, code: string, msg: string) => diags.push(new Diagnostic("error", code, `${r.id}: ${msg}`, rel, docId, r.line));
  for (const r of recs) {
    if (seen.has(r.id)) err(r, "verification-bad-heading", "run ID appears more than once in this document");
    seen.add(r.id);
    if (!TIMESTAMP_RE.test(r.stamp)) err(r, "verification-bad-heading", `timestamp must be ISO (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ), got ${repr(r.stamp)}`);
    const kind = strip(get(r, "kind")), result = strip(get(r, "result"));
    for (const key of ["story", "kind", "result", "criteria", "environment", "performed by", "observed"]) {
      if (!strip(get(r, key))) err(r, "verification-missing-field", `required field '${titleCase(key)}' is missing or empty`);
    }
    if (kind && !KINDS.includes(kind)) err(r, "verification-bad-value", `Kind must be one of ${KINDS.join(", ")}, got ${repr(kind)}`);
    if (result && !RESULTS.includes(result)) err(r, "verification-bad-value", `Result must be one of ${RESULTS.join(", ")}, got ${repr(result)}`);
    if (kind === "automated" && (result === "passed" || result === "failed")) {
      for (const key of ["command", "exit code"]) if (!strip(get(r, key))) err(r, "verification-missing-field", `automated ${result} run requires '${titleCase(key)}'`);
      const code = strip(get(r, "exit code"));
      if (code) {
        if (!/^-?[0-9]+$/.test(code)) err(r, "verification-bad-value", `Exit code must be an integer, got ${repr(code)}`);
        else if (result === "passed" && parseInt(code, 10) !== 0) err(r, "verification-inconsistent", `marked passed but exit code is ${code}`);
        else if (result === "failed" && parseInt(code, 10) === 0) err(r, "verification-inconsistent", "marked failed but exit code is 0");
      }
    }
    const story = strip(get(r, "story"));
    if (story && !storyAc.has(story)) err(r, "verification-unknown-story", `Story ${story} does not exist`);
    for (const token of get(r, "criteria").split(",").map(strip).filter((t) => t)) {
      if (token.toLowerCase() === "none") continue; // supporting/smoke check that demonstrates no acceptance criterion
      const m = AC_RE.exec(token);
      const known = storyAc.get(story);
      if (!m) err(r, "verification-bad-criteria", `criterion ${repr(token)} must look like AC-1`);
      else if (known !== undefined && known !== null && parseInt(m[1]!, 10) > known) err(r, "verification-bad-criteria", `${token} does not exist: ${story} has ${known} acceptance criteria`);
    }
  }
  return [recs, diags];
}

export const isSuperseded = (rec: Rec): boolean => strip(get(rec, "superseded")).toLowerCase().startsWith("yes");

export const criteriaOf = (rec: Rec): number[] =>
  get(rec, "criteria").split(",").flatMap((t) => { const m = AC_RE.exec(strip(t)); return m ? [parseInt(m[1]!, 10)] : []; });
