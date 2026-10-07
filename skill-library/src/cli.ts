// Command-line interface: sdlc <command> [--root DIR] [--json] (port of sdlc/cli.py).
//
// Option parsing follows argparse's behavior (exit code 2 for usage errors, unique-prefix abbreviations, `--opt=value`,
// interleaved positionals) but its help/usage prose is our own deterministic text (PARITY-EXCEPTION-002).

import path from "node:path";
import { createArtifactDir, initProject } from "./init.js";
import { allocateDocument, allocateRequirement, retire } from "./ids.js";
import { updateMaps, specs } from "./maps.js";
import { findOverlaps, listDocuments, references } from "./query.js";
import { applyPublication, buildPreview } from "./publish.js";
import { buildStatus } from "./status.js";
import { validate } from "./validate.js";
import { ARTIFACT_SUBDIRS, DOC_CATEGORIES, DOC_STATUSES, Diagnostic, Outcome } from "./model.js";
import { Project, findRoot } from "./project.js";
import { fixed, isDir, resolvePath } from "./pyfmt.js";
import { VERSION } from "./version.js";

export const JSON_SCHEMA_VERSION = 1;

interface OptSpec { name: string; value: boolean; multi?: boolean; choices?: readonly string[]; required?: boolean; dest: string; help: string }
interface Positional { dest: string; many?: boolean; optional?: boolean; help: string }
interface CommandSpec { help: string; options: OptSpec[]; positionals: Positional[]; exclusive?: [string, string] }

const common: OptSpec[] = [
  { name: "--root", value: true, dest: "root", help: "project root (default: nearest ancestor containing .sdlc/)" },
  { name: "--json", value: false, dest: "json", help: "emit machine-readable JSON" },
];

const COMMANDS: Record<string, CommandSpec> = {
  init: { help: "idempotently create the standard project structure (and AGENTS.md/CLAUDE.md if missing)", options: [{ name: "--project-name", value: true, dest: "projectName", help: "project name for a new .sdlc/config.md (default: directory name)" }], positionals: [] },
  "allocate-id": { help: "reserve the next document or requirement ID", options: [
    { name: "--category", value: true, choices: DOC_CATEGORIES, dest: "category", help: "document category" },
    { name: "--requirement", value: true, dest: "requirement", help: "allocate the next requirement ID in this document" },
    { name: "--title", value: true, dest: "title", help: "document title (used to compute the target path)" }], positionals: [], exclusive: ["category", "requirement"] },
  "retire-id": { help: "tombstone a document or requirement ID", options: [
    { name: "--replaced-by", value: true, dest: "replacedBy", help: "ID that replaces it" }, { name: "--note", value: true, dest: "note", help: "ledger note" }], positionals: [{ dest: "id", help: "ID to retire" }] },
  "create-dir": { help: "create an Artifacts subdirectory and its map on first use", options: [{ name: "--artifact", value: true, required: true, choices: Object.keys(ARTIFACT_SUBDIRS).sort(), dest: "artifact", help: "artifact directory" }], positionals: [] },
  "update-map": { help: "regenerate the generated region of map.md files", options: [], positionals: [{ dest: "directory", optional: true, help: "managed directory (default: every map)" }] },
  list: { help: "list documents with their metadata", options: [{ name: "--category", value: true, choices: DOC_CATEGORIES, dest: "category", help: "category" }, { name: "--status", value: true, choices: DOC_STATUSES, dest: "status", help: "status" }], positionals: [] },
  references: { help: "outgoing and incoming references for an ID", options: [], positionals: [{ dest: "id", help: "document or requirement ID" }] },
  "find-overlaps": { help: "rank existing documents that may overlap a proposed one", options: [
    { name: "--category", value: true, required: true, choices: DOC_CATEGORIES, dest: "category", help: "category" },
    { name: "--title", value: true, required: true, dest: "title", help: "proposed title" },
    { name: "--purpose", value: true, dest: "purpose", help: "proposed purpose" },
    { name: "--covers", value: true, multi: true, dest: "covers", help: "search hint: requirement or document IDs" }], positionals: [] },
  status: { help: "read-only progress snapshot: health, inventory, delivery, traceability, attention", options: [], positionals: [] },
  "publish-preview": { help: "render the exact GitHub Issue(s) that would be created for the named Stories (offline; never mutates)", options: [], positionals: [{ dest: "stories", many: true, optional: true, help: "Stories to publish (none are selected by default)" }] },
  "publish-apply": { help: "create the previewed GitHub Issue(s); refuses unless --confirm-digest matches a fresh preview", options: [{ name: "--confirm-digest", value: true, dest: "confirmDigest", help: "the digest shown by publish-preview, supplied only after explicit human confirmation" }], positionals: [{ dest: "stories", many: true, optional: true, help: "Stories to publish" }] },
  validate: { help: "check structure, metadata, IDs, links, maps and traceability", options: [], positionals: [] },
};

