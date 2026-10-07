// PyYAML-compatible YAML for front matter and config.md.
//
// Parsing: the `yaml` package (failsafe schema) provides the structure; implicit typing and constructors follow
// PyYAML's SafeLoader exactly (YAML 1.1 core: yes/no/on/off booleans, 0o17/017 octal, 1:30 sexagesimal, timestamps,
// `<<` merge keys, last duplicate key wins). Emitting: a port of PyYAML's scalar emitter, used only for config.md.

import { isAlias, isMap, isScalar, isSeq, parseDocument, type Node, type Scalar, type YAMLMap } from "yaml";
import { daysInMonth, pyStr } from "./pyfmt.js";

export class YamlError extends Error {
  /** "yaml": a YAMLError (reported as `invalid YAML: ...`); "value": a ValueError from a constructor (`invalid YAML value: ...`). */
  constructor(public kind: "yaml" | "value", message: string) {
    super(message);
  }
}

export class PyDate {
  constructor(public year: number, public month: number, public day: number) {}
  iso(): string {
    return `${String(this.year).padStart(4, "0")}-${String(this.month).padStart(2, "0")}-${String(this.day).padStart(2, "0")}`;
  }
  pyStr(): string { return this.iso(); }
  pyRepr(): string {
    return `datetime.date(${this.year}, ${this.month}, ${this.day})`;
  }
}

export class PyDateTime {
  constructor(public parts: { y: number; mo: number; d: number; h: number; mi: number; s: number; us: number; tz: string | null }) {}
  /** str(datetime): `YYYY-MM-DD HH:MM:SS[.ffffff][+HH:MM[:SS]]`. */
  pyStr(): string {
    const p = this.parts, z = (n: number, w = 2): string => String(n).padStart(w, "0");
    let out = `${z(p.y, 4)}-${z(p.mo)}-${z(p.d)} ${z(p.h)}:${z(p.mi)}:${z(p.s)}`;
    if (p.us) out += `.${z(p.us, 6)}`;
    if (p.tz) {
      const m = /days=(-?\d+), seconds=(\d+)|seconds=(-?\d+)/.exec(p.tz);
      const secs = p.tz === "datetime.timezone.utc" || !m ? 0 : m[1] !== undefined ? Number(m[1]) * 86400 + Number(m[2]) : Number(m[3]);
      const a = Math.abs(secs);
      out += `${secs < 0 ? "-" : "+"}${z(Math.floor(a / 3600))}:${z(Math.floor((a % 3600) / 60))}${a % 60 ? ":" + z(a % 60) : ""}`;
    }
    return out;
  }
  pyRepr(): string {
    const p = this.parts;
    const args = [p.y, p.mo, p.d, p.h, p.mi];
    if (p.us || p.s) args.push(p.s);
    if (p.us) args.push(p.us);
    return `datetime.datetime(${args.join(", ")}${p.tz ? `, tzinfo=${p.tz}` : ""})`;
  }
}

export type PyValue = null | boolean | number | string | PyDate | PyDateTime | PyValue[] | { [key: string]: PyValue };

