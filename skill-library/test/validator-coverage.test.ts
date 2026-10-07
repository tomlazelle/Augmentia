// Validator coverage: every code in the CLI contract's validate table is (a) produced by the Node source, (b) observed in
// the frozen corpus with the contracted severity (so the corpus replay holds Node to it), and exit behaviour matches.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { Corpus, applicable } from "./replay-lib.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CONTRACT = fs.readFileSync(path.join(HERE, "..", "..", "shared", "cli-contract.md"), "utf8");
const table = CONTRACT.slice(CONTRACT.indexOf("### `validate`"), CONTRACT.indexOf("The R2 rows above"));
const rows = table.split("\n").filter((l) => l.startsWith("|") && !l.startsWith("| Code") && !l.startsWith("|---"));
const contract = new Map<string, string>();
for (const row of rows) {
  const cells = row.split("|");
  for (const m of cells[1]!.matchAll(/`([a-z-]+)`/g)) contract.set(m[1]!, cells[2]!.trim());
}

const sources = fs.readdirSync(path.join(HERE, "..", "src")).filter((f) => f.endsWith(".js")).map((f) => fs.readFileSync(path.join(HERE, "..", "src", f), "utf8")).join("\n");

test("the contract lists 54 validator codes and Node implements every one", () => {
  assert.equal(contract.size, 54);
  const missing = [...contract.keys()].filter((code) => !sources.includes(`"${code}"`));
  assert.deepEqual(missing, []);
});

test("every contract code is observed in the corpus with exactly the contracted severity", () => {
  const corpus = new Corpus();
  const seen = new Map<string, Set<string>>();
  let validateErrorExit = 0, validateCleanExit = 0;
  for (const c of corpus.cases) {
    if (c.argv[0] !== "validate" || !c.argv.includes("--json") || !c.expected.stdout.trim()) continue;
    const out = JSON.parse(c.expected.stdout) as { diagnostics: { code: string; severity: string }[]; exit_code: number; result: { summary?: Record<string, number> } };
    for (const d of out.diagnostics) { if (!seen.has(d.code)) seen.set(d.code, new Set()); seen.get(d.code)!.add(d.severity); }
    // exit behaviour: errors => 1, warnings/notices alone => 0 (never affects the exit code); no project => 2
    if (!out.result.summary) { assert.equal(out.exit_code, 2, c.id); continue; }
    assert.equal(out.exit_code, out.result.summary["error"]! > 0 ? 1 : 0, c.id);
    if (out.exit_code === 1) validateErrorExit++; else validateCleanExit++;
  }
  const unobserved = [...contract.keys()].filter((code) => !seen.has(code));
  assert.deepEqual(unobserved, []);
  for (const [code, severity] of contract) assert.deepEqual([...seen.get(code)!], [severity], `${code} severity`);
  assert.ok(validateErrorExit > 50 && validateCleanExit > 50);
});

test("validate and the other newly applicable commands are covered by replayable corpus cases", () => {
  const corpus = new Corpus();
  const byCommand = new Map<string, number>();
  for (const c of corpus.cases.filter(applicable)) byCommand.set(c.argv[0]!, (byCommand.get(c.argv[0]!) ?? 0) + 1);
  for (const cmd of ["validate", "list", "references", "find-overlaps", "update-map"]) assert.ok((byCommand.get(cmd) ?? 0) >= 15, cmd);
});
