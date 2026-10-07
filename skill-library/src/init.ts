// `init` and `create-dir`: idempotent creation of the standard project structure (port of sdlc/init_cmd.py).

import fs from "node:fs";
import path from "node:path";
import { dumpConfig } from "./frontmatter.js";
import { LEDGER_REL } from "./ledger.js";
import { specs, syncMap } from "./maps.js";
import { ARTIFACT_SUBDIRS, Diagnostic, Outcome } from "./model.js";
import { DEFAULT_DIRECTORIES, Project, SCHEMA_VERSION, loadConfig, scanDocuments } from "./project.js";
import { atomicWrite, cmpStr, exists, isDir, lexists, readText, resolvePath } from "./pyfmt.js";
import { templateText } from "./resources.js";

const CONFIG_REL = ".sdlc/config.md";
const INSTRUCTION_FILES = ["AGENTS.md", "CLAUDE.md"];
const LEDGER_HEADER = `# ID Ledger

Maintained by the \`sdlc\` CLI. Do not edit by hand.
Allocated and retired IDs are recorded here so IDs are never reused within a checkout.

| ID | Kind | State | Date | Note |
|---|---|---|---|---|
`;

/** Create <root>/<name> from the packaged template unless anything (file, symlink, even a dangling one) already exists. */
function installInstructionFile(root: string, name: string): boolean {
  const target = path.join(root, name);
  if (lexists(target)) return false;
  const text = templateText(name);
  try {
    fs.writeFileSync(target, text, { encoding: "utf8", flag: "wx" }); // exclusive create: never clobber, even on a race
  } catch (exc) {
    if ((exc as NodeJS.ErrnoException).code === "EEXIST") return false;
    throw exc;
  }
  return true;
}

function configText(name: string): string {
  return `---\n${dumpConfig(name, SCHEMA_VERSION, DEFAULT_DIRECTORIES)}---\n\n# SDLC Configuration\n\nInternal configuration maintained by the \`sdlc\` CLI.\nIt is not an authored document and is not listed in any map.\n`;
}

export function initProject(rootIn: string, projectName: string | null): Outcome {
  const root = resolvePath(rootIn);
  if (!isDir(root)) return new Outcome(2, {}, [new Diagnostic("error", "bad-root", `${root} is not a directory`)]);
  const created: string[] = [];
  const existing: string[] = [];
  const diags: Diagnostic[] = [];
  const note = (p: string, wasCreated: boolean) => {
    const rel = path.relative(root, p).split(path.sep).join("/");
    (wasCreated ? created : existing).push(rel);
  };

  fs.mkdirSync(path.join(root, ".sdlc"), { recursive: true });
  const configPath = path.join(root, CONFIG_REL);
  if (exists(configPath)) {
    note(configPath, false);
    const [, cfgDiags] = loadConfig(root);
    diags.push(...cfgDiags.filter((d) => d.severity === "error"));
  } else {
    atomicWrite(configPath, configText(projectName || path.basename(root)));
    note(configPath, true);
  }
  const ledgerPath = path.join(root, LEDGER_REL);
  if (exists(ledgerPath)) note(ledgerPath, false);
  else { atomicWrite(ledgerPath, LEDGER_HEADER); note(ledgerPath, true); }

  for (const name of INSTRUCTION_FILES) note(path.join(root, name), installInstructionFile(root, name));

  const project = Project.open(root);
  for (const key of Object.keys(DEFAULT_DIRECTORIES)) {
    const directory = project.top(key);
    const wasNew = !exists(directory);
    fs.mkdirSync(directory, { recursive: true });
    if (wasNew) created.push(project.rel(directory) + "/");
  }
  const [docs] = scanDocuments(project);
  for (const spec of specs(project)) {
    const action = !exists(spec.path) ? syncMap(project, spec, docs)[0] : "exists";
    note(spec.path, action === "created");
  }
  return new Outcome(diags.length ? 1 : 0, { root, created: created.sort(cmpStr), existing: existing.sort(cmpStr) }, diags);
}

export function createArtifactDir(project: Project, sub: string): Outcome {
  const artifacts = project.top("Artifacts");
  if (!isDir(artifacts)) {
    return new Outcome(1, {}, [new Diagnostic("error", "missing-directory", "Artifacts directory does not exist; run 'sdlc init'", project.rel(artifacts))]);
  }
  const target = path.join(artifacts, sub);
  const dirCreated = !exists(target);
  fs.mkdirSync(target, { recursive: true });
  const [docs] = scanDocuments(project);
  const diags: Diagnostic[] = [];
  const result: Record<string, unknown> = { directory: project.rel(target), directory_created: dirCreated };
  for (const spec of specs(project)) {
    if (spec.key === sub || spec.key === "Artifacts") {
      const [action, diag] = syncMap(project, spec, docs);
      result[`${spec.key}_map`] = action;
      if (diag) diags.push(diag);
    }
  }
  return new Outcome(diags.length ? 1 : 0, result, diags);
}

export { ARTIFACT_SUBDIRS, readText };