const RESOLVERS: { tag: string; re: RegExp; first: string }[] = [
  { tag: "bool", re: /^(?:yes|Yes|YES|no|No|NO|true|True|TRUE|false|False|FALSE|on|On|ON|off|Off|OFF)$/, first: "yYnNtTfFoO" },
  { tag: "float", re: /^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?|[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$/, first: "-+0123456789." },
  { tag: "int", re: /^(?:[-+]?0b[0-1_]+|[-+]?0[0-7_]+|[-+]?(?:0|[1-9][0-9_]*)|[-+]?0x[0-9a-fA-F_]+|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$/, first: "-+0123456789" },
  { tag: "merge", re: /^(?:<<)$/, first: "<" },
  { tag: "null", re: /^(?:~|null|Null|NULL|)$/, first: "~nN" },
  { tag: "timestamp", re: /^(?:[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]|[0-9][0-9][0-9][0-9]-[0-9][0-9]?-[0-9][0-9]?(?:[Tt]|[ \t]+)[0-9][0-9]?:[0-9][0-9]:[0-9][0-9](?:\.[0-9]*)?(?:[ \t]*(?:Z|[-+][0-9][0-9]?(?::[0-9][0-9])?))?)$/, first: "0123456789" },
  { tag: "value", re: /^(?:=)$/, first: "=" },
];

/** Implicit tag of a plain scalar (PyYAML Resolver.resolve for a scalar with implicit=(True, False)). */
export function implicitTag(value: string): string {
  const first = value === "" ? "" : value[0]!;
  for (const r of RESOLVERS) {
    if (r.first.includes(first) || (value === "" && r.tag === "null")) {
      if (r.re.test(value)) return r.tag;
    }
  }
  return "str";
}

const TIMESTAMP =
  /^(?<year>[0-9][0-9][0-9][0-9])-(?<month>[0-9][0-9]?)-(?<day>[0-9][0-9]?)(?:(?:[Tt]|[ \t]+)(?<hour>[0-9][0-9]?):(?<minute>[0-9][0-9]):(?<second>[0-9][0-9])(?:\.(?<fraction>[0-9]*))?(?:[ \t]*(?<tz>Z|(?<tzsign>[-+])(?<tzhour>[0-9][0-9]?)(?::(?<tzminute>[0-9][0-9]))?))?)?$/;

function constructTimestamp(value: string): PyDate | PyDateTime {
  const g = TIMESTAMP.exec(value)!.groups!;
  const year = +g["year"]!, month = +g["month"]!, day = +g["day"]!;
  if (year < 1) throw new YamlError("value", `year ${year} is out of range`);
  if (month < 1 || month > 12) throw new YamlError("value", "month must be in 1..12");
  if (day < 1 || day > daysInMonth(year, month)) throw new YamlError("value", "day is out of range for month");
  if (!g["hour"]) return new PyDate(year, month, day);
  const h = +g["hour"], mi = +g["minute"]!, s = +g["second"]!;
  if (h > 23) throw new YamlError("value", "hour must be in 0..23");
  if (mi > 59) throw new YamlError("value", "minute must be in 0..59");
  if (s > 59) throw new YamlError("value", "second must be in 0..59");
  let us = 0;
  if (g["fraction"]) us = +g["fraction"].slice(0, 6).padEnd(6, "0");
  let tz: string | null = null;
  if (g["tzsign"]) {
    const total = (+g["tzhour"]! * 60 + +(g["tzminute"] ?? 0)) * (g["tzsign"] === "-" ? -1 : 1);
    tz = total === 0 ? "datetime.timezone.utc" : `datetime.timezone(datetime.timedelta(${total < 0 ? "days=-1, seconds=" + (86400 + total * 60) : "seconds=" + total * 60}))`;
  } else if (g["tz"]) tz = "datetime.timezone.utc";
  return new PyDateTime({ y: year, mo: month, d: day, h, mi, s, us, tz });
}

function constructInt(raw: string): number {
  let value = raw.replace(/_/g, "");
  let sign = 1;
  if (value[0] === "-") sign = -1;
  if (value[0] === "+" || value[0] === "-") value = value.slice(1);
  if (value === "0") return 0;
  if (value.startsWith("0b")) return sign * parseInt(value.slice(2), 2);
  if (value.startsWith("0x")) return sign * parseInt(value.slice(2), 16);
  if (value[0] === "0") return sign * parseInt(value, 8);
  if (value.includes(":")) {
    let base = 1, total = 0;
    for (const part of value.split(":").map(Number).reverse()) { total += part * base; base *= 60; }
    return sign * total;
  }
  return sign * Number(value);
}

function constructFloat(raw: string): number {
  let value = raw.replace(/_/g, "").toLowerCase();
  let sign = 1;
  if (value[0] === "-") sign = -1;
  if (value[0] === "+" || value[0] === "-") value = value.slice(1);
  if (value === ".inf") return sign * Infinity;
  if (value === ".nan") return NaN;
  if (value.includes(":")) {
    let base = 1, total = 0;
    for (const part of value.split(":").map(Number).reverse()) { total += part * base; base *= 60; }
    return sign * total;
  }
  return sign * Number(value);
}

const BOOLS: Record<string, boolean> = { yes: true, no: false, true: true, false: false, on: true, off: false };

/** Mapping of the `yaml` package's error to PyYAML's error context line (the first line of str(YAMLError)). */
function pyYamlMessage(code: string, message: string): string {
  const first = message.split("\n")[0]!;
  if (code === "BAD_INDENT" && /Flow sequence/.test(first)) return "while parsing a flow sequence";
  if (code === "BAD_INDENT" && /Flow map/.test(first)) return "while parsing a flow mapping";
  if (/Flow sequence/.test(first) && /end with a \]/.test(first)) return "while parsing a flow sequence";
  if (/Flow map/.test(first) && /end with a }/.test(first)) return "while parsing a flow mapping";
  if (code === "MISSING_CHAR" && /closing/.test(first)) return "while scanning a quoted scalar";
  if (code === "BLOCK_AS_IMPLICIT_KEY" || code === "MULTILINE_IMPLICIT_KEY" || /compact mappings/.test(first)) return "mapping values are not allowed here";
  if (code === "TAB_AS_INDENT") return "while scanning for the next token";
  return first.replace(/ at line \d+, column \d+:?$/, "");
}

