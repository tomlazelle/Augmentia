// Python-compatible text and path helpers. The corpus was recorded from Python, so string semantics that differ from
// JavaScript (whitespace sets, repr, urllib quoting, universal newlines, Path.resolve) are reproduced here.

import fs from "node:fs";
import path from "node:path";

// Characters Python's str.isspace()/strip()/split() treat as whitespace (differs from JS String.prototype.trim()).
export const WS = "\\t\\n\\v\\f\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000";
const WS_LEAD = new RegExp(`^[${WS}]+`);
const WS_TRAIL = new RegExp(`[${WS}]+$`);
const WS_RUN = new RegExp(`[${WS}]+`);

export const strip = (s: string): string => s.replace(WS_LEAD, "").replace(WS_TRAIL, "");
export const lstrip = (s: string): string => s.replace(WS_LEAD, "");
export const rstrip = (s: string): string => s.replace(WS_TRAIL, "");
/** str.split() with no arguments: split on whitespace runs, dropping empty strings. */
export const splitWs = (s: string): string[] => strip(s).split(WS_RUN).filter((p) => p !== "");
export const isSpaceChar = (ch: string): boolean => new RegExp(`^[${WS}]$`).test(ch);

/** Compare two strings by Unicode code point (Python's ordering), not by UTF-16 code unit. */
export function cmpStr(a: string, b: string): number {
  const ia = a[Symbol.iterator](), ib = b[Symbol.iterator]();
  for (;;) {
    const x = ia.next(), y = ib.next();
    if (x.done && y.done) return 0;
    if (x.done) return -1;
    if (y.done) return 1;
    const cx = x.value.codePointAt(0)!, cy = y.value.codePointAt(0)!;
    if (cx !== cy) return cx < cy ? -1 : 1;
  }
}

/** Python tuple comparison for arrays of numbers/strings. */
export function cmpTuple(a: (number | string)[], b: (number | string)[]): number {
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const x = a[i]!, y = b[i]!;
    const c = typeof x === "number" && typeof y === "number" ? (x < y ? -1 : x > y ? 1 : 0) : cmpStr(String(x), String(y));
    if (c !== 0) return c;
  }
  return a.length - b.length < 0 ? -1 : a.length > b.length ? 1 : 0;
}

export function sortedStrings(items: Iterable<string>): string[] {
  return [...items].sort(cmpStr);
}

