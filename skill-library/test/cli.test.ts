import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { main, parseArgs } from "../src/cli.js";

function run(args: string[], cwd: string): { code: number; out: string; err: string } {
  const saved = process.cwd();
  process.chdir(cwd);
  try {
    let out = "", err = "";
    const code = main(args, { stdout: (s) => (out += s), stderr: (s) => (err += s) });
    return { code, out, err };
  } finally { process.chdir(saved); }
}
const tmp = (): string => fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-cli-")));

test("usage errors exit 2 and name the offending option", () => {
  const d = tmp();
  for (const [args, needle] of [
    [["allocate-id"], "--category"], [["allocate-id", "--category", "XX"], "invalid choice"], [["allocate-id", "--category", "US", "--requirement", "PR-001"], "not allowed"],
    [["create-dir"], "--artifact"], [["create-dir", "--artifact", "nope"], "invalid choice"], [["retire-id"], "id"], [["bogus"], "invalid choice"],
    [[], "<command>"], [["init", "--nope"], "--nope"], [["init", "--project-name"], "expected one argument"], [["list", "extra"], "unrecognized"],
  ] as [string[], string][]) {
    const r = run(args, d);
    assert.equal(r.code, 2, JSON.stringify(args));
    assert.ok(r.err.includes("usage:") && r.err.includes("error:") && r.err.includes(needle), `${JSON.stringify(args)}: ${r.err}`);
  }
});

test("help and version exit 0 and are deterministic", () => {
  const d = tmp();
  const top = run(["--help"], d);
  assert.equal(top.code, 0);
  for (const c of ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "status", "publish-preview", "publish-apply", "validate"]) assert.ok(top.out.includes(c), c);
  const sub = run(["allocate-id", "--help"], d);
  assert.equal(sub.code, 0);
  for (const f of ["--category", "--requirement", "--title", "--root", "--json"]) assert.ok(sub.out.includes(f), f);
  assert.equal(run(["allocate-id", "-h"], d).out, sub.out);
  assert.equal(run(["--version"], d).out, "sdlc 2.0.0-rc.1\n");
});

test("options: unique-prefix abbreviations, --opt=value, interleaved positionals, --", () => {
  const p = parseArgs(["retire-id", "US-001", "--replaced", "US-002", "--note=x y", "--js"]);
  assert.equal(p.kind, "args");
  if (p.kind === "args") assert.deepEqual([p.args["id"], p.args["replacedBy"], p.args["note"], p.args.json], ["US-001", "US-002", "x y", true]);
  assert.throws(() => parseArgs(["find-overlaps", "--c", "US", "--title", "t"]), /ambiguous/);   // --category / --covers
  const q = parseArgs(["find-overlaps", "--category", "US", "--title", "t", "--covers", "PR-001", "PR-001-R001", "--json"]);
  if (q.kind === "args") assert.deepEqual(q.args["covers"], ["PR-001", "PR-001-R001"]);
  const dd = parseArgs(["publish-preview", "--", "-weird", "US-001"]);
  if (dd.kind === "args") assert.deepEqual(dd.args["stories"], ["-weird", "US-001"]);
  const neg = parseArgs(["allocate-id", "--category", "US", "--title", "-5"]);
  if (neg.kind === "args") assert.equal(neg.args["title"], "-5");   // negative numbers are values, as in argparse
});

test("--json envelope and exit codes", () => {
  const d = tmp();
  const outside = run(["allocate-id", "--category", "US", "--json"], d);
  assert.equal(outside.code, 2);
  const env = JSON.parse(outside.out);
  assert.deepEqual(Object.keys(env), ["schema_version", "command", "ok", "exit_code", "result", "diagnostics"]);
  assert.deepEqual([env.schema_version, env.command, env.ok, env.exit_code, env.diagnostics[0].code], [1, "allocate-id", false, 2, "no-project"]);
  assert.deepEqual(Object.keys(env.diagnostics[0]), ["severity", "code", "message", "path", "id", "line"]);
  const init = JSON.parse(run(["init", "--json"], d).out);
  assert.equal(init.ok, true);
  const alloc = JSON.parse(run(["allocate-id", "--category", "US", "--title", "A story", "--json"], d).out);
  assert.deepEqual(alloc.result, { id: "US-001", kind: "document", category: "US", directory: "Stories", path: "Stories/US-001-a-story.md" });
});

test("init is idempotent and never touches existing instruction files (including dangling symlinks)", () => {
  const d = tmp();
  fs.writeFileSync(path.join(d, "AGENTS.md"), "# mine\n");
  fs.symlinkSync("nowhere", path.join(d, "CLAUDE.md"));
  const first = JSON.parse(run(["init", "--json"], d).out);
  assert.deepEqual(first.result.existing.filter((e: string) => /MD$/.test(e) || e.endsWith(".md") && !e.includes("/")).sort(), ["AGENTS.md", "CLAUDE.md"].concat(first.result.existing.includes("map.md") ? ["map.md"] : []).sort());
  assert.equal(fs.readFileSync(path.join(d, "AGENTS.md"), "utf8"), "# mine\n");
  assert.ok(fs.lstatSync(path.join(d, "CLAUDE.md")).isSymbolicLink());
  const before = fs.readFileSync(path.join(d, ".sdlc", "ledger.md"), "utf8");
  const second = JSON.parse(run(["init", "--json"], d).out);
  assert.deepEqual(second.result.created, []);
  assert.equal(fs.readFileSync(path.join(d, ".sdlc", "ledger.md"), "utf8"), before);
});

test("init from a nested directory uses the project root; init --root a file exits 2", () => {
  const d = tmp();
  run(["init"], d);
  fs.unlinkSync(path.join(d, "AGENTS.md"));
  const r = run(["init"], path.join(d, "BR"));
  assert.equal(r.code, 0);
  assert.ok(fs.existsSync(path.join(d, "AGENTS.md")) && !fs.existsSync(path.join(d, "BR", "AGENTS.md")));
  fs.writeFileSync(path.join(d, "afile"), "x");
  const bad = run(["init", "--root", path.join(d, "afile"), "--json"], d);
  assert.equal(bad.code, 2);
  assert.equal(JSON.parse(bad.out).diagnostics[0].code, "bad-root");
});

test("allocate/retire rules (never recycle, tombstone, replaced-by kinds)", () => {
  const d = tmp();
  run(["init"], d);
  assert.equal(JSON.parse(run(["allocate-id", "--category", "BR", "--title", "One", "--json"], d).out).result.id, "BR-001");
  fs.writeFileSync(path.join(d, "BR", "BR-005-late.md"), "---\nid: BR-005\n---\n");
  assert.equal(JSON.parse(run(["allocate-id", "--category", "BR", "--json"], d).out).result.id, "BR-006");
  assert.equal(run(["allocate-id", "--category", "BR", "--title", "!!!", "--json"], d).code, 2);
  const retired = JSON.parse(run(["retire-id", "BR-001", "--replaced-by", "BR-006", "--note", "dup", "--json"], d).out);
  assert.equal(retired.result.note, "Replaced by BR-006. dup");
  assert.equal(run(["retire-id", "BR-001"], d).code, 1);
  assert.equal(run(["retire-id", "BR-001-R001", "--replaced-by", "BR-006"], d).code, 2);
  assert.equal(run(["allocate-id", "--requirement", "BR-001"], d).code, 1);
  assert.equal(JSON.parse(run(["allocate-id", "--requirement", "BR-006", "--json"], d).out).result.id, "BR-006-R001");
});
