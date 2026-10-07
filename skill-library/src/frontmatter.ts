// YAML front matter splitting and parsing (port of sdlc/frontmatter.py).

import { lstrip, strip } from "./pyfmt.js";
import { dumpConfig, PyDate, safeLoad, YamlError, type PyValue } from "./yaml.js";

/** (raw front matter or null, 0-based index of the first body line). */
export function split(text: string): [string | null, number] {
  const lines = text.split("\n");
  if (lines.length === 0 || strip(lstrip(lines[0]!.replace(/^﻿+/, ""))) !== "---") return [null, 0];
  for (let i = 1; i < lines.length; i++) {
    const s = strip(lines[i]!);
    if (s === "---" || s === "...") return [lines.slice(1, i).join("\n"), i + 1];
  }
  return [null, 0];
}

function normalise(value: PyValue): PyValue {
  if (value instanceof PyDate) return value.iso();
  if (Array.isArray(value)) return value.map(normalise);
  if (value !== null && typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    const out: { [key: string]: PyValue } = {};
    for (const [k, v] of Object.entries(value)) out[k] = normalise(v as PyValue);
    return out;
  }
  return value; // PyDateTime and scalars are kept as parsed
}

/** Parse into a mapping; dates become ISO strings. Throws Error(message) (a Python ValueError). */
export function parse(raw: string): Record<string, PyValue> {
  let data: PyValue;
  try {
    data = safeLoad(raw);
  } catch (exc) {
    if (exc instanceof YamlError) {
      if (exc.kind === "yaml") {
        const first = strip(exc.message).split("\n")[0] ?? "";
        throw new Error(`invalid YAML: ${strip(exc.message) ? first : "invalid YAML"}`);
      }
      throw new Error(`invalid YAML value: ${exc.message}`);
    }
    throw exc;
  }
  if (data === null) return {};
  if (typeof data !== "object" || Array.isArray(data) || Object.getPrototypeOf(data) !== Object.prototype) throw new Error("front matter must be a YAML mapping");
  const out: Record<string, PyValue> = {};
  for (const [k, v] of Object.entries(data as { [key: string]: PyValue })) out[k] = normalise(v);
  return out;
}

export { dumpConfig };
