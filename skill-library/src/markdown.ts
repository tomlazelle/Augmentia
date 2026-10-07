// Minimal Markdown extraction: links, requirement declarations, References sections (port of sdlc/markdown.py).
// Python's `\s`, `\S`, `\b` and `.` differ from JavaScript's; the patterns below spell out Python's meaning.

import { REQ_ID_RE } from "./model.js";
import { splitWs, strip, unquote, WS } from "./pyfmt.js";

const S = `[${WS}]`;
const NS = `[^${WS}]`;
const ANY = "[^\\n]";
const CATS = "BR|PR|US|DES|PLAN|RES|TEST";
const WORD = "[\\p{L}\\p{N}_]";

export const FENCE_RE = new RegExp(`^${S}*(\`\`\`|~~~)`);
const INLINE_CODE_RE = /`[^`]*`/g;
const LINK_RE = new RegExp(`!?\\[[^\\]]*\\]\\(${S}*(<[^>]*>|[^)${WS}]*)(?:${S}+(?:"[^"]*"|'[^']*'))?${S}*\\)`, "g");
const SCHEME_RE = /^[A-Za-z][A-Za-z0-9+.-]*:/;
export const HEADING_RE = new RegExp(`^(#{1,6})${S}+(${ANY}*?)${S}*#*${S}*$`);
const LIST_ITEM_RE = new RegExp(`^${S}*[-*+]${S}+`);
const LIST_DECL_RE = new RegExp(`^${S}*[-*+]${S}+\\*\\*([^*]+)\\*\\*${S}+—${S}+(${NS}${ANY}*)$`);
const HEAD_DECL_RE = new RegExp(`^#{1,6}${S}+\\*\\*([^*]+)\\*\\*(?:${S}+—${S}+(${NS}${ANY}*))?${S}*$`);
const ATTEMPT_RE = new RegExp(`^${S}*(?:[-*+]|#{1,6})${S}+\\**${S}*[A-Z]{2,4}-[0-9]+-R`);
export const REQ_TOKEN_RE_G = new RegExp(`(?<!${WORD})(?:${CATS})-[0-9]{3,}-R[0-9]{3,}(?!${WORD})`, "gu");

export const REF_SECTIONS = ["Derived From", "Related To", "Supporting Artifacts"] as const;

export interface ReqDecl { id: string; line: number; text: string }
export interface Ref { section: string; line: number; href: string | null; reqIds: string[] }
export interface ParsedBody {
  requirements: ReqDecl[];
  malformed: [number, string][];
  refs: Ref[];
  links: [number, string][];
}

const stripChars = (s: string, chars: string): string => {
  let a = 0, b = s.length;
  while (a < b && chars.includes(s[a]!)) a++;
  while (b > a && chars.includes(s[b - 1]!)) b--;
  return s.slice(a, b);
};

/** Local link targets on a line: fragments/queries removed; external and anchor-only skipped. */
export function extractHrefs(line: string): string[] {
  const out: string[] = [];
  for (const m of line.replace(INLINE_CODE_RE, "").matchAll(LINK_RE)) {
    let href = strip(stripChars(m[1]!, "<>"));
    if (!href || href.startsWith("#") || SCHEME_RE.test(href)) continue;
    href = unquote(href.split("#", 2)[0]!.split("?", 2)[0]!);
    if (href) out.push(href);
  }
  return out;
}

export function reqTokens(text: string): string[] {
  const found = new Set(text.replace(INLINE_CODE_RE, "").match(REQ_TOKEN_RE_G) ?? []);
  return [...found].sort(cmpCodePoint);
}

function cmpCodePoint(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0; // IDs are ASCII
}

/** Parse body lines (0-based `start` index into the full file) outside code fences. */
export function parseBody(lines: string[], start: number): ParsedBody {
  const parsed: ParsedBody = { requirements: [], malformed: [], refs: [], links: [] };
  let fence: string | null = null;
  let h2 = "", h3 = "";
  for (let idx = start; idx < lines.length; idx++) {
    const text = lines[idx]!;
    const lineno = idx + 1;
    const fm = FENCE_RE.exec(text);
    if (fm) {
      fence = fence === fm[1] ? null : (fence ?? fm[1]!);
      continue;
    }
    if (fence) continue;
    const heading = HEADING_RE.exec(text);
    if (heading) {
      const level = heading[1]!.length, title = heading[2]!;
      if (level === 2) { h2 = title; h3 = ""; }
      else if (level === 3) h3 = title;
    }
    const inRefs = h2.toLowerCase() === "references";
    const hrefs = extractHrefs(text);
    for (const h of hrefs) parsed.links.push([lineno, h]);
    if (inRefs) {
      if (h3 && LIST_ITEM_RE.test(text)) {
        const reqs = reqTokens(text);
        const section = REF_SECTIONS.find((s) => s.toLowerCase() === h3.toLowerCase()) ?? h3;
        for (const href of hrefs) parsed.refs.push({ section, line: lineno, href, reqIds: reqs });
        if (hrefs.length === 0 && reqs.length > 0) parsed.refs.push({ section, line: lineno, href: null, reqIds: reqs });
      }
      continue;
    }
    const m = LIST_DECL_RE.exec(text) ?? HEAD_DECL_RE.exec(text);
    if (m && REQ_ID_RE.test(strip(m[1]!))) parsed.requirements.push({ id: strip(m[1]!), line: lineno, text: strip(m[2] ?? "") });
    else if (ATTEMPT_RE.test(text)) parsed.malformed.push([lineno, strip(text)]);
  }
  return parsed;
}

/** Blank out a marker-delimited region (used to ignore generated content when checking links). */
export function maskRegion(text: string, startMarker: string, endMarker: string): string {
  const s = text.indexOf(startMarker), e = text.indexOf(endMarker);
  if (s === -1 || e === -1 || e < s) return text;
  const region = text.slice(s, e);
  return text.slice(0, s) + "\n".repeat(region.split("\n").length - 1) + text.slice(e + endMarker.length);
}

export { splitWs };
