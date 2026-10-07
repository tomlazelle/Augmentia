// Digest equality is absolute: for EVERY recorded preview/apply whose oracle output carries a confirmation digest, the Node
// CLI must produce exactly the same SHA-256 digest (no parity exception exists for this), and every Story item (title and
// rendered body, the digest's input) must be byte-identical. Counts are reported.
import assert from "node:assert/strict";
import { test } from "node:test";
import { Corpus, applicable, replayAll } from "./replay-lib.js";

test("every corpus digest is reproduced exactly", { timeout: 600000 }, async () => {
  const corpus = new Corpus();
  const cases = corpus.cases.filter((c) => applicable(c) && ["publish-preview", "publish-apply"].includes(c.argv[0]!) && c.argv.includes("--json") && c.expected.stdout.includes('"digest"'));
  const results = await replayAll(corpus, cases);
  const expected = cases.map((c) => JSON.parse(c.expected.stdout)?.result?.digest as string | undefined);
  let compared = 0, stories = 0;
  const distinct = new Set<string>();
  results.forEach((r, i) => {
    if (!expected[i]) return;                     // refusals deliberately omit the digest
    assert.equal(r.status, "pass", r.id + ": " + r.problems.join("; "));
    assert.equal(r.digest, expected[i], `${r.id}: digest differs from the oracle`);
    compared++; stories += r.storyItems ?? 0; distinct.add(r.digest!);
  });
  console.log(`# digest equality: ${compared} recorded runs, ${distinct.size} distinct digests, ${stories} Story items (title+body byte-identical)`);
  assert.equal(compared, 81);          // the frozen corpus holds exactly 81 digest-bearing runs ...
  assert.equal(distinct.size, 29);     // ... with 29 distinct digests
});
