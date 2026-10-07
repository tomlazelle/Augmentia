// Digest sensitivity matrix. Starting from one known preview, each single change is applied and the digest compared:
//  - every material publication input must change it; every intentionally excluded input must not;
//  - and every digest must equal the Python oracle's byte for byte (oracle-derived: parity/digest-matrix.json).
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { cli, digestOf, preview, project } from "./helpers.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const MATRIX = JSON.parse(fs.readFileSync(path.join(process.env["SDLC_PARITY_DIR"] ?? path.join(HERE, "..", "..", "parity"), "digest-matrix.json"), "utf8")) as {
  base_files: Record<string, string>; base_selection: string[]; base_digest: string;
  scenarios: { name: string; expect: "changes" | "same"; ops: Record<string, any>[]; selection: string[]; reference_selection: string[]; digest: string; reference_digest: string }[];
};

function digestFor(ops: Record<string, any>[], selection: string[]): string {
  const d = project();
  for (const op of ops) {
    if (op["replace"]) {
      const [rel, old, neu] = op["replace"] as string[];
      const p = path.join(d, rel!);
      const text = fs.readFileSync(p, "utf8");
      assert.ok(text.includes(old!), `${rel}: ${old}`);
      fs.writeFileSync(p, text.replace(old!, neu!));
    } else if (op["append"]) {
      const [rel, text] = op["append"] as string[];
      fs.appendFileSync(path.join(d, rel!), text!);
    } else if (op["config_repository"]) {
      const cfg = path.join(d, ".sdlc", "config.md");
      fs.writeFileSync(cfg, fs.readFileSync(cfg, "utf8").replace("acme/widgets", op["config_repository"]));
    }
  }
  cli(["update-map"], d);
  const r = preview(d, ...selection);
  assert.equal(r.code, 0, JSON.stringify(r.json.diagnostics));
  fs.rmSync(d, { recursive: true, force: true });
  return digestOf(r);
}

test("the base preview digest equals the oracle's", () => {
  assert.equal(digestFor([], MATRIX.base_selection), MATRIX.base_digest);
});

for (const sc of MATRIX.scenarios) {
  test(`digest ${sc.expect === "changes" ? "CHANGES" : "is UNCHANGED"} and equals the oracle: ${sc.name}`, () => {
    const digest = digestFor(sc.ops, sc.selection);
    assert.equal(digest, sc.digest, "digest must equal the Python oracle's byte for byte");
    const reference = digestFor([], sc.reference_selection);
    assert.equal(reference, sc.reference_digest);
    assert.equal(digest !== reference, sc.expect === "changes", sc.expect === "changes" ? "a material publication input did not alter the digest" : "an intentionally excluded input altered the digest");
  });
}

test("matrix size: at least 14 material and 12 excluded inputs", () => {
  assert.ok(MATRIX.scenarios.filter((s) => s.expect === "changes").length >= 14 && MATRIX.scenarios.filter((s) => s.expect === "same").length >= 12);
});