type Pair = [Node | null, Node | null];

class Constructor {
  constructor(private doc: ReturnType<typeof parseDocument>) {}

  construct(node: Node | null | undefined): PyValue {
    if (node === null || node === undefined) return null;
    if (isAlias(node)) {
      const target = node.resolve(this.doc);
      if (!target) throw new YamlError("yaml", `found undefined alias '${node.source}'`);
      return this.construct(target as Node);
    }
    if (isScalar(node)) return this.scalar(node);
    if (isSeq(node)) return node.items.map((n) => this.construct(n as Node));
    if (isMap(node)) return this.mapping(node);
    throw new YamlError("yaml", "unsupported YAML node");
  }

  private scalar(node: Scalar): PyValue {
    const raw = node.value === null || node.value === undefined ? "" : String(node.value);
    const tag = node.tag;
    if (tag) {
      const t = tag.replace("tag:yaml.org,2002:", "");
      if (!tag.startsWith("tag:yaml.org,2002:")) throw new YamlError("yaml", `could not determine a constructor for the tag '${tag}'`);
      return this.byTag(t, raw, tag);
    }
    if (node.type !== "PLAIN" && node.type !== undefined) return raw; // quoted and block scalars are always strings
    return this.byTag(implicitTag(raw), raw, null);
  }

  private byTag(t: string, raw: string, full: string | null): PyValue {
    switch (t) {
      case "str": return raw;
      case "null": return null;
      case "bool": return BOOLS[raw.toLowerCase()] ?? (() => { throw new YamlError("yaml", `could not determine a constructor for the tag '${full}'`); })();
      case "int": return constructInt(raw);
      case "float": return constructFloat(raw);
      case "timestamp": return TIMESTAMP.test(raw) ? constructTimestamp(raw) : (() => { throw new YamlError("yaml", `could not determine a constructor for the tag '${full}'`); })();
      default: throw new YamlError("yaml", `could not determine a constructor for the tag '${full ?? "tag:yaml.org,2002:" + t}'`);
    }
  }

  private pairs(map: YAMLMap): Pair[] {
    const own = map.items.map((p) => [p.key as Node | null, p.value as Node | null] as Pair);
    const merged: Pair[] = [];
    const rest: Pair[] = [];
    for (const [k, v] of own) {
      const isMerge = k !== null && isScalar(k) && !k.tag && (k.type === "PLAIN" || k.type === undefined) && String(k.value ?? "") === "<<";
      if (!isMerge) { rest.push([k, v]); continue; }
      const target = v !== null && isAlias(v) ? (v.resolve(this.doc) as Node | undefined) ?? null : v;
      if (target !== null && isMap(target)) merged.push(...this.pairs(target));
      else if (target !== null && isSeq(target)) {
        const sub: Pair[][] = [];
        for (const item of target.items) {
          const it = isAlias(item) ? (item.resolve(this.doc) as Node | undefined) ?? null : (item as Node);
          if (it === null || !isMap(it)) throw new YamlError("yaml", "while constructing a mapping");
          sub.push(this.pairs(it));
        }
        sub.reverse();
        for (const s of sub) merged.push(...s);
      } else throw new YamlError("yaml", "while constructing a mapping");
    }
    return [...merged, ...rest];
  }

  private mapping(map: YAMLMap): PyValue {
    const out: { [key: string]: PyValue } = {};
    for (const [k, v] of this.pairs(map)) {
      const key = this.construct(k);
      if (key !== null && typeof key === "object" && !(key instanceof PyDate) && !(key instanceof PyDateTime)) {
        throw new YamlError("yaml", "while constructing a mapping");
      }
      out[keyString(key)] = this.construct(v);
    }
    return out;
  }
}

