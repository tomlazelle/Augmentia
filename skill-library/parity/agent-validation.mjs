#!/usr/bin/env node
// Layer D — real agents from the npm-installed package (no source checkout on PATH).
//   node parity/tools/agent-validation.mjs --tarball <file.tgz> --out <evidence dir> [--agent claude|codex]...
// Installs the tarball into a clean prefix, then for each agent: creates a throwaway git project, links the packaged
// Skills with the installed adapter, runs a reduced M6 lifecycle in separate headless sessions (init -> Story -> Ready ->
// test plan -> status -> validate -> publish PREVIEW with a stub gh), saves every transcript and checks the result with the
// installed `sdlc`. No GitHub Issue is created: the stub's call log must contain no `issue create`.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const arg = (name, many = false) => { const v = []; process.argv.forEach((a, i) => { if (a === name) v.push(process.argv[i + 1]); }); return many ? v : v[0]; };
const tarball = path.resolve(arg("--tarball"));
const out = path.resolve(arg("--out"));
const agents = arg("--agent", true).length ? arg("--agent", true) : ["claude", "codex"];
fs.mkdirSync(out, { recursive: true });

const work = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "sdlc-agents-")));
const prefix = path.join(work, "prefix");
fs.mkdirSync(prefix);
const sh = (cmd, args, opts = {}) => spawnSync(cmd, args, { encoding: "utf8", ...opts });
const inst = sh("npm", ["install", "--offline", "--no-audit", "--no-fund", "--prefix", prefix, tarball]);
if (inst.status !== 0) { console.error(inst.stderr); process.exit(1); }
const bin = path.join(prefix, "node_modules", ".bin");
const nodeDir = path.dirname(process.execPath);
const pkg = JSON.parse(fs.readFileSync(path.join(prefix, "node_modules", "@augmentia", "sdlc", "package.json"), "utf8"));

// stub gh: a wrapper outside any project, driven by the Node stub from the compiled tests (also used by the unit tests)
const stubDir = path.join(work, "stub");
fs.mkdirSync(path.join(stubDir, "state"), { recursive: true });
const stubJs = pathToFileURL(path.resolve(HERE, "..", "dist", "test", "stub-gh.js")).href;
fs.writeFileSync(path.join(stubDir, "gh"), `#!${process.execPath}\nimport(${JSON.stringify(stubJs)}).then((m) => { process.exitCode = m.stubMain(process.argv.slice(2)); });\n`, { mode: 0o755 });

const baseEnv = (project) => ({
  HOME: process.env.HOME, USER: process.env.USER, LANG: "C.UTF-8", TERM: "dumb",
  PATH: `${bin}:${nodeDir}:/usr/local/bin:/usr/bin:/bin`,   // the installed sdlc first; no source checkout, no pipx
  SDLC_GH_COMMAND: path.join(stubDir, "gh"), FAKE_GH_STATE: path.join(stubDir, "state"),
});

const TURNS = [
  ["01-init", "Use the sdlc-init skill: check whether this project is initialized, initialize it if it is not, and tell me what exists."],
  ["02-story", `Use the create-stories skill to create ONE standalone Story (no PRD, no BRD). I cannot answer questions interactively, so these are my complete answers; treat everything else as TBD and do not ask me anything. Title: "Export overdue tasks". As a developer using tasklog, I want to export the overdue tasks as CSV so that I can share them. Acceptance criteria (decided): 1. Given tasks past their due date, when I export, then each overdue task is one CSV row with title and due date. 2. Given no overdue tasks, when I export, then the CSV has only the header row. Unresolved (put under TBD, not as criteria): whether completed tasks are exported. Run the overlap check and the contextual overlap review as your Skill says (the project is new, so expect none), create the Story as a Draft, then update the map and validate. Do not set any delivery status.`],
  ["03-refine", "Use the refine-stories skill on US-001. I declare it Ready, and I explicitly accept that its one unresolved item (whether completed tasks are exported) stays as TBD while the Story is Ready; that is my decision, do not ask me again. Use only what is already in the Story; do not invent anything. Then update the map and validate."],
  ["04-test-plan", `Use the create-test-plan skill for US-001. There is no source code in this repository yet, so record that the repository was inspected and contains none, and plan the tests as proposals. My answers: unit-level tests for both decided criteria; no performance testing; assumption: tests will be written with the project's future test runner. Do not ask me anything. Create the document in Draft, then update the map and validate.`],
  ["05-status", "Use the sdlc-status skill and tell me where this project stands and what I should do next."],
  ["06-validate", "Use the sdlc-validate skill and report the result."],
  ["07-publish-preview", "Use the publish-stories skill for US-001. The target repository is already configured. Show me the preview only. I have NOT confirmed anything; do not publish."],
];

