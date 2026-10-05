"""Acceptance checks on projects produced by real Claude Code and Codex runs of the R2 technical Skills.

Fixtures (tests/fixtures/m4) are snapshots: a small Python library `textkit` with SDLC documents, code changes
and test evidence produced by the agents. Hand-authored inputs and fixture manipulations are listed in
docs/SDLC-M4-EVIDENCE.md. The checks below re-run the recorded tests and re-derive the validator's verdicts.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import Sandbox
from sdlc import frontmatter, technical

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "m4"
NAMES = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir() and p.name != "transcripts")
RUNS_RE = re.compile(r"### VR-\d+")


@pytest.fixture
def fx(tmp_path, capsys, monkeypatch):
    def open_(name):
        root = tmp_path / name
        shutil.copytree(FIXTURES / name, root)
        return Sandbox(root, capsys, monkeypatch)
    return open_


def meta(path):
    return frontmatter.parse(frontmatter.split(path.read_text())[0])


def story(sb, sid):
    return next(p for p in (sb.root / "Stories").glob(f"{sid}-*.md"))


def tdoc(sb, n=1):
    return next((sb.root / "Artifacts" / "tests").glob(f"TEST-{n:03d}-*.md"))


def runs(sb, n=1):
    text = tdoc(sb, n).read_text()
    recs, bad = technical.records(technical.sections(text), "Verification Runs", "VR")
    assert not bad
    return recs


def pytest_result(sb):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=sb.root, env=env,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout


@pytest.mark.parametrize("name", NAMES)
def test_every_fixture_validates_and_maps_are_current(name, fx):
    sb = fx(name)
    code, data, _ = sb.run("validate")
    assert code == 0 and data["result"]["summary"]["error"] == 0, data["diagnostics"]
    assert not sb.diags(data, "stale-map") and not sb.diags(data, "unexpected-directory")
    before = sb.snapshot()
    sb.ok("update-map")
    assert sb.snapshot() == before


@pytest.mark.parametrize("name", NAMES)
def test_only_permitted_terminal_states_and_evidence_backed_claims(name, fx):
    sb = fx(name)
    for path in (sb.root / "Stories").glob("US-*.md"):
        m = meta(path)
        if m["delivery_status"] in ("Implemented", "Verified"):
            assert "### IR-1" in path.read_text()  # an Implementation Record backs the claim
        assert "{{" not in path.read_text()
    for path in list((sb.root / "Artifacts").rglob("*.md")):
        assert "{{" not in path.read_text(), path
        assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", path.read_text()), f"personal email address in {path}"
        for line in re.findall(r"(?i)\*\*performed by:\*\* .*", path.read_text()):
            assert re.search(r"(?i)agent \(|a person", line) or "@" not in line, line


def test_full_chain_ready_to_verified_with_real_artifacts(fx):
    sb = fx("us001-chain-verified")
    s = story(sb, "US-001")
    assert meta(s)["delivery_status"] == "Verified" and meta(s)["covers"] == ["PR-001-R001"]
    des, plan, tst = (next((sb.root / "Artifacts" / d).glob(f"{p}-001-*.md")) for d, p in
                      (("design", "DES"), ("plans", "PLAN"), ("tests", "TEST")))
    for doc in (des, plan, tst):
        assert meta(doc)["status"] == "Draft"
        assert f"](../../Stories/{s.name})" in doc.read_text().split("### Related To")[0]  # Derived From links the Story
        assert "PR-001-R001" in doc.read_text().split("### Related To")[0]
    assert f"(../design/{des.name})" in plan.read_text() and f"(../plans/{plan.name})" in tst.read_text()  # Related To chain
    recs = runs(sb)
    assert [r.fields["result"] for r in recs] == ["passed", "passed"]
    assert all(r.fields["exit code"] == "0" and r.fields["command"] and r.fields["environment"] and r.fields["observed"] for r in recs)
    assert all(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", r.stamp) for r in recs)
    for r in recs:  # evidence logs exist and contain the recorded outcome
        log = sb.root / "Artifacts" / "tests" / re.search(r"\((evidence/[^)]+)\)", r.fields["observed"]).group(1)
        assert log.read_text().strip()
    code, out = pytest_result(sb)
    assert code == 0 and "9 passed" in out  # the recorded result reproduces


def cited_paths(doc):
    m = re.search(r"### Inspected\n(.*?)\n### Not Inspected", doc, re.S) or re.search(r"\*\*Inspected:\*\*(.*?)\n- \*\*", doc, re.S)
    assert m, "no Inspected list"
    return re.findall(r"`([\w./-]+\.\w+)`", m.group(1))


def test_technical_proposals_cite_files_that_were_actually_inspected(fx):
    sb = fx("us001-chain-verified")
    for folder, prefix in (("design", "DES"), ("plans", "PLAN")):
        doc = next((sb.root / "Artifacts" / folder).glob(f"{prefix}-001-*.md")).read_text()
        cited = cited_paths(doc)
        assert "textkit/text.py" in cited and "tests/test_text.py" in cited, folder
        for c in cited:
            assert (sb.root / c).exists(), f"{prefix} cites {c} which does not exist"
        assert "### Not Inspected or Unavailable" in doc
    codex = fx("us002-codex-standalone")
    doc = next((codex.root / "Artifacts" / "tests").glob("TEST-001-*.md")).read_text()
    cited = cited_paths(doc)
    assert "tests/test_text.py" in cited and all((codex.root / c).exists() for c in cited)
    assert "Not inspected" in doc
    assert "slugify" in (sb.root / "textkit" / "text.py").read_text()
    ir = story(sb, "US-001").read_text().split("## Implementation Record")[1]
    files = re.search(r"\*\*Files changed:\*\* (.*)", ir).group(1)
    for f in re.findall(r"`([^`]+)`", files):
        assert (sb.root / f).exists()


def test_refinement_improved_an_ambiguous_story_without_inventing(fx):
    sb = fx("us001-refined-ready")
    m = meta(story(sb, "US-001"))
    text = story(sb, "US-001").read_text()
    assert m["delivery_status"] == "Ready" and m["covers"] == ["PR-001-R001"] and m["status"] == "Draft"
    crit = text.split("## Acceptance Criteria")[1].split("###")[0]
    assert len(re.findall(r"(?m)^\d+\. ", crit)) == 5
    assert all(re.search(r"(?i)given.*when.*then", line) for line in re.findall(r"(?m)^\d+\. .*", crit))
    tbd = text.split("### Unresolved Acceptance Behavior (TBD)")[1].split("##")[0]
    assert "**TBD**" in tbd and re.search(r"(?i)accent|non-latin", tbd)
    assert not re.search(r"(?i)\bthen\b.*\bTBD\b", crit)  # undecided outcome is not an executable criterion
    assert "PR-001-R00" in text and "PR-001-R003" not in text  # no invented requirement IDs
    assert "### IR-" not in text  # refinement recorded no implementation


def test_failed_tests_do_not_produce_verified(fx):
    sb = fx("us001-failed-verification")
    assert meta(story(sb, "US-001"))["delivery_status"] == "Implemented"
    (vr1,) = [r for r in runs(sb) if r.fields["criteria"] != "none"]
    assert vr1.fields["result"] == "failed" and vr1.fields["exit code"] == "1"
    code, out = pytest_result(sb)
    assert code == 1 and "3 failed" in out  # the failure is real and reproducible
    # a hand-forged Verified is caught by the validator
    path = story(sb, "US-001")
    path.write_text(path.read_text().replace("delivery_status: Implemented", "delivery_status: Verified"))
    code, data, _ = sb.run("validate")
    d = sb.diags(data, "verified-criteria-unproven")
    assert code == 1 and d and "AC-2" in d[0]["message"] and "failed" in d[0]["message"]


def test_unaccepted_tbd_keeps_story_implemented(fx):
    sb = fx("us001-tbd-not-accepted")
    assert meta(story(sb, "US-001"))["delivery_status"] == "Implemented"
    results = [r.fields["result"] for r in runs(sb)]
    assert "passed" in results and "blocked" in results
    blocked = next(r for r in runs(sb) if r.fields["result"] == "blocked")
    assert re.search(r"(?i)accent|non-latin|tbd", blocked.fields["observed"])
    assert "Unresolved Acceptance Behavior (TBD)" in story(sb, "US-001").read_text()


def test_blocked_and_not_run_checks_do_not_count(fx):
    sb = fx("us001-blocked-not-run")
    assert meta(story(sb, "US-001"))["delivery_status"] == "Implemented"
    by_result = {r.fields["result"]: r for r in runs(sb)}
    assert set(by_result) == {"passed", "blocked", "not-run"}
    assert by_result["blocked"].fields["criteria"] == "AC-2" and by_result["not-run"].fields["criteria"] == "AC-4"
    assert "127" in tdoc(sb).read_text()  # command-not-found exit status was recorded, not hidden
    assert by_result["not-run"].fields["kind"] == "manual"
    path = story(sb, "US-001")
    path.write_text(path.read_text().replace("delivery_status: Implemented", "delivery_status: Verified"))
    code, data, _ = sb.run("validate")
    msg = sb.diags(data, "verified-criteria-unproven")[0]["message"]
    assert code == 1 and "AC-2" in msg and "AC-4" in msg and "AC-1" not in msg


def test_material_rework_supersedes_old_evidence_and_reverifies(fx):
    sb = fx("us001-rework-reverified")
    s = story(sb, "US-001")
    m, text = meta(s), s.read_text()
    assert m["delivery_status"] == "Verified" and m["status"] == "In Review"  # approval reset, delivery re-earned
    assert len(re.findall(r"(?m)^\d+\. ", text.split("## Acceptance Criteria")[1].split("###")[0])) == 6
    assert "### IR-1" in text and "### IR-2" in text
    recs = {r.id: r for r in runs(sb)}
    assert technical.is_superseded(recs["VR-1"]) and technical.is_superseded(recs["VR-2"])
    assert recs["VR-1"].fields["result"] == "passed" and recs["VR-1"].fields["command"]  # old evidence intact and attributable
    assert not technical.is_superseded(recs["VR-3"]) and technical.criteria_of(recs["VR-3"]) == [1, 2, 3, 4, 5, 6]
    assert recs["VR-3"].stamp > recs["VR-1"].stamp
    code, data, _ = sb.run("validate")
    assert code == 0 and sb.diags(data, "verified-with-unresolved-tbd", "warning")
    pcode, out = pytest_result(sb)
    assert pcode == 0 and "10 passed" in out
    # if the old runs were current and the new one missing, Verified would not be supported
    tp = tdoc(sb)
    tp.write_text(re.sub(r"(?m)^- \*\*Criteria:\*\* AC-1, AC-2, AC-3, AC-4, AC-5, AC-6$", "- **Criteria:** AC-1, AC-2, AC-3, AC-4, AC-5", tp.read_text()))
    assert "AC-6 (no current run)" in sb.diags(sb.run("validate")[1], "verified-criteria-unproven")[0]["message"]


def test_independent_entry_without_brd_design_or_requirement(fx):
    sb = fx("us002-codex-standalone")
    m = meta(story(sb, "US-002"))
    assert m["delivery_status"] == "Verified" and m["covers"] == []
    assert not list((sb.root / "BR").glob("BR-*.md")) and not (sb.root / "Artifacts" / "design").exists()
    assert not (sb.root / "Artifacts" / "plans").exists()
    (rec,) = runs(sb)
    assert rec.fields["result"] == "passed" and rec.fields["performed by"].startswith("agent (Codex")
    data = sb.ok("validate")
    assert {(d["code"], d["id"]) for d in sb.diags(data, severity="notice")} >= {("story-no-coverage", "US-002")}
    code, out = pytest_result(sb)
    assert code == 0 and "12 passed" in out


def test_review_findings_reference_real_changed_code():
    text = (FIXTURES / "transcripts" / "a-review-codex.md").read_text()
    assert "textkit/text.py:17" in text and "PLAN-001:67" in text and "complete" in text
    assert "not verification" in text and "No code or documents changed" in text
    fixture = FIXTURES / "us001-chain-verified"
    assert (fixture / "textkit" / "text.py").read_text().split("\n")[16].strip().startswith("slug = re.sub")
    assert "Review Record" not in (fixture / "Stories" / "US-001-turn-a-title-into-a-url-slug.md").read_text()
    assert "Verified" not in text.split("### AGENT")[1].replace("only `verify-story` can set `Verified`", "")


def test_transcripts_exist_for_every_r2_skill_and_both_agents():
    names = {p.stem for p in (FIXTURES / "transcripts").glob("*.md")}
    assert {"a-refine", "a-design-codex", "a-plan", "a-testplan", "a-implement", "a-review-codex", "a-verify",
            "f1-failed-tests", "f2-tbd-not-accepted", "f3-blocked-not-run", "r1-rework", "c-us2-codex"} <= names
    text = "".join((FIXTURES / "transcripts" / f"{n}.md").read_text() for n in names)
    assert "claude -p" in text and "codex exec" in text


MATRIX = {  # skill -> {agent: transcript stem}; every R2 Skill was executed by both agents in a real session
    "refine-stories": {"claude": "a-refine", "codex": "v3-codex-refine"},
    "create-design": {"claude": "v2-claude-design", "codex": "a-design-codex"},
    "plan-implementation": {"claude": "a-plan", "codex": "v4-codex-plan"},
    "implement-story": {"claude": "a-implement", "codex": "c-us2-codex"},
    "review-implementation": {"claude": "v1-claude-review", "codex": "a-review-codex"},
    "create-test-plan": {"claude": "a-testplan", "codex": "c-us2-codex"},
    "verify-story": {"claude": "a-verify", "codex": "c-us2-codex"},
}


@pytest.mark.parametrize("skill", sorted(MATRIX))
def test_each_r2_skill_has_a_real_transcript_for_both_agents(skill):
    for agent, stem in MATRIX[skill].items():
        text = (FIXTURES / "transcripts" / f"{stem}.md").read_text()
        marker = "claude -p" if agent == "claude" else "codex exec"
        assert marker in text, (skill, agent)
        assert f"{skill}" in text or skill.replace("-", " ") in text.lower(), (skill, agent)


def test_review_transcripts_never_claim_verification():
    for stem in ("a-review-codex", "v1-claude-review"):
        text = (FIXTURES / "transcripts" / f"{stem}.md").read_text()
        assert re.search(r"not verification", text), stem
        assert "delivery_status: Verified" not in text.split("### AGENT")[1].replace("does not set or imply `delivery_status: Verified`", "")


def test_no_fixture_document_contains_an_email_address():
    pattern = re.compile(r"[\w.+-]+@[\w-]+\.[a-z]{2,}")
    for path in FIXTURES.rglob("*.md"):
        assert not pattern.search(path.read_text()), path
