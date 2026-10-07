// PARITY-EXCEPTION-007: a project text file that is not valid UTF-8. Python 1.0.0rc1 leaks a UnicodeDecodeError traceback;
// Node reports a clear `invalid-encoding` error (exit 1 where the file is essential), never a stack trace, and never rewrites the file.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { apply, cli, digestOf, preview, project, tree } from "./helpers.js";

const corrupt = (file: string): Buffer => {
  const b = fs.readFileSync(file), h = Math.floor(b.length / 2);
  const bad = Buffer.concat([b.subarray(0, h), Buffer.from([0xff, 0xfe]), b.subarray(h)]);
  fs.writeFileSync(file, bad);
  return bad;
};
const codes = (r: { json: any }) => (r.json.diagnostics as { code: string; path?: string }[]).filter((d) => d.code === "invalid-encoding");

test("a document that is not valid UTF-8 is one invalid-encoding error; the rest of the project keeps working", () => {
  const d = project();
  const story = path.join(d, "Stories", fs.readdirSync(path.join(d, "Stories")).find((f) => f.startsWith("US-002"))!);
  const bytes = corrupt(story);
  const v = cli(["validate", "--json"], d);
  assert.equal(v.code, 1);
  assert.deepEqual(codes(v).map((x) => x.path), ["Stories/" + path.basename(story)]);
  assert.ok(!v.json.diagnostics.some((x: any) => x.code === "bad-front-matter" && x.path?.endsWith(path.basename(story))), "no misleading second error");
  assert.equal(cli(["list", "--json"], d).code, 0);
  assert.equal(cli(["status", "--json"], d).code, 0);
  assert.deepEqual(fs.readFileSync(story), bytes, "never rewritten");
  // publishing never touches it: the Story is blocked, the intact one is still publishable
  const p = preview(d, "US-001", "US-002");
  assert.ok(p.json.result.stories.find((s: any) => s.id === "US-002").action === "blocked");
  assert.deepEqual(fs.readFileSync(story), bytes);
});

test("an undecodable config, ledger or map is reported, never rewritten, and never produces a stack trace", () => {
  for (const [rel, fails] of [[".sdlc/config.md", ["validate"]], [".sdlc/ledger.md", ["validate", "references US-001", "allocate-id --category US --title X"]], ["Stories/map.md", ["validate", "update-map"]], ["map.md", ["validate", "update-map"]]] as const) {
    const d = project();
    const bytes = corrupt(path.join(d, rel));
    const before = tree(d);
    for (const command of fails) {
      const r = cli([...command.split(" "), "--json"], d);
      assert.equal(r.code, 1, `${rel}: ${command}`);
      assert.ok(codes(r).length > 0, `${rel}: ${command}`);
      assert.ok(!r.err.includes("    at "), "no stack trace");
    }
    assert.deepEqual(fs.readFileSync(path.join(d, rel)), bytes, `${rel} never rewritten`);
    assert.deepEqual(tree(d), before, `${rel}: failed commands changed nothing`);
  }
});

test("a leading BOM and CRLF are still accepted (valid UTF-8), as in Python", () => {
  const d = project();
  const story = path.join(d, "Stories", fs.readdirSync(path.join(d, "Stories")).find((f) => f.startsWith("US-002"))!);
  const text = fs.readFileSync(story, "utf8");
  fs.writeFileSync(story, "﻿" + text.replace(/\n/g, "\r\n"));
  const r = cli(["list", "--json"], d);
  assert.equal(r.code, 0);
  assert.ok(!codes(r).length);
});
