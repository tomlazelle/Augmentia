// Publishing semantics that must hold in Node exactly as in the oracle (the corpus holds byte parity; these state the rules).
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { Stub, US1, US2, apply, cli, digestOf, preview, project, read, setRepository, tree } from "./helpers.js";

const changedFiles = (a: Record<string, string>, b: Record<string, string>): string[] =>
  [...new Set([...Object.keys(a), ...Object.keys(b)])].filter((k) => a[k] !== b[k]).sort();

test("preview is offline and read-only: no provider call, no file change, mutations 0", () => {
  const d = project(); const stub = new Stub().use();
  try {
    const before = tree(d);
    const r = preview(d, "US-001", "US-002");
    assert.deepEqual([r.code, r.json.result.mutations, r.json.result.access_checked, r.json.result.can_apply], [0, 0, false, true]);
    assert.equal(stub.calls().length, 0);
    assert.deepEqual(tree(d), before);
    // the preview carries everything the human confirms: target, selection, action, title, rendered body, known/other publications, notices
    const s = r.json.result.stories[0];
    assert.deepEqual(Object.keys(s).sort(), ["action", "blockers", "id", "issue_body", "issue_title", "known_publication", "labels", "other_publications", "path", "title", "warnings"]);
    assert.deepEqual([r.json.result.provider, r.json.result.repository, s.action, s.issue_title, s.labels], ["github", "acme/widgets", "create", "[US-001] Export report", []]);
    assert.ok(s.issue_body.includes("authoritative") && s.issue_body.includes("**Covers:** `PR-001-R001`"));
  } finally { stub.cleanup(); }
});

test("a digest authorizes only that exact content and repository state: every invalidation is refused and changes nothing", () => {
  const stub = new Stub().use();
  try {
    const invalidations: [string, (d: string) => void, string[]][] = [
      ["Story content changed", (d) => fs.writeFileSync(path.join(d, US1), read(d, US1).replace("a file is produced", "a CSV file is produced")), ["US-001"]],
      ["target repository changed", (d) => setRepository(d, "acme/other"), ["US-001"]],
      ["selection changed", () => {}, ["US-001", "US-002"]],
      ["a publication appeared (known state changed)", (d) => fs.appendFileSync(path.join(d, US1), "\n## Publication\n\n### PUB-1 — 2026-09-30\n- **Provider:** github\n- **Repository:** acme/widgets\n- **Issue:** #9\n"), ["US-001"]],
    ];
    for (const [name, change, selection] of invalidations) {
      const d = project();
      const digest = digestOf(preview(d, "US-001"));
      change(d);
      const before = tree(d);
      const r = apply(d, digest, ...selection);
      assert.equal(r.code, 1, name);
      assert.ok(r.json.diagnostics.some((x: any) => x.code === "preview-stale" && x.severity === "error"), name);
      assert.ok(!("digest" in r.json.result) && r.json.result.mutations === 0 && r.json.result.stories.length === 0, `${name}: a refusal must not reveal the digest or bodies`);
      assert.ok(!cli(["publish-apply", ...selection, "--confirm-digest", digest], d).out.includes("sha256:"), name);
      assert.deepEqual(tree(d), before, name);
    }
    assert.equal(stub.calls().length, 0, "no provider call may happen for a stale or missing confirmation");
    const d = project();
    assert.ok(apply(d, null, "US-001").json.diagnostics.some((x: any) => x.code === "confirmation-missing"));
    assert.equal(stub.calls().length, 0);
  } finally { stub.cleanup(); }
});

test("publication changes exactly the Story's `updated` date and its Publication record; status and delivery_status are untouched", () => {
  const d = project(); const stub = new Stub().use();
  try {
    const files = { ...tree(d) };
    fs.writeFileSync(path.join(d, US1), read(d, US1).replace("status: Draft", "status: Approved").replace("delivery_status: Not Started", "delivery_status: Ready"));
    cli(["update-map"], d);
    const before = tree(d);
    const r = apply(d, digestOf(preview(d, "US-001")), "US-001");
    assert.equal(r.code, 0);
    const after = tree(d);
    assert.deepEqual(changedFiles(before, after), [US1], "no file other than the published Story may change");
    const story = after[US1]!;
    assert.match(story, /^status: Approved$/m);
    assert.match(story, /^delivery_status: Ready$/m);
    assert.match(story, /^updated: 2026-09-29$/m);
    assert.equal(story.replace(/^updated: .*$/m, "updated: X"), before[US1]!.replace(/^updated: .*$/m, "updated: X") + "\n## Publication\n\n### PUB-1 — 2026-09-29\n- **Provider:** github\n- **Repository:** acme/widgets\n- **Issue:** #7\n- **URL:** https://github.com/acme/widgets/issues/7\n- **Recorded by:** `sdlc publish-apply` (publication is non-material; local Markdown stays authoritative)\n");
    assert.equal(cli(["validate"], d).code, 0);
    assert.equal(files[US1] === undefined, false);
  } finally { stub.cleanup(); }
});

