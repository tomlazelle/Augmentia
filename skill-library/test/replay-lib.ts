// Replay of the frozen behavioral corpus (../parity/corpus) against the Node CLI.
// Parity rules (docs/SDLC-M7-NODE-MIGRATION-PLAN.md §6.5, parity/EXCEPTIONS.md):
//  - exit code, stdout/stderr and the whole post-state tree are byte-exact; `--json` stdout is compared as parsed JSON;
//  - PARITY-EXCEPTION-002: argparse-owned help/usage prose is exempt (exit code + command/flag names required);
//  - PARITY-EXCEPTION-003: the version number differs by design.
// The corpus is never regenerated from Node.

import { spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import zlib from "node:zlib";

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const NODE_ROOT = path.join(HERE, "..", "..");
export const CORPUS_DIR = process.env["SDLC_CORPUS_DIR"] ?? path.join(NODE_ROOT, "parity", "corpus");
const BIN = process.env["SDLC_BIN"] ?? path.join(NODE_ROOT, "bin", "sdlc.js");   // SDLC_BIN: replay against an installed package

type Entry = ["d"] | ["l", string] | ["f", string];
export interface Case {
  id: string; argv: string[]; env: Record<string, string>; cwd: string; ephemeral: boolean; pre: string;
  gh_pre: Record<string, string> | null; replayable: boolean; text_parity: "exact" | "argparse";
  expected: { exit: number; stdout: string; stderr: string; post: string; gh_post: Record<string, string> | null };
}

const readJsonl = <T>(file: string): T[] =>
  zlib.gunzipSync(fs.readFileSync(path.join(CORPUS_DIR, file))).toString("utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l) as T);

export class Corpus {
  cases = readJsonl<Case>("cases.jsonl.gz");
  trees = new Map(readJsonl<{ id: string; entries: Record<string, Entry> }>("trees.jsonl.gz").map((t) => [t.id, t.entries]));
  blobs = new Map(readJsonl<{ id: string; enc: string; data: string }>("blobs.jsonl.gz").map((b) => [b.id, Buffer.from(b.data, b.enc === "utf8" ? "utf8" : "base64")]));

  materialize(treeId: string, base: string): void {
    fs.mkdirSync(base, { recursive: true });
    for (const rel of Object.keys(this.trees.get(treeId)!).sort()) {
      const entry = this.trees.get(treeId)![rel]!;
      const p = path.join(base, rel);
      if (entry[0] === "d") fs.mkdirSync(p, { recursive: true });
      else if (entry[0] === "l") { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.symlinkSync(entry[1], p); }
      else { fs.mkdirSync(path.dirname(p), { recursive: true }); fs.writeFileSync(p, this.blobs.get(entry[1])!); }
    }
  }
}

export function snapshot(base: string): Record<string, Entry> {
  const out: Record<string, Entry> = {};
  const walk = (dir: string) => {
    for (const name of fs.readdirSync(dir)) {
      const p = path.join(dir, name);
      const rel = path.relative(base, p).split(path.sep).join("/");
      const st = fs.lstatSync(p);
      if (st.isSymbolicLink()) out[rel] = ["l", fs.readlinkSync(p)];
      else if (st.isDirectory()) { out[rel] = ["d"]; walk(p); }
      else out[rel] = ["f", crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex")];
    }
  };
  walk(base);
  return out;
}

export const command = (c: Case): string => c.argv.find((a) => !a.startsWith("-")) ?? c.argv[0]!;

export interface Result { id: string; command: string; status: "pass" | "fail" | "exempt-pass" | "skipped"; problems: string[]; note?: string; digest?: string; storyItems?: number }

function runNode(args: string[], cwd: string, env: NodeJS.ProcessEnv): Promise<{ code: number; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [BIN, ...args], { cwd, env });
    let stdout = "", stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => (stderr += d));
    const timer = setTimeout(() => child.kill("SIGKILL"), 30000);
    child.on("close", (code) => { clearTimeout(timer); resolve({ code: code ?? -1, stdout, stderr }); });
  });
}

const flagNames = (text: string): string[] => [...new Set(text.match(/--[a-z][a-z-]*/g) ?? [])];