/** str(k) for a constructed mapping key (what frontmatter.parse stores). */
function keyString(key: PyValue): string {
  if (key instanceof PyDate) return key.iso();
  if (key instanceof PyDateTime) return key.pyRepr();
  if (key === null) return "None";
  if (typeof key === "boolean") return key ? "True" : "False";
  return pyStr(key);
}

/**
 * PyYAML scanner rules the `yaml` package does not share, applied in one character-level pass:
 *  - YAML 1.1 line breaks (\x85, \u2028, \u2029) are breaks everywhere except inside quoted scalars (where PyYAML keeps
 *    them as literal characters); they are normalised to "\n" so the structure is read as PyYAML reads it;
 *  - a tab outside quoted scalars, comments and block-scalar bodies can never start a token (indentation, after `:`/`-`,
 *    between words of a plain scalar, inside flow collections): "while scanning for the next token".
 */
function normalizeForPyYaml(text: string): string {
  let out = "";
  let line = "";
  let inDouble = false, inSingle = false, inComment = false;
  let blockIndent: number | null = null;
  let prevSignificant = "";
  let sawContent = false;
  let bodyLine = false;

  const endLine = () => {
    const lead = line.length - line.trimStart().length;
    if (!inDouble && !inSingle && sawContent && /(?:^|[:\-]\s+|^\s*)[|>][+-]?[1-9]?[+-]?\s*(?:#.*)?$/.test(line)) blockIndent = lead;
    line = ""; prevSignificant = ""; sawContent = false; inComment = false; bodyLine = false;
  };

  for (const ch of text) {
    if (!inDouble && !inSingle && (ch === "\x85" || ch === "\u2028" || ch === "\u2029")) { out += "\n"; endLine(); continue; }
    if (ch === "\n") {
      out += ch;
      if (inDouble || inSingle) { line = ""; prevSignificant = ""; continue; }
      endLine();
      continue;
    }
    out += ch;
    if (line === "" && blockIndent !== null && !inDouble && !inSingle) {
      // decide at the first character of a line whether it belongs to a block scalar body (needs the whole line's indent)
      bodyLine = true;
    }
    line += ch;
    if (bodyLine && blockIndent !== null) {
      const lead = line.length - line.trimStart().length;
      const onlyWs = /^[ \t]*$/.test(line);
      if (!onlyWs && ch !== " " && ch !== "\t") {
        if (lead > blockIndent) { /* body */ } else { blockIndent = null; bodyLine = false; }
      }
      if (bodyLine) continue;
    }
    if (inDouble) { if (ch === '"' && !line.endsWith('\\"')) { inDouble = false; prevSignificant = '"'; } continue; }
    if (inSingle) { if (ch === "'" ) { inSingle = false; prevSignificant = "'"; } continue; }
    if (inComment) continue;
    if (ch === "\t") throw new YamlError("yaml", "while scanning for the next token");
    if (ch === " ") continue;
    if (ch === "#" && (line.length === 1 || line[line.length - 2] === " ")) { inComment = true; continue; }
    sawContent = true;
    const opensScalar = prevSignificant === "" || ":-,[{?".includes(prevSignificant);
    if (opensScalar && ch === '"') { inDouble = true; continue; }
    if (opensScalar && ch === "'") { inSingle = true; continue; }
    prevSignificant = ch;
  }
  return out;
}

/** yaml.safe_load(raw): returns the Python-equivalent value or throws YamlError. */
export function safeLoad(input: string): PyValue {
  const raw = normalizeForPyYaml(input);
  const doc = parseDocument(raw, { schema: "failsafe", version: "1.1", uniqueKeys: false, prettyErrors: false });
  const err = doc.errors[0];
  if (err) throw new YamlError("yaml", pyYamlMessage(err.code, err.message));
  return new Constructor(doc).construct(doc.contents as Node | null);
}

// --- emitting (config.md only) --------------------------------------------------------------------

const ESCAPES: Record<string, string> = { "\0": "0", "\x07": "a", "\x08": "b", "\t": "t", "\n": "n", "\x0b": "v", "\x0c": "f", "\r": "r", "\x1b": "e", '"': '"', "\\": "\\", "\x85": "N", "\xa0": "_", " ": "L", " ": "P" };
const BREAKS = "\n\x85  ";

interface Analysis { empty: boolean; multiline: boolean; allowBlockPlain: boolean; allowSingleQuoted: boolean }

function analyzeScalar(scalar: string): Analysis {
  if (!scalar) return { empty: true, multiline: false, allowBlockPlain: true, allowSingleQuoted: true };
  const chars = [...scalar];
  let blockInd = false, flowInd = false, lineBreaks = false, special = false;
  let leadSpace = false, leadBreak = false, trailSpace = false, trailBreak = false, breakSpace = false, spaceBreak = false;
  if (scalar.startsWith("---") || scalar.startsWith("...")) { blockInd = true; flowInd = true; }
  let precededWs = true;
  const ws = "\0 \t\r\n\x85  ";
  let followedWs = chars.length === 1 || ws.includes(chars[1]!);
  let prevSpace = false, prevBreak = false;
  for (let i = 0; i < chars.length; i++) {
    const ch = chars[i]!;
    if (i === 0) {
      if ("#,[]{}&*!|>'\"%@`".includes(ch)) { flowInd = true; blockInd = true; }
      if ("?:".includes(ch)) { flowInd = true; if (followedWs) blockInd = true; }
      if (ch === "-" && followedWs) { flowInd = true; blockInd = true; }
    } else {
      if (",?[]{}".includes(ch)) flowInd = true;
      if (ch === ":") { flowInd = true; if (followedWs) blockInd = true; }
      if (ch === "#" && precededWs) { flowInd = true; blockInd = true; }
    }
    if (BREAKS.includes(ch)) lineBreaks = true;
    const cp = ch.codePointAt(0)!;
    if (!(ch === "\n" || (cp >= 0x20 && cp <= 0x7e))) {
      const okUnicode = (cp === 0x85 || (cp >= 0xa0 && cp <= 0xd7ff) || (cp >= 0xe000 && cp <= 0xfffd) || (cp >= 0x10000 && cp < 0x10ffff)) && ch !== "﻿";
      if (!okUnicode) special = true; // allow_unicode=True: valid non-ASCII characters are fine
    }
    if (ch === " ") {
      if (i === 0) leadSpace = true;
      if (i === chars.length - 1) trailSpace = true;
      if (prevBreak) breakSpace = true;
      prevSpace = true; prevBreak = false;
    } else if (BREAKS.includes(ch)) {
      if (i === 0) leadBreak = true;
      if (i === chars.length - 1) trailBreak = true;
      if (prevSpace) spaceBreak = true;
      prevSpace = false; prevBreak = true;
    } else { prevSpace = false; prevBreak = false; }
    precededWs = ws.includes(ch);
    followedWs = i + 2 >= chars.length || ws.includes(chars[i + 2]!);
  }
  let allowBlockPlain = true, allowSingle = true;
  if (leadSpace || leadBreak || trailSpace || trailBreak) allowBlockPlain = false;
  if (breakSpace) { allowBlockPlain = false; allowSingle = false; }
  if (spaceBreak || special) { allowBlockPlain = false; allowSingle = false; }
  if (lineBreaks) allowBlockPlain = false;
  if (blockInd) allowBlockPlain = false;
  return { empty: false, multiline: lineBreaks, allowBlockPlain, allowSingleQuoted: allowSingle };
}

/** Minimal port of PyYAML's Emitter for one block-mapping value (width 80, indent 2, allow_unicode). */
class ScalarWriter {
  out = "";
  column: number;
  whitespace = false;
  indention = false;
  readonly indent = 2; // value inside a top-level block mapping
  readonly width = 80;
  constructor(startColumn: number) { this.column = startColumn; }

  private put(data: string) { this.column += [...data].length; this.out += data; }
  private lineBreak(data = "\n") { this.whitespace = true; this.indention = true; this.column = 0; this.out += data; }
  private writeIndent() {
    if (!this.indention || this.column > this.indent || (this.column === this.indent && !this.whitespace)) this.lineBreak();
    if (this.column < this.indent) { this.whitespace = true; this.out += " ".repeat(this.indent - this.column); this.column = this.indent; }
  }
  private indicator(ind: string, needWs: boolean) {
    const data = this.whitespace || !needWs ? ind : " " + ind;
    this.whitespace = false;
    this.indention = false;
    this.put(data);
  }

  plain(text: string) {
    if (!text) return;
    if (!this.whitespace) this.put(" ");
    this.whitespace = false; this.indention = false;
    const t = [...text];
    let spaces = false, breaks = false, start = 0, end = 0;
    while (end <= t.length) {
      const ch = end < t.length ? t[end]! : null;
      if (spaces) {
        if (ch !== " ") {
          if (start + 1 === end && this.column > this.width) { this.writeIndent(); this.whitespace = false; this.indention = false; }
          else this.put(t.slice(start, end).join(""));
          start = end;
        }
      } else if (breaks) {
        if (ch === null || !BREAKS.includes(ch)) {
          if (t[start] === "\n") this.lineBreak();
          for (const br of t.slice(start, end)) this.lineBreak(br === "\n" ? "\n" : br);
          this.writeIndent(); this.whitespace = false; this.indention = false;
          start = end;
        }
      } else if (ch === null || " \n\x85  ".includes(ch)) {
        this.put(t.slice(start, end).join(""));
        start = end;
      }
      if (ch !== null) { spaces = ch === " "; breaks = BREAKS.includes(ch); }
      end++;
    }
  }

  singleQuoted(text: string) {
    this.indicator("'", true);
    const t = [...text];
    let spaces = false, breaks = false, start = 0, end = 0;
    while (end <= t.length) {
      const ch = end < t.length ? t[end]! : null;
      if (spaces) {
        if (ch === null || ch !== " ") {
          if (start + 1 === end && this.column > this.width && start !== 0 && end !== t.length) this.writeIndent();
          else this.put(t.slice(start, end).join(""));
          start = end;
        }
      } else if (breaks) {
        if (ch === null || !BREAKS.includes(ch)) {
          if (t[start] === "\n") this.lineBreak();
          for (const br of t.slice(start, end)) this.lineBreak(br === "\n" ? "\n" : br);
          this.writeIndent();
          start = end;
        }
      } else if (ch === null || " \n\x85  ".includes(ch) || ch === "'") {
        if (start < end) { this.put(t.slice(start, end).join("")); start = end; }
      }
      if (ch === "'") { this.put("''"); start = end + 1; }
      if (ch !== null) { spaces = ch === " "; breaks = BREAKS.includes(ch); }
      end++;
    }
    this.indicator("'", false);
  }

  doubleQuoted(text: string) {
    this.indicator('"', true);
    const t = [...text];
    let start = 0, end = 0;
    while (end <= t.length) {
      const ch = end < t.length ? t[end]! : null;
      const cp = ch === null ? 0 : ch.codePointAt(0)!;
      if (ch === null || '"\\\x85  ﻿'.includes(ch) || !((cp >= 0x20 && cp <= 0x7e) || (cp >= 0xa0 && cp <= 0xd7ff) || (cp >= 0xe000 && cp <= 0xfffd))) {
        if (start < end) { this.put(t.slice(start, end).join("")); start = end; }
        if (ch !== null) {
          const data = ESCAPES[ch] !== undefined ? "\\" + ESCAPES[ch] : cp <= 0xff ? "\\x" + cp.toString(16).toUpperCase().padStart(2, "0") : cp <= 0xffff ? "\\u" + cp.toString(16).toUpperCase().padStart(4, "0") : "\\U" + cp.toString(16).toUpperCase().padStart(8, "0");
          this.put(data);
          start = end + 1;
        }
      }
      if (end > 0 && end < t.length - 1 && (ch === " " || start >= end) && this.column + (end - start) > this.width) {
        const data = t.slice(start, end).join("") + "\\";
        if (start < end) start = end;
        this.put(data);
        this.writeIndent();
        this.whitespace = false; this.indention = false;
        if (t[start] === " ") this.put("\\");
      }
      end++;
    }
    this.indicator('"', false);
  }
}

/** The text PyYAML's safe_dump produces for a string scalar value after `key:` in a block mapping. */
export function dumpStringValue(text: string, keyLength: number): string {
  const a = analyzeScalar(text);
  const writer = new ScalarWriter(keyLength + 1); // column after "key:"
  const plainOk = implicitTag(text) === "str" && !a.empty ? a.allowBlockPlain : a.empty ? false : false;
  if (plainOk) writer.plain(text);
  else if (a.allowSingleQuoted) writer.singleQuoted(text);
  else writer.doubleQuoted(text);
  return writer.out;
}

/** frontmatter.dump for the config mapping: {project_name, schema_version, directories}. */
export function dumpConfig(projectName: string, schemaVersion: number, directories: Record<string, string>): string {
  let out = `project_name:${dumpStringValue(projectName, "project_name:".length - 1)}\n`;
  out += `schema_version: ${schemaVersion}\ndirectories:\n`;
  for (const [k, v] of Object.entries(directories)) out += `  ${k}:${dumpStringValue(v, 2 + k.length)}\n`;
  return out;
}