test("identity is Story + provider + repository: same repository skips, another repository is independently eligible", () => {
  const d = project("org/repo-a"); const stub = new Stub().use();
  try {
    const first = apply(d, digestOf(preview(d, "US-001")), "US-001");
    assert.deepEqual([first.code, first.json.result.outcomes[0].record, first.json.result.outcomes[0].issue], [0, "PUB-1", "#7"]);
    // same repository: shown as known, skipped, nothing created
    const again = preview(d, "US-001");
    assert.deepEqual([again.json.result.stories[0].action, again.json.result.will_create, again.json.result.can_apply, again.json.result.stories[0].known_publication.issue], ["skip", [], false, "#7"]);
    const skipped = apply(d, digestOf(again), "US-001");
    assert.deepEqual([skipped.code, skipped.json.result.mutations, skipped.json.result.outcomes[0].outcome], [0, 0, "skipped"]);
    assert.equal(stub.creates().length, 1);
    // a different repository: CREATE, with the other publication disclosed as a notice, and its own record
    setRepository(d, "org/repo-b");
    const other = preview(d, "US-001");
    const s = other.json.result.stories[0];
    assert.deepEqual([s.action, s.known_publication, s.other_publications.map((p: any) => [p.repository, p.issue])], ["create", null, [["org/repo-a", "#7"]]]);
    assert.ok(other.json.diagnostics.some((x: any) => x.code === "published-elsewhere" && x.severity === "notice"));
    assert.equal(apply(d, null, "US-001").code, 1);            // still gated by the digest
    const second = apply(d, digestOf(other), "US-001");
    assert.deepEqual([second.code, second.json.result.outcomes[0].record, second.json.result.outcomes[0].issue], [0, "PUB-2", "#8"]);
    assert.deepEqual(stub.creates().map((c) => c.argv[c.argv.indexOf("--repo") + 1]), ["org/repo-a", "org/repo-b"]);
    // now both are known; repeating in either repository creates nothing
    for (const repo of ["org/repo-a", "org/repo-b"]) {
      setRepository(d, repo);
      assert.equal(preview(d, "US-001").json.result.stories[0].action, "skip", repo);
    }
    assert.equal(stub.creates().length, 2);
    assert.equal(cli(["validate"], d).code, 0);
  } finally { stub.cleanup(); }
});

test("selection rules: nothing by default, only Stories, unknown Stories and invalid Stories are blocked and never published", () => {
  const d = project(); const stub = new Stub().use();
  try {
    assert.deepEqual([cli(["publish-preview", "--json"], d).code, cli(["publish-preview", "PR-001", "--json"], d).code], [2, 2]);
    const missing = preview(d, "US-001", "US-099");
    assert.deepEqual([missing.code, missing.json.result.blocked, missing.json.result.can_apply], [1, ["US-099"], false]);
    fs.appendFileSync(path.join(d, US2), "\n- [gone](missing.md)\n");
    const blocked = preview(d, "US-002");
    assert.deepEqual([blocked.code, blocked.json.result.blocked], [1, ["US-002"]]);
    const refused = apply(d, digestOf(blocked), "US-002");           // even with the blocked preview's own digest
    assert.equal(refused.code, 1);
    assert.equal(stub.calls().length, 0);
  } finally { stub.cleanup(); }
});

test("configuration failures block preview and apply before anything else", () => {
  const stub = new Stub().use();
  try {
    const d = tmpProjectWithoutPublishing();
    assert.ok(preview(d, "US-001").json.diagnostics.some((x: any) => x.code === "publishing-config-missing"));
    for (const [repository, provider, code] of [["acme/widgets", "jira", "publishing-unsupported-provider"], ["not-a-repo", "github", "publishing-config-invalid"]] as const) {
      const e = project();
      const cfg = path.join(e, ".sdlc", "config.md");
      fs.writeFileSync(cfg, fs.readFileSync(cfg, "utf8").replace("provider: github", `provider: ${provider}`).replace("acme/widgets", repository));
      const r = preview(e, "US-001");
      assert.equal(r.code, 1);
      assert.ok(r.json.diagnostics.some((x: any) => x.code === code && x.severity === "error"), code);
      assert.equal(apply(e, "sha256:x", "US-001").code, 1);
    }
    assert.equal(stub.calls().length, 0);
  } finally { stub.cleanup(); }
});

function tmpProjectWithoutPublishing(): string {
  const d = project();
  const cfg = path.join(d, ".sdlc", "config.md");
  fs.writeFileSync(cfg, fs.readFileSync(cfg, "utf8").replace(/publishing:\n {2}provider: github\n {2}repository: [^\n]*\n/, ""));
  return d;
}

test("when records for the same repository were hand-edited into duplicates, the latest record is the one shown (oracle behavior)", () => {
  const d = project("org/repo-a"); const stub = new Stub().use();
  try {
    assert.equal(apply(d, digestOf(preview(d, "US-001")), "US-001").code, 0);
    const file = fs.readdirSync(path.join(d, "Stories")).map((f) => path.join(d, "Stories", f)).find((f) => fs.readFileSync(f, "utf8").includes("PUB-1"))!;
    const text = fs.readFileSync(file, "utf8");
    const at = text.indexOf("### PUB-1");
    assert.ok(at > 0);
    const entry = text.slice(at).replace("PUB-1", "PUB-2").replace(/#7\b/g, "#99").replace(/\/7\b/g, "/99");
    fs.writeFileSync(file, text.replace(/\n*$/, "\n\n") + entry);
    const r = preview(d, "US-001");
    assert.equal(r.json.result.stories[0].known_publication.issue, "#99");
  } finally { stub.cleanup(); }
});
