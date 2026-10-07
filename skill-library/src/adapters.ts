// Symlink installer behind `sdlc-install-claude-code` and `sdlc-install-codex` (port of sdlc/adapters.py).
// Skills are never copied: each `skills/<name>` directory is symlinked into the agent's skill-discovery directory,
// so the packaged library stays the only source of Skill text.

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { resolvePath } from "./pyfmt.js";
import { skillsDir } from "./library.js";

export interface AdapterIO { stdout: (s: string) => void; stderr: (s: string) => void }
const defaultIO: AdapterIO = { stdout: (s) => process.stdout.write(s), stderr: (s) => process.stderr.write(s) };

export function availableSkills(): string[] {
  const dir = skillsDir();
  return fs.readdirSync(dir).filter((n) => fs.existsSync(path.join(dir, n, "SKILL.md"))).sort();
}

const isSymlink = (p: string): boolean => { try { return fs.lstatSync(p).isSymbolicLink(); } catch { return false; } };
const existsOrLink = (p: string): boolean => fs.existsSync(p) || isSymlink(p);
const isInside = (child: string, parent: string): boolean => { const r = path.relative(parent, child); return r !== "" && !r.startsWith("..") && !path.isAbsolute(r); };

function pointsIntoLibrary(link: string): boolean {
  try { return isSymlink(link) && isInside(resolvePath(link), resolvePath(skillsDir())); } catch { return false; }
}

export function install(target: string, names: string[], force = false): [string, string][] {
  fs.mkdirSync(target, { recursive: true });
  const results: [string, string][] = [];
  for (const name of names) {
    const source = path.join(skillsDir(), name), link = path.join(target, name);
    if (isSymlink(link) && resolvePath(link) === resolvePath(source)) results.push([name, "unchanged"]);
    else if (isSymlink(link) && force) { fs.unlinkSync(link); fs.symlinkSync(source, link, "dir"); results.push([name, "replaced"]); }
    else if (existsOrLink(link)) results.push([name, "conflict"]); // never remove real directories or foreign links
    else { fs.symlinkSync(source, link, "dir"); results.push([name, "installed"]); }
  }
  return results;
}

export function uninstall(target: string, names: string[]): [string, string][] {
  return names.map((name): [string, string] => {
    const link = path.join(target, name);
    if (pointsIntoLibrary(link)) { fs.unlinkSync(link); return [name, "removed"]; }
    return [name, existsOrLink(link) ? "skipped" : "absent"];
  });
}

interface Args { scope: "user" | "project"; projectDir: string; target: string | null; skills: string[]; force: boolean; uninstall: boolean }

class UsageError extends Error {}

function parse(argv: string[]): Args | "help" {
  const a: Args = { scope: "user", projectDir: ".", target: null, skills: [], force: false, uninstall: false };
  const value = (flag: string, i: number, inline: string | undefined): [string, number] => {
    if (inline !== undefined) return [inline, i];
    if (i + 1 >= argv.length) throw new UsageError(`argument ${flag}: expected one argument`);
    return [argv[i + 1]!, i + 1];
  };
  for (let i = 0; i < argv.length; i++) {
    const m = /^(--[a-z-]+)=(.*)$/s.exec(argv[i]!);
    const flag = m ? m[1]! : argv[i]!;
    const inline = m ? m[2]! : undefined;
    switch (flag) {
      case "-h": case "--help": return "help";
      case "--force": a.force = true; break;
      case "--uninstall": a.uninstall = true; break;
      case "--scope": { let v: string; [v, i] = value(flag, i, inline); if (v !== "user" && v !== "project") throw new UsageError(`argument --scope: invalid choice: '${v}' (choose from 'user', 'project')`); a.scope = v; break; }
      case "--project-dir": [a.projectDir, i] = value(flag, i, inline); break;
      case "--target": { let v: string; [v, i] = value(flag, i, inline); a.target = v; break; }
      case "--skill": { let v: string; [v, i] = value(flag, i, inline); a.skills.push(v); break; }
      default: throw new UsageError(`unrecognized arguments: ${argv[i]}`);
    }
  }
  return a;
}

export function run(agent: string, userDir: string, projectRel: string, prog: string, argv: string[], io: AdapterIO = defaultIO): number {
  const usage = `usage: ${prog} [-h] [--scope {user,project}] [--project-dir PROJECT_DIR] [--target TARGET] [--skill NAME] [--force] [--uninstall]\n`;
  let args: Args | "help";
  try { args = parse(argv); } catch (e) {
    if (!(e instanceof UsageError)) throw e;
    io.stderr(`${usage}${prog}: error: ${e.message}\n`);
    return 2;
  }
  if (args === "help") {
    io.stdout(`${usage}\nLink the central SDLC Skills into ${agent}'s skill discovery directory (symlinks, no copies).\n\noptions:\n` +
      `  -h, --help            show this help message and exit\n` +
      `  --scope {user,project}\n                        user: ${userDir}; project: <project-dir>/${projectRel} (default: user)\n` +
      `  --project-dir PROJECT_DIR\n                        project directory for --scope project (default: current directory)\n` +
      `  --target TARGET       override the destination directory entirely\n` +
      `  --skill NAME          install only this Skill (repeatable)\n` +
      `  --force               replace an existing symlink that points elsewhere\n` +
      `  --uninstall           remove the links this adapter created\n`);
    return 0;
  }
  const available = availableSkills();
  const names = args.skills.length ? args.skills : available;
  const unknown = [...new Set(names.filter((n) => !available.includes(n)))].sort();
  if (unknown.length) { io.stderr(`error: unknown Skill(s): ${unknown.join(", ")}\n`); return 2; }
  const target = args.target ? args.target : args.scope === "project" ? path.join(path.resolve(args.projectDir), projectRel) : userDir;
  const results = args.uninstall ? uninstall(target, names) : install(target, names, args.force);
  for (const [name, state] of results) io.stdout(`${state.padEnd(10)} ${path.join(target, name)}\n`);
  return results.some(([, s]) => s === "conflict") ? 1 : 0;
}

export const claudeCodeMain = (argv: string[], io?: AdapterIO): number =>
  run("claude-code", path.join(os.homedir(), ".claude", "skills"), ".claude/skills", "sdlc-install-claude-code", argv, io);
export const codexMain = (argv: string[], io?: AdapterIO): number =>
  run("codex", path.join(os.homedir(), ".agents", "skills"), ".agents/skills", "sdlc-install-codex", argv, io);