class UsageError extends Error {
  constructor(message: string, public command?: string) { super(message); }
}

export interface Args {
  command: string;
  root?: string;
  json: boolean;
  [dest: string]: unknown;
}

function usageLine(command?: string): string {
  if (!command) return `usage: sdlc [-h] [--version] <command> ...`;
  const spec = COMMANDS[command]!;
  const opts = [...spec.options, ...common].map((o) => {
    const meta = o.value ? ` ${o.dest.toUpperCase()}${o.multi ? " [...]" : ""}` : "";
    return o.required || (spec.exclusive && spec.exclusive.includes(o.dest) && false) ? `${o.name}${meta}` : `[${o.name}${meta}]`;
  });
  const pos = spec.positionals.map((p) => (p.many ? `[${p.dest}...]` : p.optional ? `[${p.dest}]` : p.dest));
  return `usage: sdlc ${command} [-h] ${[...opts, ...pos].join(" ")}`;
}

function helpText(command?: string): string {
  if (!command) {
    const lines = [usageLine(), "", "Deterministic helper CLI for the SDLC Skill library.", "", "commands:"];
    for (const [name, spec] of Object.entries(COMMANDS)) lines.push(`  ${name.padEnd(16)} ${spec.help}`);
    lines.push("", "options:", "  -h, --help       show this help message and exit", "  --version        show the version and exit");
    return lines.join("\n") + "\n";
  }
  const spec = COMMANDS[command]!;
  const lines = [usageLine(command), "", spec.help, ""];
  if (spec.positionals.length) { lines.push("positional arguments:"); for (const p of spec.positionals) lines.push(`  ${p.dest.padEnd(18)} ${p.help}`); lines.push(""); }
  lines.push("options:", "  -h, --help         show this help message and exit");
  for (const o of [...spec.options, ...common]) {
    const flag = o.value ? `${o.name} ${o.dest.toUpperCase()}` : o.name;
    lines.push(`  ${flag.padEnd(18)} ${o.help}${o.choices ? ` (choices: ${o.choices.join(", ")})` : ""}`);
  }
  return lines.join("\n") + "\n";
}

const NEGATIVE_NUMBER = /^-\d+$|^-\d*\.\d+$/;

/** argparse's classification of an argument string: option-like ('O') unless it is a value ('A'). */
function looksLikeOption(tok: string, all: OptSpec[]): boolean {
  if (!tok.startsWith("-") || tok === "-") return false;
  const name = tok.split("=")[0]!;
  if (tok === "-h" || all.some((o) => o.name === name || o.name.startsWith(name)) || (tok.startsWith("--") && "--help".startsWith(name))) return true;
  if (NEGATIVE_NUMBER.test(tok) || tok.includes(" ")) return false;
  return true;
}

export type Parsed = { kind: "help"; text: string } | { kind: "version" } | { kind: "args"; args: Args };