function runAgent(agent, project, name, prompt) {
  const env = baseEnv(project);
  const args = agent === "claude"
    ? ["-p", prompt, "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep,Skill", "--output-format", "text"]
    : ["exec", "--sandbox", "workspace-write", "--skip-git-repo-check", "-C", project, prompt];
  const t0 = Date.now();
  const r = sh(sh('sh', ['-c', `command -v ${agent}`]).stdout.trim(), args, { cwd: project, env, timeout: 15 * 60 * 1000, maxBuffer: 64 * 1024 * 1024 });
  const label = agent === "claude" ? "Claude Code (`claude -p`)" : "Codex (`codex exec --sandbox workspace-write`)";
  const scrub = (s) => s.split(project).join("<PROJECT>").split(work).join("<WORK>");
  fs.writeFileSync(path.join(out, `${agent}-${name}.md`), `# ${agent} — ${name}\n\n### USER\n\n${prompt}\n\n### AGENT (${label}; project skills linked by the installed \`sdlc-install-${agent === "claude" ? "claude-code" : "codex"}\`; exit ${r.status}, ${Math.round((Date.now() - t0) / 1000)} s)\n\n${scrub(r.stdout || "")}\n${r.stderr && agent === "claude" ? `\n### STDERR\n\n${scrub(r.stderr)}\n` : ""}`);
  return r.status;
}

const results = {};
for (const agent of agents) {
  const project = path.join(work, `project-${agent}`);
  fs.mkdirSync(project);
  const env = baseEnv(project);
  const run = (cmd, args) => sh(cmd, args, { cwd: project, env });
  run("git", ["init", "-q"]);
  const checks = [];
  const check = (name, ok, detail = "") => checks.push({ name, ok: Boolean(ok), detail });
  const adapter = run("sdlc-install-" + (agent === "claude" ? "claude-code" : "codex"), ["--scope", "project"]);
  check("adapter links 15 Skills", adapter.status === 0 && adapter.stdout.split("\n").filter((l) => l.startsWith("installed")).length === 15, adapter.stdout.slice(0, 200));
  const skillsDir = path.join(project, agent === "claude" ? ".claude" : ".agents", "skills");
  const linked = fs.readdirSync(skillsDir).map((n) => fs.realpathSync(path.join(skillsDir, n)));
  check("Skills resolve into the installed package, not the checkout", linked.every((p) => p.startsWith(fs.realpathSync(path.join(prefix, "node_modules", "@augmentia", "sdlc")) + path.sep)));
  check("sdlc init (before agents)", run("sdlc", ["init", "--project-name", "tasklog"]).status === 0);
  fs.writeFileSync(path.join(project, ".sdlc", "config.md"), fs.readFileSync(path.join(project, ".sdlc", "config.md"), "utf8").replace(/\n---\n\n#/, "\npublishing:\n  provider: github\n  repository: acme/widgets\n---\n\n#"));
  const exits = {};
  for (const [name, prompt] of TURNS) exits[name] = runAgent(agent, project, name, prompt);
  // independent verification with the installed CLI
  const v = run("sdlc", ["validate", "--json"]);
  const validate = JSON.parse(v.stdout || "{}");
  const stories = fs.existsSync(path.join(project, "Stories")) ? fs.readdirSync(path.join(project, "Stories")).filter((f) => f.startsWith("US-")) : [];
  const tests = fs.existsSync(path.join(project, "Artifacts", "tests")) ? fs.readdirSync(path.join(project, "Artifacts", "tests")).filter((f) => f.startsWith("TEST-")) : [];
  check("every agent turn exited 0", Object.values(exits).every((c) => c === 0), JSON.stringify(exits));
  check("one Story US-001 created", stories.length === 1 && stories[0].startsWith("US-001"), stories.join(","));
  const storyText = stories[0] ? fs.readFileSync(path.join(project, "Stories", stories[0]), "utf8") : "";
  check("Story is Ready, not approved/implemented/verified by the agent", /delivery_status: Ready/.test(storyText) && /status: (Draft|In Review)/.test(storyText), (storyText.match(/^(status|delivery_status): .*/gm) || []).join(" | "));
  check("Story keeps the unresolved behavior as TBD", /TBD/.test(storyText));
  check("a TEST-001 plan exists and links the Story", tests.length >= 1 && /US-001/.test(fs.readFileSync(path.join(project, "Artifacts", "tests", tests[0]), "utf8")), tests.join(","));
  check("sdlc validate: 0 errors", v.status === 0 && validate.result?.summary?.error === 0, v.stdout.slice(0, 200));
  const pv = run("sdlc", ["publish-preview", "US-001", "--json"]);
  const preview = JSON.parse(pv.stdout || "{}");
  check("publish-preview from the installed CLI yields a sha256 digest and CREATE for acme/widgets", pv.status === 0 && /^sha256:/.test(preview.result?.digest ?? "") && preview.result?.stories?.[0]?.action === "create" && preview.result?.repository === "acme/widgets");
  const calls = fs.existsSync(path.join(stubDir, "state", "calls.jsonl")) ? fs.readFileSync(path.join(stubDir, "state", "calls.jsonl"), "utf8") : "";
  check("stub gh saw no issue creation (nothing published)", !/issue.*create/.test(calls) && !/## Publication/.test(storyText), calls.slice(0, 200));
  const st = run("sdlc", ["status", "--json"]);
  check("sdlc status works", st.status === 0 && JSON.parse(st.stdout).ok === true);
  results[agent] = { checks, exits, stories, tests };
  fs.writeFileSync(path.join(out, `${agent}-final-tree.txt`), run("find", [".", "-path", "./.git", "-prune", "-o", "-path", "./.claude", "-prune", "-o", "-path", "./.agents", "-prune", "-o", "-type", "f", "-print"]).stdout.split("\n").sort().join("\n"));
  for (const f of [...stories.map((s) => ["Stories", s]), ...tests.map((s) => ["Artifacts/tests", s])]) fs.copyFileSync(path.join(project, f[0], f[1]), path.join(out, `${agent}-${f[1]}`));
}
const summary = { package: pkg.name + "@" + pkg.version, tarball: path.basename(tarball), node: process.version, npm: sh("npm", ["--version"]).stdout.trim(), claude: sh("claude", ["--version"]).stdout.trim(), codex: sh("codex", ["--version"]).stdout.trim(), results };
fs.writeFileSync(path.join(out, "summary.json"), JSON.stringify(summary, null, 2));
let ok = true;
for (const [agent, r] of Object.entries(results)) for (const c of r.checks) { console.log(`${c.ok ? "PASS" : "FAIL"}  [${agent}] ${c.name}${c.ok ? "" : "  -> " + c.detail}`); ok &&= c.ok; }
process.exit(ok ? 0 : 1);