export async function replayCase(corpus: Corpus, c: Case): Promise<Result> {
  const base0 = fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-node-replay-"));
  try {
    const work = fs.realpathSync(base0);
    const base = path.join(work, "project");
    corpus.materialize(c.pre, base);
    const env: NodeJS.ProcessEnv = {};
    for (const [k, v] of Object.entries(process.env)) if (!/^(SDLC_|FAKE_GH|GH_|GITHUB_)/.test(k)) env[k] = v;
    env["COLUMNS"] = "80";
    const ghdir = path.join(work, "ghstate");
    fs.mkdirSync(ghdir);
    for (const [name, text] of Object.entries(c.gh_pre ?? {})) fs.writeFileSync(path.join(ghdir, name), text);
    const stub = path.join(work, "stubbin", "gh");
    fs.mkdirSync(path.dirname(stub), { recursive: true });
    fs.writeFileSync(stub, `#!${process.execPath}\nimport(${JSON.stringify(pathToFileURL(path.join(HERE, "stub-gh.js")).href)}).then((m) => { process.exitCode = m.stubMain(process.argv.slice(2)); });\n`);
    fs.chmodSync(stub, 0o755);
    for (const [k, v] of Object.entries(c.env)) {
      if (k === "SDLC_GH_COMMAND") env[k] = v === "<STUB_GH>" ? stub : path.join(base, v.slice("<MISSING_GH:".length, -1));
      else if (k === "FAKE_GH_STATE") env[k] = ghdir;
      else if (k === "GH_TOKEN" || k === "GITHUB_TOKEN") env[k] = "replay-token-placeholder";
      else env[k] = v;
    }
    const args = c.argv.map((a) => a.replaceAll("<ROOT>", base));
    const run = await runNode(args, path.join(base, c.cwd), env);
    const norm = (s: string) => s.replaceAll(base, "<ROOT>");
    const out = norm(run.stdout), err = norm(run.stderr);
    const exp = c.expected;
    const problems: string[] = [];
    let exempt = "";
    if (run.code !== exp.exit) problems.push(`exit ${run.code} != ${exp.exit}`);
    if (c.text_parity === "argparse") {
      // PARITY-EXCEPTION-002: exit code and command/flag names only
      const want = flagNames(exp.stdout + exp.stderr);
      const have = out + err;
      const missing = want.filter((f) => !have.includes(f));
      if (missing.length) problems.push(`argparse-exempt output lacks flag names: ${missing.join(", ")}`);
      if (exp.exit === 2 && !(err.includes("usage:") && err.includes("error:"))) problems.push("usage error lacks usage/error lines");
      exempt = "argparse text exempt (EX-002)";
    } else {
      const wantOut = c.argv[0] === "--version" ? exp.stdout.replace(/1\.0\.0rc1/, "2.0.0-rc.1") : exp.stdout;
      if (c.argv[0] === "--version") exempt = "version string differs by design (EX-003)";
      if (c.argv.includes("--json") && exp.stdout.trim()) {
        try { if (!deepEqual(JSON.parse(out), JSON.parse(wantOut))) problems.push("JSON stdout differs (parsed values)"); }
        catch { problems.push("stdout is not valid JSON"); }
      } else if (out !== wantOut) problems.push("stdout differs (bytes)");
      if (err !== exp.stderr) problems.push("stderr differs (bytes)");
    }
    const want = corpus.trees.get(exp.post)!;
    const got = snapshot(base);
    const wantHashed: Record<string, Entry> = {};
    for (const [k, v] of Object.entries(want)) wantHashed[k] = v;
    const diff = diffTrees(got, wantHashed);
    if (diff.length) problems.push("post-state tree differs: " + diff.slice(0, 6).join(", "));
    if (c.env["FAKE_GH_STATE"] && exp.gh_post !== null) {
      const gotGh: Record<string, string> = {};
      for (const name of fs.readdirSync(ghdir).sort()) gotGh[name] = fs.readFileSync(path.join(ghdir, name), "utf8");
      if (!deepEqual(gotGh, exp.gh_post)) problems.push("stub gh call log/state differs");
    }
    let digest: string | undefined, storyItems: number | undefined;
    try { const j = JSON.parse(out); digest = j?.result?.digest; storyItems = Array.isArray(j?.result?.stories) ? j.result.stories.length : undefined; } catch { /* human output */ }
    return { id: c.id, command: command(c), status: problems.length ? "fail" : exempt ? "exempt-pass" : "pass", problems, note: exempt || undefined, digest, storyItems };
  } finally {
    fs.rmSync(base0, { recursive: true, force: true });
  }
}

function diffTrees(a: Record<string, Entry>, b: Record<string, Entry>): string[] {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  return [...keys].filter((k) => JSON.stringify(a[k]) !== JSON.stringify(b[k])).sort();
}

export function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== typeof b || a === null || b === null || typeof a !== "object") return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) return a.length === (b as unknown[]).length && a.every((x, i) => deepEqual(x, (b as unknown[])[i]));
  const ka = Object.keys(a as object), kb = Object.keys(b as object);
  return ka.length === kb.length && ka.every((k) => k in (b as object) && deepEqual((a as Record<string, unknown>)[k], (b as Record<string, unknown>)[k]));
}

export const IMPLEMENTED = new Set(["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "validate", "status", "publish-preview", "publish-apply", "--version"]);

export function applicable(c: Case): boolean {
  if (!c.replayable) return false;
  const cmd = command(c);
  if (c.argv[0] === "--version") return true;
  return IMPLEMENTED.has(cmd) || (c.text_parity === "argparse" && c.argv.some((a) => IMPLEMENTED.has(a)));
}

export async function replayAll(corpus: Corpus, cases: Case[], jobs = 8): Promise<Result[]> {
  const results: Result[] = new Array(cases.length);
  let next = 0;
  await Promise.all(Array.from({ length: jobs }, async () => {
    for (;;) {
      const i = next++;
      if (i >= cases.length) return;
      results[i] = await replayCase(corpus, cases[i]!);
    }
  }));
  return results;
}