export function parseArgs(argv: string[]): Parsed {
  let i = 0;
  // top-level: help, version, command
  for (; i < argv.length; i++) {
    const a = argv[i]!;
    if (a === "-h" || a === "--help") return { kind: "help", text: helpText() };
    if (a === "--version") return { kind: "version" };
    if (a === "--") { i++; break; }
    if (a.startsWith("-") && a.length > 1) {
      const longs = ["--help", "--version"].filter((l) => l.startsWith(a.split("=")[0]!));
      if (a.startsWith("--") && longs.length === 1) return longs[0] === "--help" ? { kind: "help", text: helpText() } : { kind: "version" };
      throw new UsageError(`unrecognized arguments: ${a}`);
    }
    break;
  }
  const command = argv[i];
  if (command === undefined) throw new UsageError("the following arguments are required: <command>");
  if (!(command in COMMANDS)) throw new UsageError(`argument <command>: invalid choice: '${command}' (choose from ${Object.keys(COMMANDS).map((c) => `'${c}'`).join(", ")})`);
  const spec = COMMANDS[command]!;
  const all = [...spec.options, ...common];
  const result: Args = { command, json: false };
  const positionals: string[] = [];
  const rest = argv.slice(i + 1);
  let afterDashes = false;
  for (let k = 0; k < rest.length; k++) {
    const tok = rest[k]!;
    if (afterDashes || !tok.startsWith("-") || tok === "-" || NEGATIVE_NUMBER.test(tok)) { positionals.push(tok); continue; }
    if (tok === "--") { afterDashes = true; continue; }
    if (tok === "-h" || tok === "--help") return { kind: "help", text: helpText(command) };
    if (!tok.startsWith("--")) { if (tok.includes(" ")) { positionals.push(tok); continue; } throw new UsageError(`unrecognized arguments: ${tok}`, command); }
    const [name, inline] = splitInline(tok);
    let matches = all.filter((o) => o.name === name);
    if (matches.length === 0) matches = all.filter((o) => o.name.startsWith(name));
    if (matches.length === 0 && "--help".startsWith(name)) return { kind: "help", text: helpText(command) };
    if (matches.length === 0 && tok.includes(" ")) { positionals.push(tok); continue; } // argparse: an unknown '-…' argument containing a space is a value, not an option
    if (matches.length === 0) throw new UsageError(`unrecognized arguments: ${tok}`, command);
    if (matches.length > 1) throw new UsageError(`ambiguous option: ${name} could match ${matches.map((m) => m.name).join(", ")}`, command);
    const opt = matches[0]!;
    if (!opt.value) {
      if (inline !== undefined) throw new UsageError(`argument ${opt.name}: ignored explicit argument '${inline}'`, command);
      result[opt.dest] = true;
      continue;
    }
    const values: string[] = [];
    if (inline !== undefined) values.push(inline);
    else {
      while (k + 1 < rest.length) {
        const nxt = rest[k + 1]!;
        if (nxt === "--" || looksLikeOption(nxt, all)) break;
        values.push(nxt);
        k++;
        if (!opt.multi) break;
      }
    }
    if (values.length === 0) throw new UsageError(`argument ${opt.name}: expected ${opt.multi ? "at least one argument" : "one argument"}`, command);
    for (const v of values) {
      if (opt.choices && !opt.choices.includes(v)) throw new UsageError(`argument ${opt.name}: invalid choice: '${v}' (choose from ${opt.choices.map((c) => `'${c}'`).join(", ")})`, command);
    }
    result[opt.dest] = opt.multi ? values : values[0];
  }
  // positionals
  let pi = 0;
  for (const p of spec.positionals) {
    if (p.many) { result[p.dest] = positionals.slice(pi); pi = positionals.length; continue; }
    if (pi < positionals.length) result[p.dest] = positionals[pi++];
    else if (!p.optional) throw new UsageError(`the following arguments are required: ${p.dest}`, command);
  }
  if (pi < positionals.length) throw new UsageError(`unrecognized arguments: ${positionals.slice(pi).join(" ")}`, command);
  for (const o of spec.options) if (o.required && result[o.dest] === undefined) throw new UsageError(`the following arguments are required: ${o.name}`, command);
  if (spec.exclusive) {
    const [a, b] = spec.exclusive;
    const optA = spec.options.find((o) => o.dest === a)!, optB = spec.options.find((o) => o.dest === b)!;
    if (result[a] !== undefined && result[b] !== undefined) throw new UsageError(`argument ${optB.name}: not allowed with argument ${optA.name}`, command);
    if (result[a] === undefined && result[b] === undefined) throw new UsageError(`one of the arguments ${optA.name} ${optB.name} is required`, command);
  }
  return { kind: "args", args: result };
}

