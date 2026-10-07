// Sensitivity check for the Node port: apply one deliberate behavior change at a time to a COPY of the compiled output and
// confirm the frozen-corpus replay reports differences. Usage: node scripts/mutation-check.mjs [--only SUBSTRING]
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const corpus = path.join(root, "parity", "corpus");
const only = process.argv.includes("--only") ? process.argv[process.argv.indexOf("--only") + 1] : "";

const PUB = "publish-preview,publish-apply", ST = "status", V = "validate", Q = "list,references,find-overlaps", I = "allocate-id,retire-id", MP = "init,update-map,create-dir";
const M = (name, file, old, neu, commands) => ({ name, file, old, neu, commands });
const MUTATIONS = [
  M("ids: ID zero-padding width", "ids.js", 'padStart(3, "0")', 'padStart(4, "0")', I),
  M("maps: empty-map sentence", "maps.js", '"_No documents yet._"', '"_No docs yet._"', MP),
  M("ledger: state string on allocation", "ledger.js", 'state: "Allocated"', 'state: "Allocatd"', I),
  M("validate: broken-link severity", "validate.js", 'new Diagnostic("error", "broken-link", `link target does not exist: ${href}`, doc.rel', 'new Diagnostic("warning", "broken-link", `link target does not exist: ${href}`, doc.rel', V),
  M("validate: exit code on errors", "validate.js", "counts.error ? 1 : 0", "counts.error ? 2 : 0", V),
  M("validate: warning/notice sort rank", "validate.js", "{ error: 0, warning: 1, notice: 2 }", "{ error: 0, warning: 2, notice: 1 }", V),
  M("validate: uncovered-requirement scope", "validate.js", 'ownerOf(rid).startsWith("PR-")', 'ownerOf(rid).startsWith("BR-")', V),
  M("validate: verified needs passed run", "validate.js", '.trim() !== "passed")', '.trim() === "passed")', V),
  M("validate: retired-reference hint", "validate.js", '`; replaced by ${repl}`', '`; replace by ${repl}`', V),
  M("validate: duplicate-id wording", "validate.js", "is also used by:", "is also in:", V),
  M("validate: not-in-ledger severity", "validate.js", 'new Diagnostic("warning", "not-in-ledger"', 'new Diagnostic("error", "not-in-ledger"', V),
  M("validate: TBD warning dropped", "validate.js", 'diags.push(new Diagnostic("warning", "verified-with-unresolved-tbd"', 'void (new Diagnostic("warning", "verified-with-unresolved-tbd"', V),
  M("technical: superseded detection", "technical.js", '.startsWith("yes")', '.startsWith("no")', V),
  M("technical: AC counting stops at subsections", "technical.js", 'stop = true; // subsections', 'stop = false; // subsections', V),
  M("publication: accepted providers", "publication.js", 'PROVIDERS = ["github"]', 'PROVIDERS = ["gitlab"]', V),
  M("query: overlap title weight", "query.js", "title: 0.5", "title: 0.6", Q),
  M("query: LIKELY threshold", "query.js", "const LIKELY = 0.75", "const LIKELY = 0.8", Q),
  M("query: plural stripping", "query.js", "word.length > 3 &&", "word.length > 4 &&", Q),
  M("query: list skips invalid documents silently", "query.js", '"skipped-invalid"', '"skipped-invalidd"', Q),
  M("query: replaced_by in references", "query.js", 'result["replaced_by"] = replacedBy(entry)', "", Q),
  M("query: score rounding (tie handling bypass)", "pyfmt.js", "if (!isExactTie(x, places))\n        return x.toFixed(places);", "return x.toFixed(places);", Q),
  M("project: config returned despite errors", "project.js", 'diags.some((d) => d.severity === "error") ? null : data', "data", V + ",init"),
  M("project: unknown-config-key severity", "project.js", '"warning", "unknown-config-key"', '"error", "unknown-config-key"', V + ",init"),
  M("frontmatter: ISO date normalisation", "frontmatter.js", "return value.iso();", "return String(value.year);", V + ",list"),
  M("init: instruction files overwritten (both guards)", "init.js", ["if (lexists(target))\n        return false;", 'flag: "wx"'], ["", 'flag: "w"'], "init"),
  M("cli: JSON envelope schema_version", "cli.js", "schema_version: JSON_SCHEMA_VERSION", "schema_version: JSON_SCHEMA_VERSION + 1", "list"),
  M("digest: canonical JSON separators", "pyfmt.js", "return JSON.stringify(sort(value));", "return JSON.stringify(sort(value), null, 1);", PUB),
  M("digest: key order (no sorting)", "pyfmt.js", "Object.keys(o).sort(cmpStr)", "Object.keys(o)", PUB),
  M("digest: hash algorithm", "publish.js", 'createHash("sha256")', 'createHash("sha1")', PUB),
  M("digest: body excluded from the digest", "publish.js", "body: s.issue_body, known", "body: null, known", PUB),
  M("digest: repository excluded from the digest", "publish.js", "{ provider, repository, stories:", "{ provider, stories:", PUB),
  M("apply: stale digest accepted", "publish.js", "confirmDigest !== pr.digest", "false", PUB),
  M("apply: missing-confirmation code", "publish.js", 'code = "confirmation-missing"', 'code = "preview-stale"', PUB),
  M("identity: any-repository publication blocks", "publish.js", "p.provider === config.provider && p.repository === config.repository", "true", PUB),
  M("identity: first (not latest) publication shown", "publish.js", "pubs[pubs.length - 1]", "pubs[0]", PUB),
  M("preview: other publications not disclosed", "publish.js", 'diags.push(new Diagnostic("notice", "published-elsewhere"', 'void (new Diagnostic("notice", "published-elsewhere"', PUB),
  M("preview: Issue header authority statement", "publish.js", "is authoritative; edits to this Issue", "is the authority; edits to this Issue", PUB),
  M("preview: operational sections published", "publish.js", 'const EXCLUDED_SECTIONS = ["references", "implementation record", "review record", "publication"]', 'const EXCLUDED_SECTIONS = ["references"]', PUB),
  M("record: PUB numbering", "publication.js", "Math.max(0, ...existing.map((r) => parseInt(r.id.split(\"-\")[1], 10))) + 1", "1", PUB),
  M("record: updated date not bumped", "publication.js", "next = bumpUpdated(next, date);", "", PUB),
  M("record: entry layout", "publication.js", "`- **Issue:** #${issueNumber}`", "`- **Issue:** ${issueNumber}`", PUB),
  M("apply: record written before provider success is known", "publish.js", "mutations++;", "mutations += 2;", PUB),
  M("provider: auth failure class", "github.js", '"provider-auth", `GitHub CLI is not authenticated', '"provider-failed", `GitHub CLI is not authenticated', PUB),
  M("provider: creation permission class", "github.js", "/auth|401|403|permission|forbidden/i", "/nothing-matches/i", PUB),
  M("provider: ambiguous result class", "github.js", '"provider-ambiguous"', '"provider-failed"', PUB),
  M("provider: redaction removed", "github.js", 'text.replace(SECRET_RE, "[redacted]")', "text", PUB),
  M("provider: spawn failure class (EX-001)", "github.js", '"provider-unavailable", `GitHub CLI \'${this.command}\' could not be started', '"provider-failed", `GitHub CLI \'${this.command}\' could not be started', PUB),
  M("provider: non-object response accepted (EX-006)", "github.js", 'info === null || typeof info !== "object" || Array.isArray(info)', "false", PUB),
  M("status: attention ordering", "status.js", '"awaiting-verification": 3, "in-progress": 4', '"awaiting-verification": 4, "in-progress": 3', ST),
  M("status: unresolved TBD detection", "status.js", "technical.unresolvedTbdBullets(technical.sections(st.text)) > 0", "false", ST),
  M("status: verification-problem results", '"status.js"'.replace(/"/g, ""), '["failed", "blocked", "not-run"]', '["failed"]', ST),
];

const results = [];
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-mut-"));
  try {
    for (const d of ["dist", "templates", "skills", "shared"]) fs.cpSync(path.join(root, d), path.join(tmp, d), { recursive: true });
    fs.cpSync(path.join(root, "bin"), path.join(tmp, "bin"), { recursive: true });
    fs.symlinkSync(path.join(root, "node_modules"), path.join(tmp, "node_modules"));
    fs.writeFileSync(path.join(tmp, "package.json"), fs.readFileSync(path.join(root, "package.json")));
    const control = spawnSync(process.execPath, ["--test", ...["yaml-expectations", "numeric-expectations", "overlap-tie", "ids-ascii", "ac-counting", "digest-matrix", "provider", "publish-semantics"].map((t) => path.join(tmp, "dist", "test", `${t}.test.js`))], { encoding: "utf8", env: { ...process.env, SDLC_PARITY_DIR: path.join(root, "parity") } });
    console.error(`control (unmutated copy): oracle-derived unit tests ${control.status === 0 ? "PASS" : "FAIL"}`);
    results.push({ mutation: "(control: unmutated copy)", detected: control.status !== 0, by: control.status === 0 ? "none (expected)" : "BROKEN CONTROL" });
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
}
for (const m of MUTATIONS.filter((x) => x.name.includes(only))) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-mut-"));
  try {
    for (const d of ["dist", "templates", "skills", "shared"]) fs.cpSync(path.join(root, d), path.join(tmp, d), { recursive: true });
    fs.cpSync(path.join(root, "bin"), path.join(tmp, "bin"), { recursive: true });
    fs.symlinkSync(path.join(root, "node_modules"), path.join(tmp, "node_modules"));
    fs.writeFileSync(path.join(tmp, "package.json"), fs.readFileSync(path.join(root, "package.json")));
    const file = path.join(tmp, "dist", "src", m.file);
    let text = fs.readFileSync(file, "utf8");
    const pairs = Array.isArray(m.old) ? m.old.map((o, i) => [o, m.neu[i]]) : [[m.old, m.neu]];
    if (pairs.some(([o]) => !text.includes(o))) { results.push({ mutation: m.name, status: "NOT-APPLIED" }); continue; }
    for (const [o, n] of pairs) text = text.replace(o, n);
    fs.writeFileSync(file, text);
    const done = spawnSync(process.execPath, [path.join(tmp, "dist", "test", "corpus-report.js"), "--commands", m.commands], { env: { ...process.env, SDLC_CORPUS_DIR: corpus }, encoding: "utf8", maxBuffer: 1 << 26 });
    const line = done.stdout.split("\n").find((l) => l.startsWith("passed")) ?? done.stdout.slice(-200);
    const failed = Number((/FAILED (\d+)/.exec(line) ?? [])[1] ?? -1);
    // secondary detectors: the oracle-derived unit tests (YAML, numerics/tokens, ASCII IDs, tie-score regression)
    const unit = spawnSync(process.execPath, ["--test", ...["yaml-expectations", "numeric-expectations", "overlap-tie", "ids-ascii", "ac-counting", "digest-matrix", "provider", "publish-semantics"].map((t) => path.join(tmp, "dist", "test", `${t}.test.js`))], { encoding: "utf8", maxBuffer: 1 << 26, env: { ...process.env, SDLC_PARITY_DIR: path.join(root, "parity") } });
    const unitFailed = unit.status !== 0;
    const detected = failed > 0 || unitFailed;
    results.push({ mutation: m.name, detected, by: failed > 0 ? "corpus replay" : unitFailed ? "oracle-derived unit tests" : "none", failing_cases: failed });
    console.error(`${detected ? "caught " : "MISSED "} ${m.name}  (${failed} corpus cases${unitFailed ? " + unit tests" : ""})`);
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
}
console.log(JSON.stringify(results, null, 2));
