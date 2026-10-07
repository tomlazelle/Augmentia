// PARITY-EXCEPTION-005 (approved): SDLC identifiers use ASCII digits 0-9 only; Python's accidental acceptance of other
// Unicode decimal digits through `\d` is intentionally not reproduced.
import assert from "node:assert/strict";
import { test } from "node:test";
import { DOC_ID_RE, FILENAME_RE, REQ_ID_RE, idKind } from "../src/model.js";

test("IDs and filenames accept only ASCII digits", () => {
  assert.equal(idKind("BR-001"), "document");
  assert.equal(idKind("PR-001-R003"), "requirement");
  for (const bad of ["BR-٠٠١", "BR-００１", "PR-001-R٣٣٣", "BR-12", "XX-001"]) assert.equal(idKind(bad), null, bad);
  assert.ok(!FILENAME_RE.test("BR-٠٠١-x.md") && FILENAME_RE.test("BR-001-x.md"));
  assert.ok(DOC_ID_RE.source.includes("[0-9]") && REQ_ID_RE.source.includes("[0-9]") && !/\\d/.test(DOC_ID_RE.source + REQ_ID_RE.source + FILENAME_RE.source));
});
