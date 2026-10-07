"""Stub `gh` for corpus replay (behaviourally identical to tests/unit/fakegh.py, which is what the corpus was recorded with).

A stub `gh` executable for deterministic tests of the GitHub provider boundary.

Behaviour is driven by `mode.json` in the directory named by FAKE_GH_STATE; every invocation (argv and stdin) is
appended to `calls.jsonl` there. It performs no network access and never needs a credential.
"""

import json
import os
import sys
from pathlib import Path

def main(argv):
    state = Path(os.environ["FAKE_GH_STATE"])
    mode = json.loads((state / "mode.json").read_text()) if (state / "mode.json").exists() else {}
    stdin = sys.stdin.read() if argv[:2] == ["issue", "create"] else None
    with (state / "calls.jsonl").open("a") as log:
        log.write(json.dumps({"argv": argv, "stdin": stdin}) + "\n")
    cmd = argv[:2]
    if cmd == ["auth", "status"]:
        if mode.get("unauthenticated"):
            print("You are not logged in to any GitHub hosts. Token " + "ghp_" + "SECRETSECRET123456" + " is invalid", file=sys.stderr)
            return 1
        return 0
    if cmd == ["repo", "view"]:
        if mode.get("repo_error"):
            print("HTTP 500: Internal Server Error", file=sys.stderr)
            return 1
        if mode.get("repo_bad_json"):
            print("this is not json")
            return 0
        if mode.get("repo_missing"):
            print("GraphQL: Could not resolve to a Repository with the name 'x/y'. (repository)", file=sys.stderr)
            return 1
        print(json.dumps({"nameWithOwner": argv[2], "hasIssuesEnabled": not mode.get("issues_disabled")}))
        return 0
    if cmd == ["issue", "create"]:
        title = argv[argv.index("--title") + 1]
        repo = argv[argv.index("--repo") + 1]
        if mode.get("create_forbidden"):
            print("HTTP 403: Forbidden (insufficient permission)", file=sys.stderr)
            return 1
        if any(t in title for t in mode.get("fail_titles", [])):
            print("HTTP 502: Bad Gateway", file=sys.stderr)
            return 1
        if any(t in title for t in mode.get("nourl_titles", [])):
            print("created")
            return 0
        counter = state / "counter"
        number = int(counter.read_text()) + 1 if counter.exists() else mode.get("first_issue", 7)
        counter.write_text(str(number))
        print(f"https://github.com/{repo}/issues/{number}")
        return 0
    print(f"fake gh: unsupported {argv}", file=sys.stderr)
    return 3
