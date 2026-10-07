// Shared helpers for publishing tests: in-process CLI, throwaway projects, and the stub `gh` wrapper.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";
import { main } from "../src/cli.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));

export interface Run { code: number; out: string; err: string; json: any }

export function cli(args: string[], cwd: string): Run {
  const saved = process.cwd();
  process.chdir(cwd);
  try {
    let out = "", err = "";
    const code = main(args, { stdout: (s) => (out += s), stderr: (s) => (err += s) });
    let json: any = null;
    if (args.includes("--json")) { try { json = JSON.parse(out); } catch { /* not JSON */ } }
    return { code, out, err, json };
  } finally { process.chdir(saved); }
}

export const tmpdir = (prefix = "sdlc-t-"): string => fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), prefix)));

/** A stub `gh` executable (outside any project) driven by mode.json; sets SDLC_GH_COMMAND/FAKE_GH_STATE for in-process calls. */
export class Stub {
  readonly dir = tmpdir("sdlc-stub-");
  readonly state = path.join(this.dir, "state");
  readonly script = path.join(this.dir, "gh");
  constructor() {
    fs.mkdirSync(this.state);
    fs.writeFileSync(this.script, `#!${process.execPath}\nimport(${JSON.stringify(pathToFileURL(path.join(HERE, "stub-gh.js")).href)}).then((m) => { process.exitCode = m.stubMain(process.argv.slice(2)); });\n`);
    fs.chmodSync(this.script, 0o755);
  }
  use(): this { process.env["SDLC_GH_COMMAND"] = this.script; process.env["FAKE_GH_STATE"] = this.state; return this; }
  mode(mode: Record<string, unknown>): void { fs.writeFileSync(path.join(this.state, "mode.json"), JSON.stringify(mode)); }
  calls(): { argv: string[]; stdin: string | null }[] {
    const f = path.join(this.state, "calls.jsonl");
    return fs.existsSync(f) ? fs.readFileSync(f, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)) : [];
  }
  creates(): { argv: string[]; stdin: string | null }[] { return this.calls().filter((c) => c.argv[0] === "issue" && c.argv[1] === "create"); }
  cleanup(): void { delete process.env["SDLC_GH_COMMAND"]; delete process.env["FAKE_GH_STATE"]; fs.rmSync(this.dir, { recursive: true, force: true }); }
}

export const BASE_FILES: Record<string, string> = JSON.parse(fs.readFileSync(path.join(process.env["SDLC_PARITY_DIR"] ?? path.join(HERE, "..", "..", "parity"), "digest-matrix.json"), "utf8")).base_files;

/** The standard publishing test project (BR-001, PR-001, US-001, US-002) with `publishing` pointing at `repository`. */
export function project(repository = "acme/widgets", files: Record<string, string> = BASE_FILES): string {
  const d = tmpdir("sdlc-p-");
  process.env["SDLC_TODAY"] = "2026-09-29";
  cli(["init", "--project-name", "Matrix"], d);
  for (const [rel, text] of Object.entries(files)) fs.writeFileSync(path.join(d, rel), text);
  setRepository(d, repository);
  cli(["update-map"], d);
  return d;
}

export function setRepository(d: string, repository: string): void {
  const cfg = path.join(d, ".sdlc", "config.md");
  let text = fs.readFileSync(cfg, "utf8");
  text = /\npublishing:\n {2}provider: github\n {2}repository: [^\n]*\n/.test(text)
    ? text.replace(/(\npublishing:\n {2}provider: github\n {2}repository: )[^\n]*\n/, `$1${repository}\n`)
    : text.replace("\n---\n\n#", `\npublishing:\n  provider: github\n  repository: ${repository}\n---\n\n#`);
  fs.writeFileSync(cfg, text);
}

export const digestOf = (r: Run): string => r.json.result.digest as string;
export const preview = (d: string, ...ids: string[]): Run => cli(["publish-preview", ...ids, "--json"], d);
export const apply = (d: string, digest: string | null, ...ids: string[]): Run => cli(["publish-apply", ...ids, ...(digest ? ["--confirm-digest", digest] : []), "--json"], d);
export const read = (d: string, rel: string): string => fs.readFileSync(path.join(d, rel), "utf8");
export const US1 = "Stories/US-001-export-report.md";
export const US2 = "Stories/US-002-archive-old.md";

export function tree(d: string): Record<string, string> {
  const out: Record<string, string> = {};
  const walk = (dir: string) => {
    for (const name of fs.readdirSync(dir)) {
      const p = path.join(dir, name);
      if (fs.statSync(p).isDirectory()) walk(p); else out[path.relative(d, p)] = fs.readFileSync(p, "utf8");
    }
  };
  walk(d);
  return out;
}
