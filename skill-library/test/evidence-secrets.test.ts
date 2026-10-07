// No secrets in evidence: no token-shaped string in any evidence document, corpus file, expectation file or fixture.
// (Source files of the stubs construct a fake token at runtime and are not evidence.)
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.join(HERE, "..", "..", "..");
const TOKEN = /gh[pousr]_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}|Bearer[ \t]+[A-Za-z0-9._-]{12,}/;

function* files(dir: string): Generator<string> {
  for (const name of fs.readdirSync(dir)) {
    if (name === "node_modules" || name === ".git") continue;
    const p = path.join(dir, name);
    const st = fs.lstatSync(p);
    if (st.isSymbolicLink()) continue;
    if (st.isDirectory()) yield* files(p); else yield p;
  }
}

test("evidence documents, corpus, oracle expectations and fixtures contain no token-shaped string", () => {
  const roots = ["docs", "skill-library/parity", "skill-library/test/fixtures", "skill-library/README.md", "README.md"].map((r) => path.join(REPO, r));
  const hits: string[] = [];
  let scanned = 0;
  for (const root of roots) {
    for (const f of fs.statSync(root).isDirectory() ? files(root) : [root]) {
      if (f.includes(`${path.sep}oracle-tools${path.sep}`)) continue;      // the stub sources build their fake token at runtime
      let text: string;
      try { text = f.endsWith(".gz") ? zlib.gunzipSync(fs.readFileSync(f)).toString("utf8") : fs.readFileSync(f, "utf8"); } catch { continue; }
      scanned++;
      const m = TOKEN.exec(text);
      if (m) hits.push(`${path.relative(REPO, f)}: ${m[0].slice(0, 12)}…`);
    }
  }
  assert.ok(scanned > 100, `scanned ${scanned} files`);
  assert.deepEqual(hits, []);
});
