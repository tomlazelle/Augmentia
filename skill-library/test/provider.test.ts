// Provider/stub failure matrix. PARITY-EXCEPTION-001 (approved): ANY failure to start the provider executable is
// `provider-unavailable`; the oracle's exact text is kept for "not found". PARITY-EXCEPTION-006 (proposed): a repository-view
// response that is valid JSON but not an object is `provider-failed` (Python crashes). Nothing is ever recorded on failure.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { GitHubCli, ProviderError, redact } from "../src/github.js";
import { BASE_FILES, Stub, US1, apply, cli, digestOf, preview, project, read, tmpdir, tree } from "./helpers.js";

function failOf(fn: () => unknown): ProviderError {
  try { fn(); } catch (e) { assert.ok(e instanceof ProviderError, String(e)); return e; }
  assert.fail("expected a ProviderError");
}

// --- PARITY-EXCEPTION-001: every way of not being able to start `gh` --------------------------------------------------
test("EX-001: failures to START the provider executable are provider-unavailable, whatever the mechanism", () => {
  const dir = tmpdir("sdlc-start-");
  const nonExec = path.join(dir, "not-executable"); fs.writeFileSync(nonExec, "#!/bin/sh\nexit 0\n"); fs.chmodSync(nonExec, 0o644);
  const aDirectory = path.join(dir, "a-directory"); fs.mkdirSync(aDirectory);
  const badInterp = path.join(dir, "bad-interpreter"); fs.writeFileSync(badInterp, "#!/nonexistent/interpreter\n"); fs.chmodSync(badInterp, 0o755);
  const noExecDir = path.join(dir, "locked"); fs.mkdirSync(noExecDir); fs.writeFileSync(path.join(noExecDir, "gh"), "#!/bin/sh\nexit 0\n"); fs.chmodSync(path.join(noExecDir, "gh"), 0o755); fs.chmodSync(noExecDir, 0o000);
  const cases: [string, string][] = [
    ["missing executable (ENOENT)", path.join(dir, "no-such-gh")], ["file without execute permission (EACCES)", nonExec], ["a directory (EACCES)", aDirectory],
    ["interpreter in the shebang does not exist (ENOENT)", badInterp], ["executable inside a directory without search permission (EACCES)", path.join(noExecDir, "gh")],
  ];
  try {
    for (const [what, command] of cases) {
      for (const op of [(p: GitHubCli) => p.checkAccess("acme/widgets"), (p: GitHubCli) => p.createIssue("acme/widgets", "t", "b")]) {
        const e = failOf(() => op(new GitHubCli(command)));
        assert.equal(e.code, "provider-unavailable", `${what}: ${e.message}`);
        assert.ok(e.message.includes(command), what);
      }
    }
    // the oracle's exact wording is kept where the oracle had a defined behaviour (a missing executable)
    assert.equal(failOf(() => new GitHubCli(path.join(dir, "no-such-gh")).checkAccess("a/b")).message, `GitHub CLI '${path.join(dir, "no-such-gh")}' was not found; install gh and run 'gh auth login'`);
    assert.match(failOf(() => new GitHubCli(nonExec).checkAccess("a/b")).message, /could not be started \(EACCES\)/);
  } finally { fs.chmodSync(noExecDir, 0o755); fs.rmSync(dir, { recursive: true, force: true }); }
});

test("EX-001 end to end: publish-apply with an unusable gh exits 1 with provider-unavailable, no traceback, nothing changed", () => {
  const d = project();
  const dir = tmpdir("sdlc-start-");
  const nonExec = path.join(dir, "gh"); fs.writeFileSync(nonExec, "#!/bin/sh\nexit 0\n"); fs.chmodSync(nonExec, 0o644);
  try {
    process.env["SDLC_GH_COMMAND"] = nonExec;
    const digest = digestOf(preview(d, "US-001"));
    const before = tree(d);
    const r = apply(d, digest, "US-001");
    assert.equal(r.code, 1);
    assert.deepEqual(r.json.diagnostics.filter((x: any) => x.severity === "error").map((x: any) => x.code), ["provider-unavailable"]);
    assert.equal(r.json.result.mutations, 0);
    assert.ok(!r.err.includes("Error:") && !r.err.includes("at "), r.err);
    assert.deepEqual(tree(d), before);
  } finally { delete process.env["SDLC_GH_COMMAND"]; fs.rmSync(dir, { recursive: true, force: true }); }
});

