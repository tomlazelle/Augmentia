// Static checks on the packaged Skill sources and shared conventions, plus template instantiation through the real CLI
// (port of tests/unit/test_skills.py). These are text/contract checks; Skill text is unchanged by the migration except
// where it named Python/pipx.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { parse, split } from "../src/frontmatter.js";
import { cli, tmpdir } from "./helpers.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PKG = path.join(HERE, "..", "..");
const ROOT = PKG;
const TEMPLATES = path.join(PKG, "templates");
const NAMES = fs.readdirSync(path.join(ROOT, "skills"), { withFileTypes: true }).filter((e) => e.isDirectory()).map((e) => e.name).sort();
const CREATING = ["create-brd", "create-prd", "create-stories"];
const TECH = ["refine-stories", "create-design", "plan-implementation", "implement-story", "review-implementation", "create-test-plan", "verify-story"];
const TECH_CREATING: Record<string, [string, string]> = { "create-design": ["DES", "design"], "plan-implementation": ["PLAN", "plans"], "create-test-plan": ["TEST", "tests"] };
const PATH_TOKEN = /`((?:references\/|\.\.\/\.\.\/shared\/|\.\.\/\.\.\/\.\.\/shared\/)[\w./-]+\.md)`/g;

const rd = (...p: string[]): string => fs.readFileSync(path.join(ROOT, ...p), "utf8");
const skill = (name: string): string => rd("skills", name, "SKILL.md");
const ref = (name: string, file: string): string => rd("skills", name, "references", file);
const shared = (file: string): string => rd("shared", file);
const has = (text: string, ...needles: string[]): void => { for (const n of needles) assert.ok(text.includes(n), n); };
const idx = (text: string, needle: string): number => { const i = text.indexOf(needle); assert.ok(i >= 0, `missing: ${needle}`); return i; };
const resolves = (base: string, token: string): boolean => fs.existsSync(`${base}/${token}`);   // no lexical normalisation: resolve through symlinks like the agent does

function helpFlags(command: string): Set<string> {
  const r = cli([command, "--help"], tmpdir());
  assert.equal(r.code, 0, command);
  return new Set(r.out.match(/--[a-z-]+/g) ?? []);
}
const COMMANDS = ["init", "allocate-id", "retire-id", "create-dir", "update-map", "list", "references", "find-overlaps", "status", "publish-preview", "publish-apply", "validate"];

test("there are 15 Skills and the creating Skills and interview guide are present", () => {
  assert.equal(NAMES.length, 15);
  for (const n of CREATING) assert.ok(NAMES.includes(n));
  assert.ok(fs.existsSync(path.join(ROOT, "shared", "interview.md")));
});