/** Python repr() of a str. */
export function reprStr(s: string): string {
  const quote = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = quote;
  for (const ch of s) {
    const cp = ch.codePointAt(0)!;
    if (ch === quote || ch === "\\") out += "\\" + ch;
    else if (ch === "\t") out += "\\t";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (cp < 0x20 || cp === 0x7f) out += "\\x" + cp.toString(16).padStart(2, "0");
    else if (cp < 0x7f) out += ch;
    else if (/[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u.test(ch)) {
      if (cp <= 0xff) out += "\\x" + cp.toString(16).padStart(2, "0");
      else if (cp <= 0xffff) out += "\\u" + cp.toString(16).padStart(4, "0");
      else out += "\\U" + cp.toString(16).padStart(8, "0");
    } else out += ch;
  }
  return out + quote;
}

export interface PyRepr {
  pyRepr(): string;
}
export const isPyRepr = (v: unknown): v is PyRepr => typeof v === "object" && v !== null && typeof (v as PyRepr).pyRepr === "function";

/** Python repr() for the values that can come out of YAML front matter. */
export function repr(v: unknown): string {
  if (v === null || v === undefined) return "None";
  if (typeof v === "string") return reprStr(v);
  if (typeof v === "boolean") return v ? "True" : "False";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : String(v);
  if (isPyRepr(v)) return v.pyRepr();
  if (Array.isArray(v)) return "[" + v.map(repr).join(", ") + "]";
  if (typeof v === "object") return "{" + Object.entries(v as object).map(([k, x]) => `${reprStr(k)}: ${repr(x)}`).join(", ") + "}";
  return String(v);
}

/** Python str() of a value (strings unchanged). */
export function pyStr(v: unknown): string {
  if (typeof v === "object" && v !== null && typeof (v as { pyStr?: unknown }).pyStr === "function") return (v as { pyStr(): string }).pyStr();
  return typeof v === "string" ? v : repr(v);
}

/** urllib.parse.quote(s) with the default safe="/" */
export function quote(s: string): string {
  const bytes = new TextEncoder().encode(s);
  let out = "";
  for (const b of bytes) {
    const ch = String.fromCharCode(b);
    out += /[A-Za-z0-9_.\-~/]/.test(ch) ? ch : "%" + b.toString(16).toUpperCase().padStart(2, "0");
  }
  return out;
}

/** urllib.parse.unquote(s): lenient percent-decoding with UTF-8 replacement. */
export function unquote(s: string): string {
  if (!s.includes("%")) return s;
  return s.replace(/(?:%[0-9A-Fa-f]{2})+/g, (run) => {
    const bytes = new Uint8Array(run.length / 3);
    for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(run.slice(i * 3 + 1, i * 3 + 3), 16);
    return new TextDecoder("utf-8", { fatal: false }).decode(bytes);
  });
}

/** posixpath.relpath(target, start) for absolute posix paths ("." when equal). */
export function relpath(target: string, start: string): string {
  const r = path.posix.relative(start, target);
  return r === "" ? "." : r;
}

/** pathlib.Path.resolve(): absolute, symlinks resolved for the part that exists. */
export function resolvePath(p: string): string {
  const abs = path.resolve(p);
  const rest: string[] = [];
  let cur = abs;
  for (;;) {
    try {
      const real = fs.realpathSync(cur);
      return rest.length ? path.join(real, ...rest.reverse()) : real;
    } catch {
      const parent = path.dirname(cur);
      if (parent === cur) return abs;
      rest.push(path.basename(cur));
      cur = parent;
    }
  }
}

/** Path.read_text(encoding="utf-8"): universal-newline translation (\r\n and \r become \n). */
export function readText(p: string): string {
  return decodeUtf8(fs.readFileSync(p), p).replace(/\r\n?/g, "\n");
}

/** A project text file whose bytes are not valid UTF-8 (PARITY-EXCEPTION-007: Python 1.0.0rc1 leaks a UnicodeDecodeError traceback). */
export class InvalidEncodingError extends Error {
  constructor(readonly file: string) { super("file is not valid UTF-8"); }
}

const STRICT_UTF8 = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }); // a leading BOM is kept, as Python's utf-8 codec does
export function decodeUtf8(bytes: Uint8Array, file: string): string {
  try { return STRICT_UTF8.decode(bytes); } catch { throw new InvalidEncodingError(file); }
}

export const isDir = (p: string): boolean => {
  try { return fs.statSync(p).isDirectory(); } catch { return false; }
};
export const isFile = (p: string): boolean => {
  try { return fs.statSync(p).isFile(); } catch { return false; }
};
export const exists = (p: string): boolean => {
  try { fs.statSync(p); return true; } catch { return false; }
};
/** os.path.lexists: true even for dangling symlinks. */
export const lexists = (p: string): boolean => {
  try { fs.lstatSync(p); return true; } catch { return false; }
};

/** ledger.atomic_write: write `<name>.tmp` then rename over the target. */
export function atomicWrite(target: string, text: string): void {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  const tmp = target + ".tmp";
  fs.writeFileSync(tmp, text, "utf8");
  fs.renameSync(tmp, target);
}

export function daysInMonth(y: number, m: number): number {
  return [31, (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0 ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]!;
}

/** datetime.date.fromisoformat validity for YYYY-MM-DD. */
export function isRealDate(value: string): boolean {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!m) return false;
  const y = +m[1]!, mo = +m[2]!, d = +m[3]!;
  return y >= 1 && mo >= 1 && mo <= 12 && d >= 1 && d <= daysInMonth(y, mo);
}

