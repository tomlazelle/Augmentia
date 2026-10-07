// A project crafted so the find-overlaps score is an exact rounding tie. Expected values come from the Python oracle:
// score 0.562 (round-half-even), "title similarity 0.12" and the displayed "0.56". Plain JavaScript rounding gives 0.563/0.13.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { main } from "../src/cli.js";

function cli(args: string[], cwd: string) {
  const saved = process.cwd();
  process.chdir(cwd);
  try {
    let out = "", err = "";
    const code = main(args, { stdout: (s) => (out += s), stderr: (s) => (err += s) });
    return { code, out, err };
  } finally { process.chdir(saved); }
}

const doc = (id: string, title: string, purpose: string, extra = "", body = "") =>
  `---\nid: ${id}\ntitle: ${title}\npurpose: ${purpose}\nstatus: Draft\ncreated: 2026-09-01\nupdated: 2026-09-01\n${extra}---\n\n# ${id} — ${title}\n${body}`;

test("exact-tie score: oracle rounding in JSON and human output", () => {
  const d = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-tie-")));
  process.env["SDLC_TODAY"] = "2026-09-29";
  cli(["init", "--project-name", "Tie"], d);
  fs.writeFileSync(path.join(d, "BR", "BR-001-base.md"), doc("BR-001", "Base", "Base requirements.", "", "\n- **BR-001-R001** — A requirement.\n"));
  fs.writeFileSync(path.join(d, "PR", "PR-001-prd.md"), doc("PR-001", "Prd", "Product requirements.", "",
    "\n## References\n\n### Derived From\n- [BR-001](../BR/BR-001-base.md)\n\n## Requirements\n\n- **PR-001-R001** — A product requirement.\n"));
  fs.writeFileSync(path.join(d, "Stories", "US-001-alpha-echo-foxtrot-golf-hotel.md"),
    doc("US-001", "alpha echo foxtrot golf hotel", "users export weekly reports quickly", "delivery_status: Not Started\ncovers: [PR-001-R001]\n",
      "\n## References\n\n### Derived From\n- [PR-001](../PR/PR-001-prd.md)\n"));
  cli(["update-map"], d);
  const args = ["find-overlaps", "--category", "US", "--title", "alpha bravo charlie delta", "--purpose", "users export weekly reports quickly", "--covers", "PR-001-R001"];
  const json = JSON.parse(cli([...args, "--json"], d).out).result.candidates;
  assert.equal(json.length, 1);
  assert.deepEqual([json[0].score, json[0].level, json[0].reasons], [0.562, "possible", ["title similarity 0.12", "purpose similarity 1.00", "shares references: PR-001-R001"]]);
  const human = cli(args, d).out.split("\n");
  assert.equal(human[0], "possible 0.56  US-001 alpha echo foxtrot golf hotel  (Stories/US-001-alpha-echo-foxtrot-golf-hotel.md)");
  assert.deepEqual(human.slice(1, 4), ["           - title similarity 0.12", "           - purpose similarity 1.00", "           - shares references: PR-001-R001"]);
  fs.rmSync(d, { recursive: true, force: true });
});
