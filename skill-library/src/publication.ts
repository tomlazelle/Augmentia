// Publication records: the durable, Markdown-resident identity of a published Story (port of sdlc/publication.py;
// the append side arrives with the publishing commands in M7.4).

import fs from "node:fs";
import { Diagnostic } from "./model.js";
import path from "node:path";
import { readText, repr, strip } from "./pyfmt.js";
import { type Section, find, records, sections } from "./technical.js";

export const HEADING = "Publication";
export const PROVIDERS = ["github"];
const ISSUE_RE = /^#([0-9]+)$/;
export const REPO_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const DATE_RE = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
const cut = (s: string, n: number): string => [...s].slice(0, n).join("");

export interface Publication { id: string; date: string; provider: string; repository: string; issue: string; url: string | null; line: number }

/** Publications recorded in a Story, plus `publication-invalid` errors for anything malformed. */
export function parse(rel: string, docId: string, secs: Section[]): [Publication[], Diagnostic[]] {
  const [recs, bad] = records(secs, HEADING, "PUB");
  const diags = bad.map(([line, title]) => new Diagnostic("error", "publication-invalid", `heading must be '### PUB-<n> — <YYYY-MM-DD>': ${cut(title, 50)}`, rel, docId, line));
  const out: Publication[] = [];
  const seen = new Set<string>();
  for (const r of recs) {
    const err = (msg: string) => diags.push(new Diagnostic("error", "publication-invalid", `${r.id}: ${msg}`, rel, docId, r.line));
    if (seen.has(r.id)) err("appears more than once");
    seen.add(r.id);
    if (!DATE_RE.test(r.stamp)) err(`date must be YYYY-MM-DD, got ${repr(r.stamp)}`);
    const provider = strip(r.fields["provider"] ?? "");
    const repository = strip(r.fields["repository"] ?? "");
    const issue = strip(r.fields["issue"] ?? "");
    const url = strip(r.fields["url"] ?? "") || null;
    let ok = true;
    if (!PROVIDERS.includes(provider)) { err(`Provider must be one of ${PROVIDERS.join(", ")}, got ${repr(provider)}`); ok = false; }
    if (!REPO_RE.test(repository)) { err(`Repository must be 'owner/name', got ${repr(repository)}`); ok = false; }
    if (!ISSUE_RE.test(issue)) { err(`Issue must look like '#42', got ${repr(issue)}`); ok = false; }
    if (ok) out.push({ id: r.id, date: r.stamp, provider, repository, issue, url, line: r.line });
  }
  return [out, diags];
}

const EMPTY_SECTION_TEXT = "None recorded.";

export function renderEntry(number: number, date: string, provider: string, repository: string, issueNumber: number, url: string | null): string {
  const lines = [`### PUB-${number} — ${date}`, `- **Provider:** ${provider}`, `- **Repository:** ${repository}`, `- **Issue:** #${issueNumber}`];
  if (url) lines.push(`- **URL:** ${url}`);
  lines.push("- **Recorded by:** `sdlc publish-apply` (publication is non-material; local Markdown stays authoritative)");
  return lines.join("\n") + "\n";
}

function bumpUpdated(text: string, today: string): string {
  if (!text.startsWith("---")) return text;
  const end = text.indexOf("\n---", 3);
  if (end === -1) return text;
  const head = text.slice(0, end), rest = text.slice(end);
  const replaced = head.replace(/^updated:[^\n]*$/m, `updated: ${today}`);
  return replaced !== head || /^updated:[^\n]*$/m.test(head) ? replaced + rest : text;
}

/**
 * Append a PUB entry to the Story file and set `updated`. Does not touch `status` or `delivery_status`.
 * Returns the new PUB id. The write is atomic (temp file + rename), so a failure leaves the Story unchanged.
 */
export function appendRecord(file: string, date: string, provider: string, repository: string, issueNumber: number, url: string | null): string {
  const text = readText(file);
  const secs = sections(text);
  const [existing] = records(secs, HEADING, "PUB");
  const number = Math.max(0, ...existing.map((r) => parseInt(r.id.split("-")[1]!, 10))) + 1;
  const entry = renderEntry(number, date, provider, repository, issueNumber, url).replace(/\n+$/, "");
  const section = find(secs, HEADING, 2);
  let next: string;
  if (!section) next = text.replace(/\n+$/, "") + `\n\n## ${HEADING}\n\n${entry}\n`;
  else {
    const lines = text.split("\n");
    const head = lines.slice(0, section.line).join("\n");
    const trimNl = (s: string) => s.replace(/^\n+|\n+$/g, "");
    const body = trimNl(lines.slice(section.line, section.end).filter((ln) => strip(ln) !== EMPTY_SECTION_TEXT).join("\n"));
    const tail = trimNl(lines.slice(section.end).join("\n"));
    next = head + "\n\n" + (body ? body + "\n\n" : "") + entry + "\n" + (tail ? "\n" + tail + "\n" : "");
  }
  next = bumpUpdated(next, date);
  const tmp = path.join(path.dirname(file), `.${path.basename(file)}.sdlc-tmp`);
  fs.writeFileSync(tmp, next, "utf8");
  fs.renameSync(tmp, file);
  return `PUB-${number}`;
}
