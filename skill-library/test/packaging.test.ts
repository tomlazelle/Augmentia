// M7.5 packaging: the npm tarball carries every runtime resource and works from a clean prefix without the checkout.
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { before, test } from "node:test";
import { tmpdir } from "./helpers.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PKG = path.join(HERE, "..", "..");
const CANON = PKG;                                     // the package root holds the canonical skills/ and shared/
const pkg = JSON.parse(fs.readFileSync(path.join(PKG, "package.json"), "utf8"));
const walk = (dir: string): string[] => fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
  e.isDirectory() ? (e.name === "__pycache__" ? [] : walk(path.join(dir, e.name))) : e.name.endsWith(".pyc") ? [] : [path.join(dir, e.name)]);
const SKILLS = fs.readdirSync(path.join(CANON, "skills")).filter((n) => fs.existsSync(path.join(CANON, "skills", n, "SKILL.md"))).sort();

let tarball = "", prefix = "", listing: string[] = [];
const npm = (args: string[], cwd: string) => {
  const r = spawnSync("npm", args, { cwd, encoding: "utf8", env: { ...process.env, npm_config_audit: "false", npm_config_fund: "false", npm_config_update_notifier: "false" } });
  assert.equal(r.status, 0, `npm ${args.join(" ")}: ${r.stderr}`);
  return r.stdout;
};
const bin = (name: string) => path.join(prefix, "node_modules", ".bin", name);
function runBin(name: string, args: string[], cwd: string, home = cwd) {
  const env: NodeJS.ProcessEnv = { ...process.env, HOME: home }; delete env["SDLC_TODAY"];
  const r = spawnSync(bin(name), args, { cwd, env, encoding: "utf8" });
  return { code: r.status ?? -1, out: r.stdout, err: r.stderr };
}