function splitInline(tok: string): [string, string | undefined] {
  const eq = tok.indexOf("=");
  return eq === -1 ? [tok, undefined] : [tok.slice(0, eq), tok.slice(eq + 1)];
}

function envelope(command: string, out: Outcome) {
  return { schema_version: JSON_SCHEMA_VERSION, command, ok: out.exitCode === 0, exit_code: out.exitCode, result: out.result, diagnostics: out.diagnostics.map((d) => d.toDict()) };
}

function human(command: string, out: Outcome): string {
  const r = out.result as Record<string, any>;
  const lines: string[] = [];
  if (command === "init") {
    if ("root" in r) {
      lines.push(`Initialized SDLC project at ${r["root"]}`);
      lines.push(...r["created"].map((p: string) => `  created:  ${p}`), ...r["existing"].map((p: string) => `  existing: ${p}`));
    }
  } else if (command === "allocate-id" && Object.keys(r).length) {
    lines.push(r["id"]);
    if (r["path"]) lines.push(`path: ${r["path"]}`);
    else if (r["directory"]) lines.push(`directory: ${r["directory"]}`);
  } else if (command === "retire-id" && Object.keys(r).length) {
    lines.push(`Retired ${r["id"]}` + (r["replaced_by"] ? ` (replaced by ${r["replaced_by"]})` : ""));
  } else if (command === "create-dir" && Object.keys(r).length) {
    lines.push(`${r["directory_created"] ? "Created" : "Found"} ${r["directory"]}/`);
    for (const [k, v] of Object.entries(r)) if (k.endsWith("_map")) lines.push(`  ${k}: ${v}`);
  } else if (command === "update-map") {
    for (const state of ["created", "updated", "unchanged", "blocked"]) for (const p of (r[state] ?? []) as string[]) lines.push(`${state}: ${p}`);
  } else if (command === "list") {
    for (const d of (r["documents"] ?? []) as Record<string, string>[]) {
      const extra = d["delivery_status"] ? `  [${d["delivery_status"]}]` : "";
      lines.push(`${d["id"]!.padEnd(10)} ${d["status"]!.padEnd(11)} ${d["title"]}${extra}  (${d["path"]})`);
    }
    lines.push(`${r["count"] ?? 0} document(s)`);
  } else if (command === "references" && Object.keys(r).length) {
    lines.push(`${r["id"]} (${r["kind"]}, ${r["state"]})` + (r["title"] ? ` — ${r["title"]}` : ""));
    if (r["defined_in"]) lines.push(`defined in: ${r["defined_in"].id} (${r["defined_in"].path})`);
    lines.push("outgoing:");
    for (const o of r["outgoing"] as Record<string, any>[]) {
      const tgt = o["target"]?.id || o["target"]?.path || (o["requirements"] as string[]).join(", ");
      lines.push(`  ${o["relationship"]}: ${tgt}`);
    }
    lines.push("incoming:");
    for (const i of r["incoming"] as Record<string, any>[]) {
      const reqs = (i["requirements"] as string[]).length ? ` (${(i["requirements"] as string[]).join(", ")})` : "";
      lines.push(`  ${i["relationship"]}: ${i["source"].id}${reqs}`);
    }
  } else if (command === "find-overlaps" && Object.keys(r).length) {
    const cands = r["candidates"] as Record<string, any>[];
    if (!cands.length) lines.push("No plausible overlaps found.");
    for (const c of cands) {
      lines.push(`${String(c["level"]).padEnd(8)} ${fixed(c["score"], 2)}  ${c["id"]} ${c["title"]}  (${c["path"]})`);
      for (const reason of c["reasons"] as string[]) lines.push(`           - ${reason}`);
    }
    if (cands.length) lines.push("Ask the user whether to revise/extend an existing document or create a new one.");
  } else if (command === "status" && Object.keys(r).length) {
    lines.push(...humanStatus(r));
  } else if ((command === "publish-preview" || command === "publish-apply") && Object.keys(r).length) {
    lines.push(...humanPublish(command, r));
  } else if (command === "validate" && Object.keys(r).length) {
    const sm = r["summary"];
    lines.push(`${r["documents"]} document(s): ${sm.error} error(s), ${sm.warning} warning(s), ${sm.notice} notice(s)`);
  }
  return lines.join("\n");
}

