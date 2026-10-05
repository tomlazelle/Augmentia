"""GitHub Issues provider: the only code that talks to GitHub (via the `gh` CLI).

Authentication comes from the user's `gh` login or environment (`GH_TOKEN`/`GITHUB_TOKEN`); nothing here reads,
writes or logs a credential. The executable can be replaced with `SDLC_GH_COMMAND` (tests use a stub script).
Operations are deliberately narrow: check access (read-only) and create one Issue. No labels, projects,
milestones, branches, PRs or edits.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass

TIMEOUT_SECONDS = 60
ISSUE_URL_RE = re.compile(r"https://[^\s/]+/([^\s/]+/[^\s/]+)/issues/(\d+)")
_SECRET_RE = re.compile(r"(gh[pousr]_[A-Za-z0-9]{8,}|github_pat_[A-Za-z0-9_]{8,}|Bearer\s+\S+)")


class ProviderError(Exception):
    """A provider operation failed. `code` becomes the diagnostic code; nothing was created."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class AmbiguousResult(ProviderError):
    """The provider may have created the Issue but did not say which. Never retry blindly."""


@dataclass(frozen=True)
class IssueRef:
    number: int
    url: str | None


def redact(text: str) -> str:
    return _SECRET_RE.sub("[redacted]", text)


class GitHubCli:
    def __init__(self, command: str | None = None):
        self.command = command or os.environ.get("SDLC_GH_COMMAND") or "gh"

    def _run(self, args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
        try:
            return subprocess.run([self.command, *args], input=stdin, capture_output=True, text=True,
                                  timeout=TIMEOUT_SECONDS, check=False)
        except FileNotFoundError:
            raise ProviderError("provider-unavailable",
                                f"GitHub CLI '{self.command}' was not found; install gh and run 'gh auth login'") from None
        except subprocess.TimeoutExpired:
            raise ProviderError("provider-failed", f"'{self.command} {args[0]}' timed out after {TIMEOUT_SECONDS}s") from None

    def check_access(self, repository: str) -> None:
        """Read-only preflight: authenticated, repository reachable, Issues enabled. Raises ProviderError."""
        auth = self._run(["auth", "status"])
        if auth.returncode != 0:
            raise ProviderError("provider-auth", "GitHub CLI is not authenticated; run 'gh auth login' "
                                f"(or set GH_TOKEN) — {redact(auth.stderr.strip() or auth.stdout.strip())[:200]}")
        view = self._run(["repo", "view", repository, "--json", "nameWithOwner,hasIssuesEnabled"])
        if view.returncode != 0:
            detail = redact(view.stderr.strip() or view.stdout.strip())
            if re.search(r"could not resolve|not found|404", detail, re.I):
                raise ProviderError("repository-not-found", f"repository {repository} was not found or is not accessible: {detail[:200]}")
            raise ProviderError("provider-failed", f"could not read repository {repository}: {detail[:200]}")
        try:
            info = json.loads(view.stdout)
        except ValueError:
            raise ProviderError("provider-failed", f"unexpected response when reading repository {repository}") from None
        if info.get("hasIssuesEnabled") is False:
            raise ProviderError("issues-disabled", f"Issues are disabled on {repository}")

    def create_issue(self, repository: str, title: str, body: str) -> IssueRef:
        result = self._run(["issue", "create", "--repo", repository, "--title", title, "--body-file", "-"], stdin=body)
        if result.returncode != 0:
            detail = redact(result.stderr.strip() or result.stdout.strip())
            code = "provider-auth" if re.search(r"auth|401|403|permission|forbidden", detail, re.I) else "provider-failed"
            raise ProviderError(code, f"gh issue create failed (exit {result.returncode}): {detail[:300]}")
        match = ISSUE_URL_RE.search(result.stdout)
        if not match:
            raise AmbiguousResult("provider-ambiguous",
                                  "gh exited 0 but did not return an Issue URL; check the repository's Issues before retrying "
                                  "to avoid a duplicate")
        return IssueRef(int(match.group(2)), match.group(0))