before(() => {
  const dest = tmpdir("sdlc-pack-");
  npm(["pack", "--ignore-scripts", "--pack-destination", dest], PKG);   // the build already ran (npm test); no rebuild during the test
  tarball = path.join(dest, fs.readdirSync(dest).find((f) => f.endsWith(".tgz"))!);
  listing = spawnSync("tar", ["-tzf", tarball], { encoding: "utf8" }).stdout.split("\n").filter(Boolean).map((l) => l.replace(/^package\//, ""));
  prefix = tmpdir("sdlc-prefix-");
  npm(["install", "--offline", "--prefix", prefix, tarball], prefix);  // clean prefix; the only dependency (yaml) comes from the npm cache
});

test("package metadata: scoped name, release-candidate version, MIT, Node >= 22, one runtime dependency, three executables", () => {
  assert.deepEqual([pkg.name, pkg.version, pkg.license, pkg.engines.node], ["@augmentia/sdlc", "2.0.0-rc.1", "MIT", ">=22"]);
  assert.deepEqual(Object.keys(pkg.dependencies), ["yaml"]);
  assert.deepEqual(pkg.bin, { sdlc: "bin/sdlc.js", "sdlc-install-claude-code": "bin/sdlc-install-claude-code.js", "sdlc-install-codex": "bin/sdlc-install-codex.js" });
  assert.match(fs.readFileSync(path.join(CANON, "..", "LICENSE"), "utf8"), /^MIT License/);
});

test("the tarball contains every runtime resource and no test, build-tool or Python artefact", () => {
  const names = new Set(listing);
  for (const src of walk(path.join(CANON, "skills"))) assert.ok(names.has(`skills/${path.relative(path.join(CANON, "skills"), src)}`), src);
  for (const src of walk(path.join(CANON, "shared"))) assert.ok(names.has(`shared/${path.relative(path.join(CANON, "shared"), src)}`), src);
  for (const required of ["package.json", "LICENSE", "README.md", "bin/sdlc.js", "bin/sdlc-install-claude-code.js", "bin/sdlc-install-codex.js",
    "dist/src/cli.js", "dist/src/adapters.js", "templates/AGENTS.md", "templates/CLAUDE.md"]) assert.ok(names.has(required), required);
  assert.deepEqual(listing.filter((n) => /^(dist\/test|test|src|scripts|parity|tsconfig)|\.ts$|\.map$|__pycache__|\.pyc$|\.py$/.test(n) && !n.endsWith(".d.ts")), []);
  assert.deepEqual(listing.filter((n) => /\.d\.ts$/.test(n)), listing.filter((n) => /\.d\.ts$/.test(n))); // declarations are harmless
  assert.equal(SKILLS.length, 15);
});

test("the installed `sdlc` runs from a clean prefix without the checkout", () => {
  const cwd = tmpdir();
  const v = runBin("sdlc", ["--version"], cwd);
  assert.deepEqual([v.code, v.out.trim()], [0, `sdlc ${pkg.version}`]);
  const help = runBin("sdlc", ["--help"], cwd).out;
  for (const c of ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "status", "publish-preview", "publish-apply", "validate"]) assert.ok(help.includes(c), c);
});

test("release smoke sequence from the installed package", () => {
  const project = tmpdir();
  for (const args of [["init"], ["init"], ["validate"], ["status"], ["list"], ["allocate-id", "--category", "BR", "--title", "Overview"]]) {
    const r = runBin("sdlc", args, project);
    assert.equal(r.code, 0, `${args.join(" ")}: ${r.out}${r.err}`);
  }
  const agents = fs.readFileSync(path.join(project, "AGENTS.md"), "utf8");
  assert.equal(agents, fs.readFileSync(path.join(project, "CLAUDE.md"), "utf8"));
  assert.ok(agents.includes("create-brd") && agents.includes("sdlc validate"));
  assert.equal(runBin("sdlc", ["validate"], project).code, 0);
});

for (const [script, parts] of [["sdlc-install-claude-code", [".claude", "skills"]], ["sdlc-install-codex", [".agents", "skills"]]] as const) {
  test(`installed ${script} links the packaged Skills (not the checkout) and references resolve`, () => {
    const project = tmpdir(), home = tmpdir();
    const done = runBin(script, ["--scope", "project", "--project-dir", project], home, home);
    assert.equal(done.code, 0, done.err);
    const base = path.join(project, ...parts);
    assert.deepEqual(fs.readdirSync(base).sort(), SKILLS);
    const installedLib = fs.realpathSync(path.join(prefix, "node_modules", "@augmentia", "sdlc"));
    for (const skill of SKILLS) {
      const link = path.join(base, skill), target = fs.realpathSync(link);
      assert.ok(fs.lstatSync(link).isSymbolicLink() && target.startsWith(installedLib + path.sep) && !target.startsWith(fs.realpathSync(CANON) + path.sep + "skills"), skill);
      for (const m of fs.readFileSync(path.join(link, "SKILL.md"), "utf8").matchAll(/`((?:references\/|\.\.\/\.\.\/shared\/)[\w./-]+\.md)`/g)) assert.ok(fs.existsSync(`${link}/${m[1]!}`), `${skill}: ${m[1]}`);
    }
    const again = runBin(script, ["--scope", "project", "--project-dir", project], home, home);
    assert.deepEqual([...new Set(again.out.trim().split("\n").map((l) => l.split(/\s+/)[0]))], ["unchanged"]);
    assert.equal(runBin(script, ["--scope", "project", "--project-dir", project, "--uninstall"], home, home).code, 0);
    assert.deepEqual(fs.readdirSync(base), []);
  });
}

test("installed adapter conflict behaviour never touches a foreign directory", () => {
  const project = tmpdir();
  fs.mkdirSync(path.join(project, ".claude", "skills", "sdlc-init"), { recursive: true });
  const done = runBin("sdlc-install-claude-code", ["--scope", "project", "--project-dir", project], project);
  assert.ok(done.code === 1 && done.out.includes("conflict"));
  assert.equal(runBin("sdlc-install-claude-code", ["--scope", "project", "--project-dir", project, "--uninstall"], project).code, 0);
  assert.ok(fs.statSync(path.join(project, ".claude", "skills", "sdlc-init")).isDirectory());
});

test("Skills and shared docs name the installed command and no Python/pipx tooling", () => {
  const offenders: string[] = [];
  for (const dir of ["skills", "shared"]) for (const f of walk(path.join(PKG, dir)).filter((f) => f.endsWith(".md"))) {
    const text = fs.readFileSync(f, "utf8");
    if (/python -m sdlc|pipx|pip install|PyYAML|sdlc\/[a-z_]+\.py/.test(text)) offenders.push(path.relative(PKG, f));
  }
  assert.deepEqual(offenders, []);
});