function humanStatus(r: Record<string, any>): string[] {
  const h = r["health"], sm = h["summary"];
  const lines = ["# Project status", "", "## Project health",
    `- Validation: ${h["ok"] ? "OK" : "ERRORS"} — ${sm.error} error(s), ${sm.warning} warning(s), ${sm.notice} notice(s) across ${h["documents"]} document(s)`];
  if (h["stale_maps"].length) lines.push(`- Stale or missing maps: ${h["stale_maps"].join(", ")}`);
  for (const b of h["broken_references"]) lines.push(`- Broken reference: ${b.message} (${b.path})`);
  lines.push("", "## Document inventory");
  for (const [cat, row] of Object.entries(r["inventory"]) as [string, any][]) {
    if (row.total) {
      const parts = [...Object.entries(row.by_status).filter(([, n]) => n).map(([name, n]) => `${n} ${name}`), ...(row.invalid ? [`${row.invalid} invalid`] : [])];
      lines.push(`- ${cat}: ${row.total} (${parts.join(", ")})`);
    } else lines.push(`- ${cat}: none`);
  }
  lines.push("", "## Story delivery");
  for (const [name, items] of Object.entries(r["delivery"]) as [string, any[]][]) lines.push(`- ${name}: ${items.length}` + (items.length ? ` (${items.map((i) => i.id).join(", ")})` : ""));
  const t = r["traceability"];
  lines.push("", "## Traceability",
    `- Uncovered PR requirements (notice): ${t["uncovered_requirements"].join(", ") || "none"}`,
    `- Standalone Stories, covers [] (notice): ${t["standalone_stories"].join(", ") || "none"}`,
    `- Invalid references: ${t["invalid_references"].length || "none"}`,
    `- Unresolved acceptance behavior (TBD): ${t["unresolved_tbd"].join(", ") || "none"}`,
    "", "## Needs attention / next actions");
  const attention = (r["attention"] as any[]).map((a) => `- [${a.kind}] ${a.id ?? ""} ${a.message}`.replaceAll("  ", " "));
  lines.push(...(attention.length ? attention : ["- Nothing needs attention."]));
  if (r["empty"]) lines.push("", "No documents yet: start with create-brd, create-prd or create-stories.");
  return lines;
}

function humanPublish(command: string, r: Record<string, any>): string[] {
  const lines = [`Target: ${r["provider"]} ${r["repository"]}   (access is checked only when applying)`];
  for (const s of r["stories"] as any[]) {
    lines.push("", `=== ${s.id} — ${String(s.action).toUpperCase()} ===`);
    if (s.action === "blocked") { lines.push(`blocked: ${s.blockers.join(", ")}`); continue; }
    lines.push(`Title: ${s.issue_title}`, "Labels: none", "Body:", "", ...s.issue_body.replace(/\n+$/, "").split("\n").map((ln: string) => `    ${ln}`));
    if (s.known_publication) {
      const k = s.known_publication;
      lines.push(`Known publication: ${k.repository}${k.issue} ${k.url || ""}`.replace(/[\s]+$/, ""));
    }
    for (const o of s.other_publications ?? []) lines.push(`Also published elsewhere: ${o.provider}:${o.repository}${o.issue} (does not block this repository)`);
  }
  lines.push("", `Will create: ${r["will_create"].join(", ") || "nothing"}`);
  if (r["digest"]) lines.push(`Digest: ${r["digest"]}`);
  if (command === "publish-preview") lines.push("Preview only — no external mutation was made. Publish only after explicit human confirmation.");
  else {
    for (const o of (r["outcomes"] ?? []) as any[]) {
      const detail = o.url || o.issue || o.reason || o.error || "";
      lines.push(`${o.id}: ${o.outcome} ${detail}`.replace(/[\s]+$/, ""));
    }
    lines.push(`External mutations: ${r["mutations"]}`);
  }
  return lines;
}

