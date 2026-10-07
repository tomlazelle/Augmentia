// The user guide must match the released CLI, Skills and generated output (port of tests/unit/test_readme.py).
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { cli, preview, apply, project, tmpdir } from "./helpers.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CANON = path.join(HERE, "..", "..");           // skill-library/ (the package root)
const README = fs.readFileSync(path.join(CANON, "README.md"), "utf8");
const ROOT_README = fs.readFileSync(path.join(CANON, "..", "README.md"), "utf8");
const SKILLS = fs.readdirSync(path.join(CANON, "skills"), { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name).sort();
const COMMANDS = ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "status", "publish-preview", "publish-apply", "validate"];

test("every `sdlc <command>` in the guides exists, and the guide lists the whole command surface", () => {
  for (const text of [README, ROOT_README]) {
    const mentioned = new Set([...text.matchAll(/`sdlc ([a-z][a-z-]+)/g), ...text.matchAll(/^sdlc ([a-z][a-z-]+)/gm)].map((m) => m[1]!));
    for (const prose of ["command", "install"]) mentioned.delete(prose);
    assert.ok(mentioned.size > 0);
    for (const m of mentioned) assert.ok(COMMANDS.includes(m), m);
  }
  for (const c of COMMANDS) assert.ok(README.includes(c), c);
});

test("every Skill is documented and every documented Skill exists", () => {
  const named = new Set([...README.matchAll(/`((?:sdlc-)?[a-z]+-[a-z-]+)`/g)].map((m) => m[1]!).filter((n) => SKILLS.includes(n)));
  assert.deepEqual([...named].sort(), SKILLS);
  assert.ok(README.includes(`${SKILLS.length} Skills`));
});

test("install documentation: npm, Node 22, the three commands, adapter flags and folders; no Python/pipx", () => {
  for (const text of [README, ROOT_README]) {
    assert.ok(text.includes("npm install -g @augmentia/sdlc") && /Node\.js[^\n]{0,40}22/.test(text));
    assert.ok(!/pipx|pip install|python3?\.?1?1? -m|Python 3/i.test(text.replace(/The Python 1\.0\.0rc1[^\n]*/g, "")), "stale Python install instructions");
  }
  for (const s of ["sdlc", "sdlc-install-claude-code", "sdlc-install-codex"]) assert.ok(README.includes(s));
  for (const flag of ["--scope project", "--project-dir", "--skill", "--force", "--uninstall"]) assert.ok(README.includes(flag), flag);
  assert.ok(README.includes(".claude/skills") && README.includes(".agents/skills"));
  assert.ok(README.includes("sdlc 2.0.0-rc.1"));
});

test("the documented layout matches what init generates", () => {
  const d = tmpdir();
  assert.equal(cli(["init", "--project-name", "Demo"], d).code, 0);
  const created = new Set<string>();
  const walk = (dir: string): void => { for (const e of fs.readdirSync(dir, { withFileTypes: true })) { const p = path.join(dir, e.name); created.add(path.relative(d, p)); if (e.isDirectory()) walk(p); } };
  walk(d);
  for (const rel of [".sdlc/config.md", ".sdlc/ledger.md", "AGENTS.md", "CLAUDE.md", "map.md", "BR/map.md", "PR/map.md", "Stories/map.md", "Artifacts/map.md"]) {
    assert.ok(created.has(rel), rel); assert.ok(README.includes(rel.split("/").pop()!), rel);
  }
  const block = /```text\n(\.sdlc\/config\.md.*?)```/s.exec(README)![1]!;
  for (const token of ["BR/", "PR/", "Stories/", "Artifacts/", "AGENTS.md", "CLAUDE.md"]) assert.ok(block.includes(token), token);
});

test("publishing documentation matches actual behavior", () => {
  const d = project("owner/repository");
  const config = "publishing:\n     provider: github\n     repository: owner/repository";
  assert.ok(README.includes(config));
  assert.ok(fs.readFileSync(path.join(d, ".sdlc", "config.md"), "utf8").includes("publishing:\n  provider: github\n  repository: owner/repository"));
  const p = preview(d, "US-001");
  assert.ok(p.code === 0 && p.json.result.digest.startsWith("sha256:"));
  const refused = apply(d, null, "US-001");
  assert.ok(refused.code === 1 && refused.json.diagnostics.some((x: any) => x.code === "confirmation-missing"));
  for (const phrase of ["--confirm-digest", "Story + provider + repository", "never reads, stores or prints a credential", "one way"]) assert.ok(README.toLowerCase().includes(phrase.toLowerCase()), phrase);
});
