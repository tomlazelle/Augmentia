#!/usr/bin/env python3
"""Generate parity/digest-matrix.json from the PYTHON ORACLE: the confirmation digest of `publish-preview` for one base
project and a matrix of single changes. Each scenario declares whether the change is expected to alter the digest (a
material publication input) or not (intentionally excluded from publication input); the oracle's own results are checked
against those declarations before the file is written. A frozen M7 asset; Node must reproduce every digest exactly."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

LIB = Path(__file__).resolve().parents[2]

DOC = "---\nid: {id}\ntitle: {title}\npurpose: {purpose}\nstatus: {status}\ncreated: 2026-09-01\nupdated: {updated}\n{extra}---\n\n# {id} — {title}\n{body}"
BASE_FILES = {
    "BR/BR-001-business.md": DOC.format(id="BR-001", title="Business", purpose="Why.", status="Approved", updated="2026-09-01", extra="", body="\n- **BR-001-R001** — A business requirement.\n"),
    "PR/PR-001-product.md": DOC.format(id="PR-001", title="Product", purpose="What.", status="Approved", updated="2026-09-01", extra="",
        body="\n## References\n\n### Derived From\n- [BR-001](../BR/BR-001-business.md)\n\n## Requirements\n\n- **PR-001-R001** — First.\n- **PR-001-R002** — Second.\n"),
    "Stories/US-001-export-report.md": DOC.format(id="US-001", title="Export report", purpose="Let users export a weekly report.", status="Draft", updated="2026-09-01",
        extra="delivery_status: Not Started\ncovers: [PR-001-R001]\n",
        body="\n## References\n\n### Derived From\n- [PR-001](../PR/PR-001-product.md)\n\n## Story\n\nAs a user, I want to export a report, so that I can share it.\n\n## Acceptance Criteria\n\n1. **Given** data, **when** I export, **then** a file is produced.\n\n## Notes\n\nKeep it simple.\n"),
    "Stories/US-002-archive-old.md": DOC.format(id="US-002", title="Archive old", purpose="Archive stale items.", status="Draft", updated="2026-09-01",
        extra="delivery_status: Not Started\ncovers: []\n", body="\n## Acceptance Criteria\n\n1. **Given** stale items, **when** archiving runs, **then** they are archived.\n"),
}
PUB_OTHER = "\n## Publication\n\n### PUB-1 — 2026-09-30\n- **Provider:** github\n- **Repository:** org/elsewhere\n- **Issue:** #5\n"
PUB_SAME = "\n## Publication\n\n### PUB-1 — 2026-09-30\n- **Provider:** github\n- **Repository:** acme/widgets\n- **Issue:** #9\n- **URL:** https://github.com/acme/widgets/issues/9\n"
US1 = "Stories/US-001-export-report.md"

def rep(rel, old, new): return {"replace": [rel, old, new]}
def append(rel, text): return {"append": [rel, text]}

SCENARIOS = [
    # --- material publication inputs: the digest MUST change -------------------------------------------------------
    ("Story body: acceptance criterion text", "changes", [rep(US1, "a file is produced", "a CSV file is produced")], ["US-001"]),
    ("Story body: new section", "changes", [append(US1, "\n## Edge Cases\n\nEmpty data.\n")], ["US-001"]),
    ("Story body: unresolved TBD added", "changes", [append(US1, "\n### Unresolved Acceptance Behavior (TBD)\n\n- **TBD** — Large exports.\n")], ["US-001"]),
    ("Story title", "changes", [rep(US1, "title: Export report", "title: Export weekly report"), rep(US1, "# US-001 — Export report", "# US-001 — Export weekly report")], ["US-001"]),
    ("Story purpose (rendered in the Issue header)", "changes", [rep(US1, "Let users export a weekly report.", "Let users export a monthly report.")], ["US-001"]),
    ("Story covers (rendered in the Issue header)", "changes", [rep(US1, "covers: [PR-001-R001]", "covers: [PR-001-R001, PR-001-R002]")], ["US-001"]),
    ("Story references (Derived From IDs in the header)", "changes", [rep(US1, "- [PR-001](../PR/PR-001-product.md)\n", "- [PR-001](../PR/PR-001-product.md)\n- [BR-001](../BR/BR-001-business.md)\n")], ["US-001"]),
    ("Story body: relative link text", "changes", [rep(US1, "Keep it simple.", "Keep it simple, see [notes](../PR/PR-001-product.md).")], ["US-001"]),
    ("Target repository", "changes", [{"config_repository": "acme/other"}], ["US-001"]),
    ("Selection: second Story added", "changes", [], ["US-001", "US-002"]),
    ("Selection: different Story", "changes", [], ["US-002"]),
    ("Known publication in the target repository (action CREATE -> SKIP)", "changes", [append(US1, PUB_SAME)], ["US-001"]),
    ("Known publication: different Issue number", "changes", [append(US1, PUB_SAME.replace("#9", "#10").replace("/9", "/10"))], ["US-001"]),
    ("Second Story's body changes (two-Story selection)", "changes", [rep("Stories/US-002-archive-old.md", "they are archived", "they are archived nightly")], ["US-001", "US-002"]),
    # --- intentionally excluded from publication input: the digest must NOT change ---------------------------------
    ("Front matter `updated` date", "same", [rep(US1, "updated: 2026-09-01", "updated: 2026-10-05")], ["US-001"]),
    ("Document status Draft -> Approved (a warning only)", "same", [rep(US1, "status: Draft", "status: Approved")], ["US-001"]),
    ("delivery_status Not Started -> Ready", "same", [rep(US1, "delivery_status: Not Started", "delivery_status: Ready")], ["US-001"]),
    ("Implementation Record added (operational section)", "same", [rep(US1, "delivery_status: Not Started", "delivery_status: Implemented"), append(US1, "\n## Implementation Record\n\n### IR-1 — 2026-09-29\n- **Summary:** done\n- **Files changed:** `a.py`\n")], ["US-001"]),
    ("Review Record added (operational section)", "same", [append(US1, "\n## Review Record\n\n### RV-1 — 2026-09-29\n- **Verdict:** complete\n")], ["US-001"]),
    ("Publication record for a DIFFERENT repository (identity is Story + provider + repository)", "same", [append(US1, PUB_OTHER)], ["US-001"]),
    ("References section link text (same target)", "same", [rep(US1, "[PR-001](../PR/PR-001-product.md)", "[the product requirements](../PR/PR-001-product.md)")], ["US-001"]),
    ("Extra blank lines between paragraphs", "same", [rep(US1, "so that I can share it.\n", "so that I can share it.\n\n\n\n")], ["US-001"]),
    ("Trailing blank lines at the end of the file", "same", [append(US1, "\n\n\n")], ["US-001"]),
    ("Selection order and duplicates", "same", [], ["US-001", "US-002", "US-001"]),
    ("Unrelated Story (not selected) changes", "same", [rep("Stories/US-002-archive-old.md", "they are archived", "they are archived nightly")], ["US-001"]),
    ("Unrelated document changes", "same", [rep("BR/BR-001-business.md", "A business requirement.", "A reworded business requirement.")], ["US-001"]),
]


def build(tmp: Path, ops, config_repository="acme/widgets"):
    run(tmp, "init", "--project-name", "Matrix")
    for rel, text in BASE_FILES.items():
        (tmp / rel).write_text(text)
    cfg = tmp / ".sdlc" / "config.md"
    cfg.write_text(cfg.read_text().replace("\n---\n\n#", f"\npublishing:\n  provider: github\n  repository: {config_repository}\n---\n\n#", 1))
    for op in ops:
        if "replace" in op:
            rel, old, new = op["replace"]
            text = (tmp / rel).read_text()
            assert old in text, (rel, old)
            (tmp / rel).write_text(text.replace(old, new, 1))
        elif "append" in op:
            rel, text = op["append"]
            (tmp / rel).write_text((tmp / rel).read_text() + text)
        elif "config_repository" in op:
            cfg.write_text(cfg.read_text().replace(config_repository, op["config_repository"]))
    run(tmp, "update-map")


def run(cwd, *args):
    return subprocess.run([sys.executable, "-m", "sdlc", *args], cwd=cwd, capture_output=True, text=True, env={"PYTHONPATH": str(LIB), "SDLC_TODAY": "2026-09-29", "PATH": "/usr/bin:/bin"})


def preview_digest(ops, selection):
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        build(tmp, ops)
        done = run(tmp, "publish-preview", *selection, "--json")
        data = json.loads(done.stdout)
        assert done.returncode == 0, (done.stdout, done.stderr)
        return data["result"]["digest"], [s["action"] for s in data["result"]["stories"]]


def main() -> None:
    base_digest, _ = preview_digest([], ["US-001"])
    rows = []
    for name, expect, ops, selection in SCENARIOS:
        digest, actions = preview_digest(ops, selection)
        ref = ["US-001", "US-002"] if name.startswith("Second Story's body") or "Selection order" in name else ["US-001"]
        base = base_digest if ref == ["US-001"] else preview_digest([], ref)[0]
        changed = digest != base
        assert changed == (expect == "changes"), f"oracle disagrees with the declaration for {name!r}: changed={changed}"
        rows.append({"name": name, "expect": expect, "ops": ops, "selection": selection, "reference_selection": ref, "digest": digest, "reference_digest": base, "actions": actions})
    out = {"source": "python-1.0.0rc1", "base_files": BASE_FILES, "base_selection": ["US-001"], "base_digest": base_digest, "scenarios": rows}
    (LIB / "parity" / "digest-matrix.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"{len(rows)} scenarios: {sum(r['expect'] == 'changes' for r in rows)} must change the digest, {sum(r['expect'] == 'same' for r in rows)} must not")


if __name__ == "__main__":
    main()
