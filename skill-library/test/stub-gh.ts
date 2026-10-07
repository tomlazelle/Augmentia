// Node port of the stub `gh` the corpus was recorded with (tests/unit/fakegh.py / parity/tools/stub_gh.py).
// Behaviour is driven by `mode.json` in the directory named by FAKE_GH_STATE; every invocation (argv and stdin) is appended to
// `calls.jsonl` using Python's json.dumps formatting so the recorded call logs compare byte for byte. No network, no credentials.

import fs from "node:fs";
import path from "node:path";
import { pyJsonDumps } from "../src/pyfmt.js";

type Mode = Record<string, unknown>;

export function stubMain(argv: string[]): number {
  const state = process.env["FAKE_GH_STATE"]!;
  const modeFile = path.join(state, "mode.json");
  const mode: Mode = fs.existsSync(modeFile) ? (JSON.parse(fs.readFileSync(modeFile, "utf8")) as Mode) : {};
  const isCreate = argv[0] === "issue" && argv[1] === "create";
  const stdin = isCreate ? fs.readFileSync(0, "utf8") : null;
  fs.appendFileSync(path.join(state, "calls.jsonl"), pyJsonDumps({ argv, stdin }) + "\n");
  const err = (s: string) => fs.writeSync(2, s + "\n");
  const out = (s: string) => fs.writeSync(1, s + "\n");

  if (argv[0] === "auth" && argv[1] === "status") {
    if (mode["unauthenticated"]) {
      err("You are not logged in to any GitHub hosts. Token " + "ghp_" + "SECRETSECRET123456" + " is invalid");
      return 1;
    }
    return 0;
  }
  if (argv[0] === "repo" && argv[1] === "view") {
    if (mode["repo_error"]) { err("HTTP 500: Internal Server Error"); return 1; }
    if (mode["repo_bad_json"]) { out("this is not json"); return 0; }
    if (mode["repo_json"] !== undefined) { out(JSON.stringify(mode["repo_json"])); return 0; } // test hook: any JSON document
    if (mode["repo_missing"]) { err("GraphQL: Could not resolve to a Repository with the name 'x/y'. (repository)"); return 1; }
    out(JSON.stringify({ nameWithOwner: argv[2], hasIssuesEnabled: !mode["issues_disabled"] }));
    return 0;
  }
  if (isCreate) {
    const title = argv[argv.indexOf("--title") + 1]!;
    const repo = argv[argv.indexOf("--repo") + 1]!;
    if (mode["create_forbidden"]) { err("HTTP 403: Forbidden (insufficient permission)"); return 1; }
    if (((mode["fail_titles"] as string[] | undefined) ?? []).some((t) => title.includes(t))) { err("HTTP 502: Bad Gateway"); return 1; }
    if (((mode["nourl_titles"] as string[] | undefined) ?? []).some((t) => title.includes(t))) { out("created"); return 0; }
    const counter = path.join(state, "counter");
    const number = fs.existsSync(counter) ? parseInt(fs.readFileSync(counter, "utf8"), 10) + 1 : ((mode["first_issue"] as number | undefined) ?? 7);
    fs.writeFileSync(counter, String(number));
    out(`https://github.com/${repo}/issues/${number}`);
    return 0;
  }
  err(`fake gh: unsupported ${pyReprList(argv)}`);
  return 3;
}

const pyReprList = (a: string[]): string => "[" + a.map((x) => `'${x}'`).join(", ") + "]";
