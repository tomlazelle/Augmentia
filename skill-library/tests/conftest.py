import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sdlc.cli import main  # noqa: E402


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch):
    monkeypatch.setenv("SDLC_TODAY", "2026-09-29")


class Sandbox:
    """An isolated temporary repository plus helpers to drive the CLI in-process."""

    def __init__(self, root: Path, capsys, monkeypatch):
        self.root = root
        self.capsys = capsys
        monkeypatch.chdir(root)

    def run(self, *args, json_out=True):
        argv = list(args) + (["--json"] if json_out else [])
        self.capsys.readouterr()
        code = main(argv)
        out = self.capsys.readouterr()
        return code, (json.loads(out.out) if json_out and out.out.strip() else out.out), out.err

    def ok(self, *args):
        code, data, _ = self.run(*args)
        assert code == 0, data
        return data

    def init(self):
        return self.ok("init", "--project-name", "Demo")

    def doc(self, rel, id, *, title="Sample", purpose="A sample purpose.", status="Draft", created="2026-09-01",
            updated="2026-09-01", extra=None, body="", covers=None, derived=(), related=(), fields=None):
        """Write an authored document. `fields` overrides front matter keys (None value drops the key)."""
        meta = {"id": id, "title": title, "purpose": purpose, "status": status, "created": created, "updated": updated}
        if id.startswith("US"):
            meta["delivery_status"] = "Not Started"
            meta["covers"] = covers if covers is not None else []
        meta.update(extra or {})
        meta.update(fields or {})
        head = "\n".join(f"{k}: {v!r}" if isinstance(v, list) else f"{k}: {v}" for k, v in meta.items() if v is not None)
        refs = ["## References", "", "### Derived From"] + ([f"- [{t}]({p})" for t, p in derived] or ["- None identified."])
        refs += ["", "### Related To"] + ([f"- [{t}]({p})" for t, p in related] or ["- None identified."])
        text = f"---\n{head}\n---\n\n# {id} — {title}\n\n{chr(10).join(refs)}\n\n## Content\n\n{body}\n"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def diags(self, data, code=None, severity=None):
        return [d for d in data["diagnostics"]
                if (code is None or d["code"] == code) and (severity is None or d["severity"] == severity)]

    def snapshot(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in sorted(self.root.rglob("*")) if p.is_file()}


@pytest.fixture
def sb(tmp_path, capsys, monkeypatch):
    return Sandbox(tmp_path, capsys, monkeypatch)


@pytest.fixture
def proj(sb):
    sb.init()
    return sb


@pytest.fixture
def traced(proj):
    """BR-001 with a requirement, PR-001 derived from it with two requirements, US-001 covering one; maps synced."""
    proj.ok("allocate-id", "--category", "BR", "--title", "Business Overview")
    proj.ok("allocate-id", "--requirement", "BR-001")
    proj.doc("BR/BR-001-business-overview.md", "BR-001", title="Business Overview", purpose="Why the business needs this.",
             body="- **BR-001-R001** — Reduce onboarding time.")
    proj.ok("allocate-id", "--category", "PR", "--title", "Product Overview")
    proj.ok("allocate-id", "--requirement", "PR-001")
    proj.ok("allocate-id", "--requirement", "PR-001")
    proj.doc("PR/PR-001-product-overview.md", "PR-001", title="Product Overview", purpose="Core product expectations.",
             derived=[("BR-001 — Business Overview", "../BR/BR-001-business-overview.md")],
             body="- **PR-001-R001** — Users can register.\n- **PR-001-R002** — Users can reset a password.")
    proj.ok("allocate-id", "--category", "US", "--title", "Register user")
    proj.doc("Stories/US-001-register-user.md", "US-001", title="Register user", purpose="Let a visitor create an account.",
             covers=["PR-001-R001"], derived=[("PR-001 — Product Overview", "../PR/PR-001-product-overview.md")])
    proj.ok("update-map")
    return proj
