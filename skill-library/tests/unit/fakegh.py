"""A stub `gh` executable for deterministic tests of the GitHub provider boundary.

Behaviour is driven by `mode.json` in the directory named by FAKE_GH_STATE; every invocation (argv and stdin) is
appended to `calls.jsonl` there. It performs no network access and never needs a credential.
"""

import json
import os
import sys
from pathlib import Path

SCRIPT = f"""#!{sys.executable}
import sys
sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})
import fakegh
sys.exit(fakegh.main(sys.argv[1:]))
"""


def main(argv):
    state = Path(os.environ["FAKE_GH_STATE"])
    mode = json.loads((state / "mode.json").read_text()) if (state / "mode.json").exists() else {}
    stdin = sys.stdin.read() if argv[:2] == ["issue", "create"] else None
    with (state / "calls.jsonl").open("a") as log:
        log.write(json.dumps({"argv": argv, "stdin": stdin}) + "\n")
    cmd = argv[:2]
    if cmd == ["auth", "status"]:
        if mode.get("unauthenticated"):
            print("You are not logged in to any GitHub hosts. Token ghp_SECRETSECRET123456 is invalid", file=sys.stderr)
            return 1
        return 0
    if cmd == ["repo", "view"]:
        if mode.get("repo_missing"):
            print("GraphQL: Could not resolve to a Repository with the name 'x/y'. (repository)", file=sys.stderr)
            return 1
        print(json.dumps({"nameWithOwner": argv[2], "hasIssuesEnabled": not mode.get("issues_disabled")}))
        return 0
    if cmd == ["issue", "create"]:
        title = argv[argv.index("--title") + 1]
        repo = argv[argv.index("--repo") + 1]
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
