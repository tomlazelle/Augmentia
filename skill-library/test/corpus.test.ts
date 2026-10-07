// Gate: every corpus case applicable to this build must pass byte-for-byte (JSON by value; approved exemptions applied).
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { CORPUS_DIR, Corpus, applicable, replayAll } from "./replay-lib.js";

test("the corpus is the frozen Python-oracle asset (checksums unchanged)", () => {
  const lines = fs.readFileSync(path.join(CORPUS_DIR, "MANIFEST.sha256"), "utf8").trim().split("\n");
  assert.equal(lines.length, 5);
  for (const line of lines) {
    const [digest, name] = line.split(/\s+/) as [string, string];
    assert.equal(crypto.createHash("sha256").update(fs.readFileSync(path.join(CORPUS_DIR, name))).digest("hex"), digest, `${name} changed`);
  }
});

test("the oracle-derived expectation files are frozen too", () => {
  const dir = path.join(CORPUS_DIR, "..");
  const lines = fs.readFileSync(path.join(dir, "EXPECTATIONS.sha256"), "utf8").trim().split("\n");
  assert.equal(lines.length, 3);
  for (const line of lines) {
    const [digest, name] = line.split(/\s+/) as [string, string];
    assert.equal(crypto.createHash("sha256").update(fs.readFileSync(path.join(dir, name))).digest("hex"), digest, `${name} changed`);
  }
});

test("applicable corpus cases replay against the Node CLI", { timeout: 600000 }, async () => {
  const corpus = new Corpus();
  const cases = corpus.cases.filter(applicable);
  assert.ok(cases.length > 1000);
  const results = await replayAll(corpus, cases);
  const failed = results.filter((r) => r.status === "fail");
  assert.deepEqual(failed.slice(0, 5).map((f) => `${f.id}: ${f.problems.join("; ")}`), []);
  assert.equal(failed.length, 0);
});