for (const name of NAMES) {
  test(`${name}: front matter valid, referenced files exist, only real CLI commands and flags, no embedded algorithms`, () => {
    const text = skill(name);
    const [raw] = split(text);
    const meta = parse(raw!) as Record<string, string>;
    assert.ok(meta["name"] === name && meta["description"]!.length > 40 && meta["description"]!.length <= 1024);
    assert.deepEqual(Object.keys(meta).sort(), ["description", "name"]);
    const dir = path.join(ROOT, "skills", name);
    for (const m of text.matchAll(PATH_TOKEN)) assert.ok(fs.existsSync(path.resolve(dir, m[1]!)), m[1]);
    const refDir = path.join(dir, "references");
    if (fs.existsSync(refDir)) for (const f of fs.readdirSync(refDir).filter((x) => x.endsWith(".md"))) {
      for (const m of fs.readFileSync(path.join(refDir, f), "utf8").matchAll(PATH_TOKEN)) assert.ok(fs.existsSync(path.resolve(refDir, m[1]!)) || fs.existsSync(path.resolve(dir, m[1]!)), `${f}: ${m[1]}`);
    }
    for (const m of text.matchAll(/`sdlc ([a-z-]+)([^`]*)`/g)) {
      assert.ok(COMMANDS.includes(m[1]!), m[1]);
      const known = helpFlags(m[1]!);
      for (const flag of m[2]!.match(/--[a-z-]+/g) ?? []) assert.ok(known.has(flag), `${name}: ${m[1]} ${flag}`);
    }
    assert.ok(!text.includes("```"));
    assert.ok(!/highest (existing )?(ID|number)|plus one|max\(|glob\(/.test(text));
    if (TECH.includes(name)) has(text, "technical-conventions.md");
  });
}

for (const name of CREATING) {
  test(`${name}: supporting files, workflow order, rules, verbatim overlaps, mandatory recap, contextual overlap review`, () => {
    for (const f of ["section-catalog.md", "discovery-questions.md", "template.md"]) assert.ok(fs.existsSync(path.join(ROOT, "skills", name, "references", f)));
    const text = skill(name);
    assert.ok(idx(text, "find-overlaps") < idx(text, "allocate-id --category"));
    assert.ok(idx(text, "update-map") < text.lastIndexOf("validate"));
    has(text, "shared/interview.md", "Draft", "In Review", "Approved", "TBD", "coverage notices", ...(name === "create-stories" ? ["covers"] : ["retire-id", "allocate-id --requirement"]));
    assert.match(text, /[Nn]ever set `status: Approved` on your own/);
    has(text, "ask the user to choose", "exactly as the CLI returned them", "Do not paraphrase, round, reorder, summarize or invent any ID, score or reason", "mandatory recap");
    const cat = { "create-brd": "BR", "create-prd": "PR", "create-stories": "US" }[name]!;
    const mapfile = { BR: "BR/map.md", PR: "PR/map.md", US: "Stories/map.md" }[cat]!;
    const cliAt = idx(text, "exactly as the CLI returned them"), review = idx(text, "Contextual overlap review"), alloc = idx(text, "allocate-id --category");
    assert.ok(idx(text, "find-overlaps") < cliAt && cliAt < review && review < alloc);
    has(text, `sdlc list --category ${cat}`, mapfile, "Conceptual overlaps (my judgement, not CLI-scored)", "separately", "Never attach a score, percentage or level", "never invent a similarity value",
      "No conceptual overlaps found.", "even when the CLI returned no candidates", "**revise**", "**relate**", "**create new**", "Do not allocate an ID until they choose", "Related To");
  });
}

test("create-stories forbids delivery states and invented IDs, supports standalone Stories, and reviews covered requirements", () => {
  const text = skill("create-stories");
  has(text, "Never set `delivery_status` to `In Progress`, `Implemented` or `Verified`", "Never invent requirement IDs", "standalone", "story-no-coverage", "covers: []", "which requirement IDs existing Stories already cover");
});

test("the interview guide: contents and mandatory recap boundary", () => {
  has(shared("interview.md"), "3–5", "Unknown", "TBD", "Not applicable", "Assumption", "Round 1", "Round 2", "before writing", "suggested option",
    "Mandatory recap between rounds", "Recap so far", "Skipping it is not allowed", "Recap before Round 2 (mandatory)", "Move from one question round to the next without the recap");
});

test("unresolved acceptance is TBD, not an executable criterion", () => {
  has(skill("create-stories"), "not** an acceptance criterion", "Unresolved Acceptance Behavior (TBD)");
  has(ref("create-stories", "template.md"), "### Unresolved Acceptance Behavior (TBD)", "- **TBD** —");
  has(ref("create-stories", "section-catalog.md"), "Verifiable versus unresolved", "decided, observable");
  has(ref("create-prd", "section-catalog.md"), "duplicate detection", "`- **TBD** — <question>`");
  has(skill("create-brd"), "TBD", "never as an assertion");
});

test("project instruction templates are narrow workflow guidance, identical, and route publishing through the Skill", () => {
  const agents = fs.readFileSync(path.join(TEMPLATES, "AGENTS.md"), "utf8");
  assert.equal(agents, fs.readFileSync(path.join(TEMPLATES, "CLAUDE.md"), "utf8"));
  has(agents, "create-brd", "create-prd", "create-stories", "refine-stories", "create-design", "plan-implementation", "create-test-plan", "implement-story",
    "review-implementation", "verify-story", "Approved", "In Review", "revision rules", "SKILL.md", "actually run and recorded", "publish-stories", "explicit confirmation", "sdlc-status");
  assert.ok(!/\b(hash|checksum|daemon|database)/i.test(agents));
  assert.ok(agents.split("\n").length - 1 < 40);
});

test("cli-contract documents lexical limit, instruction files, R3 commands and rules", () => {
  const text = shared("cli-contract.md");
  has(text, "contextual overlap review", "Scoring is lexical", "create-if-missing", "AGENTS.md", "CLAUDE.md", "### `status`", "### `publish-preview", "### `publish-apply",
    "publication-invalid", "preview-stale", "confirmation-missing", "SDLC_GH_COMMAND", "publishing-config-missing", "npm install -g @augmentia/sdlc");
});

test("technical Skills: shared conventions, optional Design/Research/Plan, and the state-setting contracts", () => {
  for (const n of TECH) assert.ok(NAMES.includes(n));
  has(shared("technical-conventions.md"), "Two separate states", "delivery_status` transitions", "Rework and invalidation", "Implementation Record", "Verification Runs", "Review Record",
    "passed", "blocked", "not-run", "Superseded", "Inspect before proposing", "### RV-1 — ");
  const design = skill("create-design");
  assert.ok(design.includes("optional Research") || design.includes("optional Research note"));
  assert.ok(/never required|not required/i.test(design));
  assert.ok(skill("plan-implementation").includes("without a Design"));
  assert.ok(fs.existsSync(path.join(ROOT, "skills", "create-design", "references", "research-template.md")));

  has(skill("refine-stories"), "Never set `delivery_status: Ready` because you think the Story is ready", "you never set `In Progress`, `Implemented` or `Verified`", "Invalidation", "`Ready`",
    "Superseded:** yes — Story changed", "never `then … TBD`");
  assert.ok(fs.existsSync(path.join(ROOT, "skills", "refine-stories", "references", "readiness-checklist.md")));

  const impl = skill("implement-story");
  has(impl, "Only this Skill sets `Implemented`", "you never set `Verified`", "you never set `Ready`", "explicit go-ahead", "Implementation Record", "Tests run", "Never claim completion from generated code alone",
    "never invent a pass", "`Not Started`", "Superseded", "In Progress", "reserved for `verify-story`", "Superseded:** yes — new implementation pass");
  assert.ok(idx(impl, "Get authorization") < idx(impl, "Set `delivery_status: In Progress`") && idx(impl, "Set `delivery_status: In Progress`") < idx(impl, "Run the tests for real"));

  const verify = skill("verify-story");
  has(verify, "Only this Skill sets `Verified`", "`passed`", "`failed`", "`blocked`", "`not-run`", "exit code", "date -u", "Artifacts/tests/evidence/", "never edit or delete earlier runs",
    "every numbered decided criterion", "Unresolved TBD behavior is **not** verified", "Review Record", "Never claim an unrun command passed", "Criteria: none", "never a personal email address",
    "Set `delivery_status: Verified`", "only if");

  const review = skill("review-implementation");
  has(review, "read-only", "not verification", "blocker", "major", "minor", "nit", "verified observation", "potential concern", "complete", "requires-rework", "blocked", "Never set or imply `Verified`",
    "Suggest; do not apply", "### RV-<n> — <YYYY-MM-DD>", "RV, not RR");

  for (const n of TECH) if (n !== "verify-story") assert.ok(!/(?<!never )(?<!Never )[Ss]et `delivery_status: Verified`/.test(skill(n).replace("never set `Verified`", "")), n);
  has(impl, "Set `delivery_status: Implemented`");
  assert.ok(!verify.includes("Set `delivery_status: Implemented`"));
});

for (const [name, [cat, sub]] of Object.entries(TECH_CREATING)) {
  test(`${name}: follows the R1 workflow (overlap check, review, create-dir, allocate)`, () => {
    for (const f of ["section-catalog.md", "discovery-questions.md", "template.md"]) assert.ok(fs.existsSync(path.join(ROOT, "skills", name, "references", f)));
    const text = skill(name);
    const cliAt = idx(text, "exactly as the CLI returned them"), review = idx(text, "Contextual overlap review"), create = idx(text, `create-dir --artifact ${sub}`), alloc = idx(text, `allocate-id --category ${cat}`);
    assert.ok(idx(text, "find-overlaps") < cliAt && cliAt < review && review < create && create < alloc);
    has(text, `find-overlaps --category ${cat}`, `list --category ${cat}`, "mandatory recap", "Conceptual overlaps (my judgement, not CLI-scored)", "**revise**", "**relate**", "**create new**",
      "Do not allocate an ID until they choose", "Inspect the repository", "In Review", "Never change a Story's `delivery_status`", "Never set `status: Approved` on your own", "Derived From", "coverage notices");
    assert.ok(idx(text, "update-map") < text.lastIndexOf("validate"));
  });
}

test("R3 Skills: sdlc-status is read-only; publish-stories enforces preview, explicit confirmation and no scope creep", () => {
  for (const n of ["sdlc-status", "publish-stories"]) { assert.ok(NAMES.includes(n)); has(skill(n), "../../shared/publishing-conventions.md"); }
  const status = skill("sdlc-status");
  has(status, "sdlc status", "Read-only", "conversation memory", "informational", "not a defect", "Never run `init`, `allocate-id`, `retire-id`, `create-dir` or `update-map`");
  for (const forbidden of ["sdlc update-map`,", "sdlc allocate-id`,"]) assert.ok(!status.split("## Rules")[0]!.includes(forbidden));
  const pub = skill("publish-stories");
  const flow = pub.split("## Workflow")[1]!.split("## Rules")[0]!;
  assert.ok(idx(flow, "publish-preview") < idx(flow, "Ask for explicit confirmation") && idx(flow, "Ask for explicit confirmation") < idx(flow, "publish-apply"));
  has(pub, "verbatim", "complete body", "not** confirmation", "--confirm-digest", "Never create an Issue yourself", "never one printed by a refused apply", "No external mutation before a shown preview",
    "preview-stale", "Never print or store credentials", "never changes requirements, acceptance criteria, `status` or `delivery_status`", "Do not update, close, label or edit existing Issues",
    "do not import anything from GitHub", "open or closed Issue says nothing about `delivery_status`", "do not create PRs, branches", "you have not read it",
    "gained a `## Publication` record and a new `updated` date, and nothing else");
  assert.equal(pub.split("gh issue create").length - 1, 1);
  const conv = shared("publishing-conventions.md");
  has(conv, "Local Markdown is authoritative", "preview-stale", "## Publication", "PUB-1", "Non-material metadata", "never matched to a Story by its title", "GH_TOKEN", "published-unrecorded", "unconfirmed",
    "publishing:\n  provider: github\n  repository: owner/repository");
});

// ---- templates instantiate into documents the validator accepts --------------------------------

function sandbox(): { d: string; ok: (...a: string[]) => any; run: (...a: string[]) => { code: number; json: any }; diags: (j: any, code: string) => any[] } {
  const d = tmpdir("sdlc-sk-");
  process.env["SDLC_TODAY"] = "2026-09-29";
  assert.equal(cli(["init", "--project-name", "Demo"], d).code, 0);
  const run = (...a: string[]) => { const r = cli([...a, "--json"], d); return { code: r.code, json: r.json }; };
  const ok = (...a: string[]) => { const r = run(...a); assert.equal(r.code, 0, JSON.stringify(r.json)); return r.json; };
  return { d, ok, run, diags: (j, code) => j.diagnostics.filter((x: any) => x.code === code) };
}

function instantiate(skillName: string, id: string, title: string, o: { covers?: string; derived?: string; tmpl?: string; tech?: string } = {}): string {
  let text = ref(skillName, o.tmpl ?? "template.md");
  const rep = (k: string, v: string) => { text = text.split(k).join(v); };
  rep("{{ID}}", id); rep("{{TITLE}}", title); rep("{{DATE}}", "2026-09-29"); rep("{{ONE_SENTENCE_PURPOSE}}", "A purpose."); rep("{{ONE_SENTENCE_VALUE}}", "A value.");
  rep("{{REQUIREMENT_IDS_OR_EMPTY}}", o.covers ?? "");
  if (o.tech) { rep("{{SOURCE_STORY_LINK_AND_REQUIREMENT_IDS}}", o.tech); rep("{{SOURCE_STORY_OR_DESIGN_LINK}}", o.tech); }
  if (o.derived) text = text.replace("### Derived From\n- None identified.", `### Derived From\n- ${o.derived}`);
  return text.replace(/\{\{[^}]*\}\}/g, "Placeholder content.");
}
const put = (d: string, rel: string, text: string) => fs.writeFileSync(path.join(d, rel), text);

test("BRD and PRD templates yield valid documents, with and without a BRD", () => {
  const s = sandbox();
  s.ok("allocate-id", "--category", "BR", "--title", "T"); s.ok("allocate-id", "--requirement", "BR-001");
  put(s.d, "BR/BR-001-t.md", instantiate("create-brd", "BR-001", "T")); s.ok("update-map");
  assert.equal(s.run("validate").code, 0);
  const refs = s.ok("references", "BR-001-R001").result;
  assert.deepEqual([refs.defined_in.id, refs.incoming.length], ["BR-001", 0]);
  s.ok("allocate-id", "--category", "PR", "--title", "P"); s.ok("allocate-id", "--requirement", "PR-001");
  put(s.d, "PR/PR-001-p.md", instantiate("create-prd", "PR-001", "P"));
  s.ok("allocate-id", "--category", "PR", "--title", "Q"); s.ok("allocate-id", "--requirement", "PR-002");
  put(s.d, "PR/PR-002-q.md", instantiate("create-prd", "PR-002", "Q", { derived: "[BR-001 — T](../BR/BR-001-t.md) — serves BR-001-R001" }));
  s.ok("update-map");
  const v = s.run("validate");
  assert.equal(v.code, 0, JSON.stringify(v.json.diagnostics));
  assert.ok(fs.readFileSync(path.join(s.d, "PR", "map.md"), "utf8").includes("Derived From"));
});

test("Story template: standalone and covering; covers without a link is rejected; unresolved section still validates", () => {
  const s = sandbox();
  s.ok("allocate-id", "--category", "PR", "--title", "P"); s.ok("allocate-id", "--requirement", "PR-001");
  put(s.d, "PR/PR-001-p.md", instantiate("create-prd", "PR-001", "P"));
  s.ok("allocate-id", "--category", "US", "--title", "Alone");
  put(s.d, "Stories/US-001-alone.md", instantiate("create-stories", "US-001", "Alone"));
  s.ok("allocate-id", "--category", "US", "--title", "Linked");
  put(s.d, "Stories/US-002-linked.md", instantiate("create-stories", "US-002", "Linked", { covers: "PR-001-R001", derived: "[PR-001 — P](../PR/PR-001-p.md)" }));
  s.ok("update-map");
  const v = s.run("validate");
  assert.equal(v.code, 0, JSON.stringify(v.json.diagnostics));
  assert.deepEqual(v.json.diagnostics.filter((x: any) => x.severity === "notice").map((x: any) => [x.code, x.id]), [["story-no-coverage", "US-001"]]);
  s.ok("allocate-id", "--category", "US", "--title", "Bad");
  put(s.d, "Stories/US-003-bad.md", instantiate("create-stories", "US-003", "Bad", { covers: "PR-001-R001" }));
  s.ok("update-map");
  assert.ok(s.diags(s.run("validate").json, "covers-source-not-linked").length > 0);
});

test("technical templates instantiate into valid, linked documents; the test-plan template carries no runs", () => {
  const s = sandbox();
  s.ok("allocate-id", "--category", "PR", "--title", "P"); s.ok("allocate-id", "--requirement", "PR-001");
  put(s.d, "PR/PR-001-p.md", instantiate("create-prd", "PR-001", "P"));
  s.ok("allocate-id", "--category", "US", "--title", "S");
  put(s.d, "Stories/US-001-s.md", instantiate("create-stories", "US-001", "S", { covers: "PR-001-R001", derived: "[PR-001 — P](../PR/PR-001-p.md)" }));
  const link = "[US-001 — S](../../Stories/US-001-s.md) — serves PR-001-R001";
  for (const [sk, cat, sub, tmpl] of [["create-design", "DES", "design", "template.md"], ["create-design", "RES", "research", "research-template.md"],
    ["plan-implementation", "PLAN", "plans", "template.md"], ["create-test-plan", "TEST", "tests", "template.md"]] as const) {
    s.ok("create-dir", "--artifact", sub);
    const id = s.ok("allocate-id", "--category", cat, "--title", "Thing").result.id;
    put(s.d, `Artifacts/${sub}/${id}-thing.md`, instantiate(sk, id, "Thing", { tech: link, tmpl }));
  }
  s.ok("update-map");
  const v = s.run("validate");
  assert.equal(v.code, 0, JSON.stringify(v.json.diagnostics));
  for (const [sub, prefix] of [["design", "DES"], ["plans", "PLAN"], ["research", "RES"], ["tests", "TEST"]]) assert.ok(fs.readFileSync(path.join(s.d, "Artifacts", sub, "map.md"), "utf8").includes(`${prefix}-001`));
  assert.deepEqual(new Set(s.ok("references", "US-001").result.incoming.map((i: any) => i.source.id)), new Set(["DES-001", "RES-001", "PLAN-001", "TEST-001"]));
  const plan = ref("create-test-plan", "template.md");
  has(plan, "## Repository Context", "### Inspected", "## Verification Runs\n\nNone recorded.", "## Unresolved Acceptance Behavior (TBD)", "TS-1", "AC-1");
  assert.ok(!plan.includes("### Unresolved Acceptance Behavior"));
});
