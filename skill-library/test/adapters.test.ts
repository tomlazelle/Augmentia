// The `sdlc-install-*` adapters (port of tests/unit/test_install.py): symlinks into the packaged library, never copies.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { tmpdir } from "./helpers.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PKG = path.join(HERE, "..", "..");
const LIB = PKG;
const SKILLS = fs.readdirSync(path.join(LIB, "skills")).sort();
const ADAPTERS: Record<string, [string, string]> = { "sdlc-install-claude-code": [".claude", "skills"], "sdlc-install-codex": [".agents", "skills"] };

function run(adapter: string, args: string[], home: string): { code: number; out: string; err: string } {
  const r = spawnSync(process.execPath, [path.join(PKG, "bin", `${adapter}.js`), ...args], { env: { ...process.env, HOME: home }, encoding: "utf8" });
  return { code: r.status ?? -1, out: r.stdout, err: r.stderr };
}

for (const [adapter, parts] of Object.entries(ADAPTERS)) {
  test(`${adapter}: user scope links every Skill without copying`, () => {
    const home = tmpdir();
    const r = run(adapter, [], home);
    assert.equal(r.code, 0, r.err);
    const base = path.join(home, ...parts);
    assert.deepEqual(fs.readdirSync(base).sort(), SKILLS);
    for (const name of SKILLS) {
      const link = path.join(base, name);
      assert.ok(fs.lstatSync(link).isSymbolicLink());
      assert.equal(fs.realpathSync(link), fs.realpathSync(path.join(LIB, "skills", name)));
      assert.equal(fs.readFileSync(path.join(link, "SKILL.md"), "utf8"), fs.readFileSync(path.join(LIB, "skills", name, "SKILL.md"), "utf8"));
    }
    assert.equal(SKILLS.length, 15);
  });

  test(`${adapter}: project scope, idempotence, relative references resolve through the links`, () => {
    const home = tmpdir(), project = tmpdir();
    assert.equal(run(adapter, ["--scope", "project", "--project-dir", project], home).code, 0);
    const again = run(adapter, ["--scope", "project", "--project-dir", project], home);
    assert.equal(again.code, 0);
    assert.deepEqual([...new Set(again.out.trim().split("\n").map((l) => l.split(/\s+/)[0]))], ["unchanged"]);
    const base = path.join(project, ...parts);
    assert.ok(fs.lstatSync(path.join(base, "sdlc-init")).isSymbolicLink());
    for (const skill of SKILLS) {
      const text = fs.readFileSync(path.join(base, skill, "SKILL.md"), "utf8");
      for (const m of text.matchAll(/`((?:references\/|\.\.\/\.\.\/shared\/)[\w./-]+\.md)`/g)) assert.ok(fs.existsSync(`${path.join(base, skill)}/${m[1]!}`), `${skill}: ${m[1]}`);
    }
    assert.equal(fs.readdirSync(path.join(home)).length, 0, "project scope must not touch the user directory");
  });

  test(`${adapter}: conflicts are reported and never destroyed; uninstall removes only its own links`, () => {
    const home = tmpdir();
    const base = path.join(home, ...parts);
    fs.mkdirSync(path.join(base, "sdlc-init"), { recursive: true });
    fs.writeFileSync(path.join(base, "sdlc-init", "mine.txt"), "keep");
    const r = run(adapter, [], home);
    assert.equal(r.code, 1);
    assert.match(r.out, /^conflict {2}/m);
    assert.equal(fs.readFileSync(path.join(base, "sdlc-init", "mine.txt"), "utf8"), "keep");
    assert.ok(fs.lstatSync(path.join(base, "sdlc-explore")).isSymbolicLink());
    fs.mkdirSync(path.join(base, "other"));
    const u = run(adapter, ["--uninstall"], home);
    assert.equal(u.code, 0);
    assert.match(u.out, /^skipped /m);
    assert.ok(fs.statSync(path.join(base, "sdlc-init")).isDirectory() && fs.statSync(path.join(base, "other")).isDirectory());
    assert.ok(!fs.existsSync(path.join(base, "sdlc-explore")));
  });

  test(`${adapter}: --force replaces a link that points elsewhere; without it that is a conflict; --skill limits the set`, () => {
    const home = tmpdir(), elsewhere = tmpdir();
    const base = path.join(home, ...parts);
    fs.mkdirSync(base, { recursive: true });
    fs.symlinkSync(elsewhere, path.join(base, "sdlc-init"), "dir");
    assert.equal(run(adapter, ["--skill", "sdlc-init"], home).code, 1);
    assert.equal(fs.realpathSync(path.join(base, "sdlc-init")), fs.realpathSync(elsewhere));
    const forced = run(adapter, ["--skill", "sdlc-init", "--force"], home);
    assert.equal(forced.code, 0);
    assert.match(forced.out, /^replaced /);
    assert.equal(fs.readdirSync(base).length, 1);
    assert.equal(fs.realpathSync(path.join(base, "sdlc-init")), fs.realpathSync(path.join(LIB, "skills", "sdlc-init")));
    // a link that points elsewhere is not ours: uninstall skips it
    fs.rmSync(path.join(base, "sdlc-init")); fs.symlinkSync(elsewhere, path.join(base, "sdlc-init"), "dir");
    assert.match(run(adapter, ["--uninstall", "--skill", "sdlc-init"], home).out, /^skipped /);
    assert.match(run(adapter, ["--uninstall", "--skill", "sdlc-explore"], home).out, /^absent /);
  });

  test(`${adapter}: --target overrides the destination; usage errors exit 2`, () => {
    const home = tmpdir(), target = path.join(tmpdir(), "dest");
    assert.equal(run(adapter, ["--target", target, "--skill", "sdlc-init"], home).code, 0);
    assert.deepEqual(fs.readdirSync(target), ["sdlc-init"]);
    assert.equal(run(adapter, ["--skill", "nope"], home).code, 2);
    assert.match(run(adapter, ["--skill", "nope"], home).err, /unknown Skill\(s\): nope/);
    assert.equal(run(adapter, ["--scope", "galaxy"], home).code, 2);
    assert.equal(run(adapter, ["--bogus"], home).code, 2);
    assert.equal(run(adapter, ["--skill"], home).code, 2);
    const help = run(adapter, ["--help"], home);
    assert.equal(help.code, 0);
    for (const flag of ["--scope", "--project-dir", "--target", "--skill", "--force", "--uninstall"]) assert.ok(help.out.includes(flag), flag);
  });
}
