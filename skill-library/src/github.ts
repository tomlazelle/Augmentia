// GitHub Issues provider: the only code that talks to GitHub (via the `gh` CLI) (port of sdlc/github_provider.py).
//
// Authentication comes from the user's `gh` login or environment; nothing here reads, writes or logs a credential.
// The executable can be replaced with `SDLC_GH_COMMAND` (tests use a stub). Operations are deliberately narrow: check
// access (read-only) and create one Issue.
//
// PARITY-EXCEPTION-001 (approved): Python 1.0.0rc1 leaks an uncaught OS exception when `gh` exists but cannot be
// executed. Node normalises *every* failure to start the provider executable (missing, not executable, permission denied,
// a directory, a broken interpreter, any spawn error) to `provider-unavailable`.
// PARITY-EXCEPTION-006 (proposed, same principle): a repository-view response that is valid JSON but not an object crashes
// Python (`AttributeError`); Node reports `provider-failed` "unexpected response".

import { spawnSync } from "node:child_process";
import { WS, strip } from "./pyfmt.js";

export const TIMEOUT_SECONDS = 60;
const ISSUE_URL_RE = new RegExp(`https://[^${WS}/]+/([^${WS}/]+/[^${WS}/]+)/issues/([0-9]+)`);
const SECRET_RE = new RegExp(`(gh[pousr]_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}|Bearer[${WS}]+[^${WS}]+)`, "g");

export class ProviderError extends Error {
  constructor(public code: string, message: string) { super(message); }
}
export class AmbiguousResult extends ProviderError {}

export interface IssueRef { number: number; url: string | null }
export interface Provider {
  checkAccess(repository: string): void;
  createIssue(repository: string, title: string, body: string): IssueRef;
}

export const redact = (text: string): string => text.replace(SECRET_RE, "[redacted]");
const cut = (s: string, n: number): string => [...s].slice(0, n).join("");

export class GitHubCli implements Provider {
  readonly command: string;
  constructor(command?: string, private timeoutMs = TIMEOUT_SECONDS * 1000) {
    this.command = command || process.env["SDLC_GH_COMMAND"] || "gh";
  }

  private run(args: string[], stdin?: string): { status: number; stdout: string; stderr: string } {
    const done = spawnSync(this.command, args, { input: stdin, encoding: "utf8", timeout: this.timeoutMs, maxBuffer: 1 << 26 });
    if (done.error) {
      const code = (done.error as NodeJS.ErrnoException).code;
      if (code === "ETIMEDOUT") throw new ProviderError("provider-failed", `'${this.command} ${args[0]}' timed out after ${TIMEOUT_SECONDS}s`);
      if (code === "ENOENT") throw new ProviderError("provider-unavailable", `GitHub CLI '${this.command}' was not found; install gh and run 'gh auth login'`);
      // PARITY-EXCEPTION-001: any other failure to start the executable (EACCES, ENOEXEC, EISDIR, ENOTDIR, E2BIG, ...)
      throw new ProviderError("provider-unavailable", `GitHub CLI '${this.command}' could not be started (${code ?? done.error.message}); install gh and run 'gh auth login'`);
    }
    if (done.status === null) {
      // killed by a signal (for example the timeout's SIGTERM) without an error object
      throw new ProviderError("provider-failed", `'${this.command} ${args[0]}' timed out after ${TIMEOUT_SECONDS}s`);
    }
    return { status: done.status, stdout: done.stdout, stderr: done.stderr };
  }

  /** Read-only preflight: authenticated, repository reachable, Issues enabled. Throws ProviderError. */
  checkAccess(repository: string): void {
    const auth = this.run(["auth", "status"]);
    if (auth.status !== 0) {
      throw new ProviderError("provider-auth", `GitHub CLI is not authenticated; run 'gh auth login' (or set GH_TOKEN) — ${cut(redact(strip(auth.stderr) || strip(auth.stdout)), 200)}`);
    }
    const view = this.run(["repo", "view", repository, "--json", "nameWithOwner,hasIssuesEnabled"]);
    if (view.status !== 0) {
      const detail = redact(strip(view.stderr) || strip(view.stdout));
      if (/could not resolve|not found|404/i.test(detail)) throw new ProviderError("repository-not-found", `repository ${repository} was not found or is not accessible: ${cut(detail, 200)}`);
      throw new ProviderError("provider-failed", `could not read repository ${repository}: ${cut(detail, 200)}`);
    }
    let info: unknown;
    try { info = JSON.parse(view.stdout); }
    catch { throw new ProviderError("provider-failed", `unexpected response when reading repository ${repository}`); }
    if (info === null || typeof info !== "object" || Array.isArray(info)) {
      throw new ProviderError("provider-failed", `unexpected response when reading repository ${repository}`); // PARITY-EXCEPTION-006 (proposed)
    }
    if ((info as Record<string, unknown>)["hasIssuesEnabled"] === false) throw new ProviderError("issues-disabled", `Issues are disabled on ${repository}`);
  }

  createIssue(repository: string, title: string, body: string): IssueRef {
    const result = this.run(["issue", "create", "--repo", repository, "--title", title, "--body-file", "-"], body);
    if (result.status !== 0) {
      const detail = redact(strip(result.stderr) || strip(result.stdout));
      const code = /auth|401|403|permission|forbidden/i.test(detail) ? "provider-auth" : "provider-failed";
      throw new ProviderError(code, `gh issue create failed (exit ${result.status}): ${cut(detail, 300)}`);
    }
    const match = ISSUE_URL_RE.exec(result.stdout);
    if (!match) {
      throw new AmbiguousResult("provider-ambiguous", "gh exited 0 but did not return an Issue URL; check the repository's Issues before retrying to avoid a duplicate");
    }
    return { number: parseInt(match[2]!, 10), url: match[0] };
  }
}
