// Oracle-confirmed regression (python-1.0.0rc1): numbered items after a `###` subsection of "Acceptance Criteria" are NOT
// decided criteria, so a Verified Story whose only decided criterion AC-1 has a passed run validates (exit 0) with just the
// TBD warning and the not-in-ledger/standalone notices. Counting past the subsection would demand a run for AC-2 and fail.
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

test("acceptance criteria counting stops at the first ### subsection", () => {
  const d = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-ac-")));
  process.env["SDLC_TODAY"] = "2026-09-29";
  cli(["init", "--project-name", "Ac"], d);
  cli(["create-dir", "--artifact", "tests"], d);
  fs.mkdirSync(path.join(d, "Artifacts", "tests", "evidence"), { recursive: true });
  const head = (id: string, title: string, extra = "") => `---\nid: ${id}\ntitle: ${title}\npurpose: ${title} purpose.\nstatus: Draft\ncreated: 2026-09-01\nupdated: 2026-09-01\n${extra}---\n\n# ${id} — ${title}\n`;
  fs.writeFileSync(path.join(d, "Stories", "US-001-ac-counting.md"), head("US-001", "AC counting", "delivery_status: Verified\ncovers: []\n") +
    "\n## Acceptance Criteria\n\n1. **Given** a, **when** b, **then** c.\n\n### Unresolved Acceptance Behavior (TBD)\n\n- **TBD** — open question\n\n" +
    "1. A numbered item under the subsection is not a decided criterion.\n\n## Implementation Record\n\n### IR-1 — 2026-09-29\n- **Summary:** done\n- **Files changed:** `a.py`\n");
  fs.writeFileSync(path.join(d, "Artifacts", "tests", "TEST-001-plan.md"), head("TEST-001", "Plan") +
    "\n## Verification Runs\n\n### VR-1 — 2026-09-29T10:00:00Z\n- **Story:** US-001\n- **Kind:** automated\n- **Result:** passed\n- **Criteria:** AC-1\n- **Command:** `pytest`\n- **Exit code:** 0\n- **Environment:** py\n- **Performed by:** agent (t)\n- **Observed:** ok\n");
  cli(["update-map"], d);
  const r = JSON.parse(cli(["validate", "--json"], d).out);
  assert.equal(r.exit_code, 0);
  assert.deepEqual(r.result.summary, { error: 0, warning: 3, notice: 1 });
  assert.deepEqual(r.diagnostics.map((x: { severity: string; code: string }) => `${x.severity} ${x.code}`),
    ["warning not-in-ledger", "warning not-in-ledger", "warning verified-with-unresolved-tbd", "notice story-no-coverage"]);
  fs.rmSync(d, { recursive: true, force: true });
});