/** Today's date (local, not UTC): SDLC_TODAY overrides. */
export function today(): string {
  const env = process.env["SDLC_TODAY"];
  if (env) return env;
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** The digits after position `places` of the exact decimal expansion of x tell whether x is an exact tie at `places`. */
function isExactTie(x: number, places: number): boolean {
  const exact = Math.abs(x).toFixed(Math.min(100, places + 25));
  const frac = exact.split(".")[1]!;
  return frac[places] === "5" && /^0*$/.test(frac.slice(places + 1));
}

/** Python's round-half-even to `places` decimals, as a string (what `f"{x:.{places}f}"` prints). */
export function fixed(x: number, places: number): string {
  if (!isExactTie(x, places)) return x.toFixed(places);
  const scaled = Math.abs(x) * 10 ** places; // an exact tie scales exactly to n + 0.5
  const n = Math.floor(scaled);
  const rounded = (n % 2 === 0 ? n : n + 1) / 10 ** places;
  return (x < 0 ? -rounded : rounded).toFixed(places);
}

/** round(x, places) with Python's round-half-even on the exact binary value. */
export const pyRound = (x: number, places: number): number => Number(fixed(x, places));

const ERRNO: Record<string, [number, string]> = {
  EPERM: [1, "Operation not permitted"], ENOENT: [2, "No such file or directory"], EIO: [5, "Input/output error"], EACCES: [13, "Permission denied"],
  EEXIST: [17, "File exists"], ENOTDIR: [20, "Not a directory"], EISDIR: [21, "Is a directory"], EINVAL: [22, "Invalid argument"],
  EMFILE: [24, "Too many open files"], ENOSPC: [28, "No space left on device"], EROFS: [30, "Read-only file system"], ENAMETOOLONG: [36, "File name too long"],
  ENOTEMPTY: [39, "Directory not empty"], ELOOP: [40, "Too many levels of symbolic links"],
};

/** str(OSError) as CPython formats it: `[Errno 21] Is a directory: '/path'`. Other errors use their message. */
export function pyErrorString(err: unknown): string {
  const e = err as NodeJS.ErrnoException;
  const known = e && typeof e.code === "string" ? ERRNO[e.code] : undefined;
  if (!known) return e instanceof Error ? e.message : String(err);
  const dest = (e as { dest?: string }).dest;
  const where = e.path ? `: ${reprStr(e.path)}${dest ? ` -> ${reprStr(dest)}` : ""}` : "";
  return `[Errno ${known[0]}] ${known[1]}${where}`;
}

/** json.dumps(value) with Python's defaults (ensure_ascii=True, separators ", " and ": ") for strings/arrays/objects/null/bool/int. */
export function pyJsonDumps(value: unknown): string {
  if (value === null || value === undefined) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (typeof value === "string") {
    let out = '"';
    for (let i = 0; i < value.length; i++) {
      const ch = value[i]!;
      const cp = ch.charCodeAt(0);
      if (ch === '"') out += '\\"';
      else if (ch === "\\") out += "\\\\";
      else if (ch === "\n") out += "\\n";
      else if (ch === "\r") out += "\\r";
      else if (ch === "\t") out += "\\t";
      else if (ch === "\b") out += "\\b";
      else if (ch === "\f") out += "\\f";
      else if (cp < 0x20 || cp > 0x7e) out += "\\u" + cp.toString(16).padStart(4, "0"); // ensure_ascii: UTF-16 units, so astral characters become surrogate pairs
      else out += ch;
    }
    return out + '"';
  }
  if (Array.isArray(value)) return "[" + value.map(pyJsonDumps).join(", ") + "]";
  const o = value as Record<string, unknown>;
  return "{" + Object.keys(o).map((k) => `${pyJsonDumps(k)}: ${pyJsonDumps(o[k])}`).join(", ") + "}";
}

/** json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")): the canonical bytes hashed for confirmation digests. */
export function canonicalJson(value: unknown): string {
  const sort = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(sort);
    if (v !== null && typeof v === "object") {
      const o = v as Record<string, unknown>;
      return Object.fromEntries(Object.keys(o).sort(cmpStr).map((k) => [k, sort(o[k])]));
    }
    return v;
  };
  return JSON.stringify(sort(value));
}
