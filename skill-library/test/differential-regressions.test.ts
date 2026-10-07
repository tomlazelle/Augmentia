// Defects found by the Layer C differential run (Python vs Node on generated inputs); each pins the oracle's behavior.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { cli, tmpdir } from "./helpers.js";

function fresh(): string {
  const d = tmpdir();
  process.env["SDLC_TODAY"] = "2026-09-29";
  assert.equal(cli(["init"], d).code, 0);
  return d;
}

test("argparse: an unknown '-…' argument containing a space is a value, not an option (oracle: exit 0)", () => {
  const d = fresh();
  for (const title of ["- dash start", "-x y", "--not an option"]) {
    const r = cli(["find-overlaps", "--category", "BR", "--title", title, "--json"], d);
    assert.equal(r.code, 0, title);
  }
  const a = cli(["allocate-id", "--category", "BR", "--title", "- dash start", "--json"], d);
  assert.deepEqual([a.code, a.json.result.id, a.json.result.path], [0, "BR-001", "BR/BR-001-dash-start.md"]);
  // without a space it is still an unknown option
  assert.equal(cli(["allocate-id", "--category", "BR", "--title", "-dash"], d).code, 2);
  assert.equal(cli(["allocate-id", "--category", "BR", "--title"], d).code, 2);
});

test("a YAML timestamp title/purpose is rendered with Python's str(datetime), not repr", () => {
  const d = fresh();
  assert.equal(cli(["allocate-id", "--category", "US", "--title", "Thing"], d).code, 0);
  const file = path.join(d, "Stories", "US-001-thing.md");
  const story = (title: string) => `---\nid: US-001\ntitle: ${title}\npurpose: A thing.\nstatus: Draft\ndelivery_status: Not Started\ncovers: []\ncreated: 2026-09-01\nupdated: 2026-09-01\n---\n\n# Thing\n\n## Acceptance Criteria\n\n1. **Given** a, **when** b, **then** c.\n`;
  const expected: Record<string, string> = {
    "2026-09-29T10:00:00": "2026-09-29 10:00:00",
    "2026-09-29T10:00:00Z": "2026-09-29 10:00:00+00:00",
    "2026-09-29 10:00:00.5+05:30": "2026-09-29 10:00:00.500000+05:30",
    "2026-09-29T10:00:00-0830": "2026-09-29T10:00:00-0830",   // not a YAML timestamp: stays a string
    "2026-09-29": "2026-09-29",
  };
  for (const [yaml, str] of Object.entries(expected)) {
    fs.writeFileSync(file, story(yaml));
    const r = cli(["references", "US-001", "--json"], d);
    assert.equal(r.json.result.title, str, yaml);
  }
});