function emit(command: string, out: Outcome, asJson: boolean, stdout: (s: string) => void, stderr: (s: string) => void): void {
  if (asJson) { stdout(JSON.stringify(envelope(command, out), null, 2) + "\n"); return; }
  const body = human(command, out);
  if (command === "validate") {
    for (const d of out.diagnostics) stdout(d.human() + "\n");
    stdout(body + "\n");
    return;
  }
  if (body) stdout(body + "\n");
  for (const d of out.diagnostics) stderr(d.human() + "\n");
}

function resolveRoot(args: Args): [string | null, Diagnostic | null] {
  if (args.root !== undefined) {
    const root = resolvePath(args.root);
    if (args.command === "init") return [root, null];
    if (!isDir(path.join(root, ".sdlc"))) return [null, new Diagnostic("error", "no-project", `${root} is not an SDLC project (no .sdlc/); run 'sdlc init'`)];
    return [root, null];
  }
  const found = findRoot(process.cwd());
  if (found) return [found, null];
  if (args.command === "init") return [process.cwd(), null];
  return [null, new Diagnostic("error", "no-project", "no .sdlc/ found in this or any parent directory; run 'sdlc init'")];
}

export function run(args: Args): Outcome {
  const [root, problem] = resolveRoot(args);
  if (problem) return new Outcome(2, {}, [problem]);
  if (args.command === "init") return initProject(root!, (args["projectName"] as string | undefined) ?? null);
  const project = Project.open(root!);
  switch (args.command) {
    case "allocate-id":
      if (args["requirement"] !== undefined) return allocateRequirement(project, args["requirement"] as string);
      return allocateDocument(project, args["category"] as string, (args["title"] as string | undefined) ?? null);
    case "retire-id":
      return retire(project, args["id"] as string, (args["replacedBy"] as string | undefined) ?? null, (args["note"] as string | undefined) ?? null);
    case "create-dir":
      return createArtifactDir(project, args["artifact"] as string);
    case "update-map": return updateMapCommand(project, args["directory"] as string | undefined);
    case "list": return listDocuments(project, (args["category"] as string | undefined) ?? null, (args["status"] as string | undefined) ?? null);
    case "references": return references(project, args["id"] as string);
    case "find-overlaps": return findOverlaps(project, args["category"] as string, args["title"] as string, (args["purpose"] as string | undefined) ?? null, (args["covers"] as string[] | undefined) ?? []);
    case "validate": return validate(project);
    case "status": return buildStatus(project);
    case "publish-preview": return buildPreview(project, (args["stories"] as string[] | undefined) ?? []);
    case "publish-apply": return applyPublication(project, (args["stories"] as string[] | undefined) ?? [], (args["confirmDigest"] as string | undefined) ?? null);
    default:
      return new Outcome(2, {}, [new Diagnostic("error", "not-implemented", `'${args.command}' is not implemented in this build yet`)]);
  }
}

function updateMapCommand(project: Project, directory: string | undefined): Outcome {
  let only = null;
  if (directory !== undefined) {
    const target = resolvePath(path.isAbsolute(directory) ? directory : path.join(process.cwd(), directory));
    only = specs(project).find((s) => resolvePath(s.directory) === target) ?? null;
    if (only === null) return new Outcome(2, {}, [new Diagnostic("error", "bad-directory", `${directory} is not a managed directory with a map`)]);
  }
  const [result, diags] = updateMaps(project, only);
  return new Outcome(diags.length ? 1 : 0, result, diags);
}

export interface IO { stdout(s: string): void; stderr(s: string): void }

export function main(argv: string[], io: IO = { stdout: (s) => { process.stdout.write(s); }, stderr: (s) => { process.stderr.write(s); } }): number {
  let parsed;
  try { parsed = parseArgs(argv); }
  catch (exc) {
    if (exc instanceof UsageError) {
      io.stderr(`${usageLine(exc.command)}\nsdlc${exc.command ? " " + exc.command : ""}: error: ${exc.message}\n`);
      return 2;
    }
    throw exc;
  }
  if (parsed.kind === "help") { io.stdout(parsed.text); return 0; }
  if (parsed.kind === "version") { io.stdout(`sdlc ${VERSION}\n`); return 0; }
  const out = run(parsed.args);
  emit(parsed.args.command, out, parsed.args.json, io.stdout, io.stderr);
  return out.exitCode;
}
