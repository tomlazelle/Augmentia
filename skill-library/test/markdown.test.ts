import assert from "node:assert/strict";
import { test } from "node:test";
import { extractHrefs, maskRegion, parseBody, reqTokens } from "../src/markdown.js";

test("extractHrefs keeps local targets only and decodes them", () => {
  assert.deepEqual(extractHrefs("see [a](../PR/PR-001-x.md#sec) and [b](https://x.test) and [c](#top) and [d](<sp ace.md>) and `[e](code.md)`"),
    ["../PR/PR-001-x.md", "sp ace.md"]);
  assert.deepEqual(extractHrefs("[x](a%20b.md?q=1 \"title\")"), ["a b.md"]);
  assert.deepEqual(extractHrefs("[q](?only=query) ![img](pic.png)"), ["pic.png"]);
});

test("requirement tokens respect word boundaries (including non-ASCII letters)", () => {
  assert.deepEqual(reqTokens("PR-001-R002, PR-001-R001 and `PR-009-R001` and xPR-002-R001 and éPR-003-R001 and PR-004-R001z"), ["PR-001-R001", "PR-001-R002"]);
});

test("parseBody: requirements, malformed declarations, References sections, fences", () => {
  const text = [
    "---", "id: PR-001", "---", "", "# T", "",
    "## References", "", "### Derived From", "- [BR](../BR/BR-001-x.md) — serves BR-001-R001", "- BR-001-R002 without a link", "### Other", "- [o](o.md)", "",
    "## Requirements", "", "- **PR-001-R001** — A requirement.", "- **PR-001-R002** — Another.", "### **PR-001-R003** — Heading form", "- **PR-001-R4** - malformed", "",
    "```", "- **PR-001-R099** — inside a fence", "[f](fence.md)", "```", "~~~", "~~~", "after [a](after.md)",
  ];
  const parsed = parseBody(text, 4);
  assert.deepEqual(parsed.requirements.map((r) => [r.id, r.text]), [["PR-001-R001", "A requirement."], ["PR-001-R002", "Another."], ["PR-001-R003", "Heading form"]]);
  assert.equal(parsed.malformed.length, 1);
  assert.deepEqual(parsed.refs.map((r) => [r.section, r.href, r.reqIds]), [
    ["Derived From", "../BR/BR-001-x.md", ["BR-001-R001"]], ["Derived From", null, ["BR-001-R002"]], ["Other", "o.md", []]]);
  assert.deepEqual(parsed.links.map(([, h]) => h), ["../BR/BR-001-x.md", "o.md", "after.md"]);
});

test("maskRegion blanks a marker-delimited region but keeps line numbers", () => {
  assert.equal(maskRegion("a\n<S>\nx\ny\n<E>\nb", "<S>", "<E>"), "a\n\n\n\n\nb".replace("a\n\n\n\n\nb", "a\n" + "\n\n\n" + "\nb"));
  assert.equal(maskRegion("no markers", "<S>", "<E>"), "no markers");
});