test("timeout is a provider-failed error (deterministic: injected short timeout, constant message)", () => {
  const dir = tmpdir("sdlc-slow-");
  const slow = path.join(dir, "gh"); fs.writeFileSync(slow, "#!/bin/sh\nsleep 5\n"); fs.chmodSync(slow, 0o755);
  try {
    const t0 = Date.now();
    const e = failOf(() => new GitHubCli(slow, 300).checkAccess("acme/widgets"));
    assert.equal(e.code, "provider-failed");
    assert.equal(e.message, `'${slow} auth' timed out after 60s`);   // the oracle's text, including its fixed 60s figure
    assert.ok(Date.now() - t0 < 4000);
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

// --- stub-driven failure matrix (preflight and creation) --------------------------------------------------------------
const PREFLIGHT: [string, Record<string, unknown>, string, RegExp][] = [
  ["not authenticated", { unauthenticated: true }, "provider-auth", /not authenticated; run 'gh auth login'/],
  ["repository not found", { repo_missing: true }, "repository-not-found", /was not found or is not accessible/],
  ["issues disabled", { issues_disabled: true }, "issues-disabled", /Issues are disabled on acme\/widgets/],
  ["repository read fails (HTTP 500)", { repo_error: true }, "provider-failed", /could not read repository acme\/widgets: HTTP 500/],
  ["repository response is not JSON", { repo_bad_json: true }, "provider-failed", /unexpected response when reading repository/],
  ["repository response is JSON but an array (EX-006)", { repo_json: [] }, "provider-failed", /unexpected response when reading repository/],
  ["repository response is JSON null (EX-006)", { repo_json: null }, "provider-failed", /unexpected response when reading repository/],
  ["repository response is a JSON string (EX-006)", { repo_json: "x" }, "provider-failed", /unexpected response when reading repository/],
  ["repository response is a JSON number (EX-006)", { repo_json: 5 }, "provider-failed", /unexpected response when reading repository/],
];
for (const [name, mode, code, pattern] of PREFLIGHT) {
  test(`preflight failure aborts before any creation and records nothing: ${name}`, () => {
    const d = project(); const stub = new Stub().use(); stub.mode(mode);
    try {
      const digest = digestOf(preview(d, "US-001"));
      const before = tree(d);
      const r = apply(d, digest, "US-001");
      assert.equal(r.code, 1);
      const errors = r.json.diagnostics.filter((x: any) => x.severity === "error");
      assert.deepEqual(errors.map((x: any) => x.code), [code]);
      assert.match(errors[0].message, pattern);
      assert.equal(r.json.result.mutations, 0);
      assert.equal(stub.creates().length, 0);
      assert.deepEqual(tree(d), before);
    } finally { stub.cleanup(); }
  });
}

const CREATION: [string, Record<string, unknown>, string, string][] = [
  ["permission/forbidden", { create_forbidden: true }, "provider-auth", "failed"],
  ["API failure (HTTP 502)", { fail_titles: ["[US-001]"] }, "provider-failed", "failed"],
  ["gh exits 0 without an Issue URL (ambiguous)", { nourl_titles: ["[US-001]"] }, "provider-ambiguous", "unconfirmed"],
];
for (const [name, mode, code, outcome] of CREATION) {
  test(`creation failure is reported per Story and never recorded as success: ${name}`, () => {
    const d = project(); const stub = new Stub().use(); stub.mode(mode);
    try {
      const digest = digestOf(preview(d, "US-001"));
      const before = tree(d);
      const r = apply(d, digest, "US-001");
      assert.equal(r.code, 1);
      assert.equal(r.json.result.outcomes[0].outcome, outcome);
      assert.ok(r.json.diagnostics.some((x: any) => x.code === code && x.severity === "error"));
      assert.equal(r.json.result.published, 0);
      assert.equal(r.json.result.mutations, 0);
      assert.deepEqual(tree(d), before);        // no Publication record, nothing else touched
    } finally { stub.cleanup(); }
  });
}

test("partial success is reported per Story; an ambiguous result stops the run without a blind retry", () => {
  const d = project(); const stub = new Stub().use();
  try {
    stub.mode({ fail_titles: ["[US-002]"] });
    let r = apply(d, digestOf(preview(d, "US-001", "US-002")), "US-001", "US-002");
    assert.deepEqual(r.json.result.outcomes.map((o: any) => [o.id, o.outcome]), [["US-001", "published"], ["US-002", "failed"]]);
    assert.equal(r.json.result.published, 1);
    assert.match(read(d, US1), /### PUB-1/);
    // an ambiguous result for the first Story: later Stories are not attempted
    const d2 = project(); stub.mode({ nourl_titles: ["[US-001]"] });
    r = apply(d2, digestOf(preview(d2, "US-001", "US-002")), "US-001", "US-002");
    assert.deepEqual(r.json.result.outcomes.map((o: any) => [o.id, o.outcome]), [["US-001", "unconfirmed"], ["US-002", "not-attempted"]]);
    assert.equal(stub.creates().length, 3);   // 2 in the first run (one failed) + exactly 1 here: no blind retry, no second Issue
  } finally { stub.cleanup(); }
});

test("a failure to record after a successful create is reported as an INCONSISTENCY and never retried", () => {
  const d = project(); const stub = new Stub().use();
  try {
    fs.mkdirSync(path.join(d, "Stories", ".US-001-export-report.md.sdlc-tmp"));   // the atomic-write temp path is occupied by a directory
    const r = apply(d, digestOf(preview(d, "US-001", "US-002")), "US-001", "US-002");
    assert.equal(r.code, 1);
    assert.deepEqual(r.json.result.outcomes.map((o: any) => [o.id, o.outcome]), [["US-001", "published-unrecorded"], ["US-002", "not-attempted"]]);
    const msg = r.json.diagnostics.find((x: any) => x.code === "record-failed").message as string;
    assert.match(msg, /^INCONSISTENCY: US-001 WAS published as https:\/\/github\.com\/acme\/widgets\/issues\/7 but recording it in Stories\/US-001-export-report\.md failed \(\[Errno 21\] Is a directory: '.*\.US-001-export-report\.md\.sdlc-tmp'\); do not publish this Story again/);
    assert.equal(stub.creates().length, 1);
  } finally { stub.cleanup(); }
});

// --- redaction ----------------------------------------------------------------------------------------------------------
test("redaction removes every token shape and provider diagnostics never carry a credential", () => {
  for (const secret of ["ghp_abcdefgh12345678", "gho_abcdefgh12345678", "ghs_abcdefgh12345678", "ghu_abcdefgh12345678", "ghr_abcdefgh12345678", "github_pat_11ABCDEFG0abcdefgh_12345", "Bearer abc.def-ghi"]) {
    const out = redact(`error with ${secret} inside`);
    assert.ok(!out.includes(secret.split(" ").pop()!) && out.includes("[redacted]"), secret);
  }
  assert.equal(redact("short ghp_abc is not a token"), "short ghp_abc is not a token");   // under 8 characters: not redacted (as in the oracle)
});

test("a token in provider output and in the environment never reaches stdout, stderr, the project or the call log", () => {
  const d = project(); const stub = new Stub().use(); stub.mode({ unauthenticated: true });
  process.env["GH_TOKEN"] = "ghp_" + "ENVSECRETTOKEN0123456789";
  try {
    const r = apply(d, digestOf(preview(d, "US-001")), "US-001");
    const everything = r.out + r.err + JSON.stringify(tree(d)) + JSON.stringify(stub.calls());
    assert.ok(!/gh[pousr]_[A-Za-z0-9]{8,}|github_pat_/.test(everything), "a token-shaped string leaked");
    assert.ok(r.out.includes("[redacted]"));      // the provider's own message contained one and was scrubbed
  } finally { delete process.env["GH_TOKEN"]; stub.cleanup(); }
});

test("sanity: the standard project validates cleanly enough to publish", () => {
  const d = project();
  assert.equal(cli(["validate"], d).code, 0);
  assert.ok(BASE_FILES[US1]);
});
