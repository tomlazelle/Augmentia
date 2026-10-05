"""M6 release walkthrough: checks on the fresh `tasklog` repository produced by real Claude Code and Codex runs.

The fixture (tests/fixtures/m6/tasklog-e2e) is a snapshot of a repository created from scratch for M6 (not seeded
from an M1-M5 fixture), driven through the pipx-installed release candidate. Hand-authored inputs and manual
interventions are disclosed in the transcripts and docs/SDLC-M6-EVIDENCE.md.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import Sandbox
from sdlc import frontmatter, publication, technical

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "m6"
PROJECT = FIX / "tasklog-e2e"
TRANSCRIPTS = FIX / "transcripts"
RUNS = [json.loads(line) for line in (TRANSCRIPTS / "run-log.jsonl").read_text().splitlines()]


@pytest.fixture
def e2e(tmp_path, capsys, monkeypatch):
    root = tmp_path / "tasklog"
    shutil.copytree(PROJECT, root)
    return Sandbox(root, capsys, monkeypatch)


def meta(path):
    return frontmatter.parse(frontmatter.split(path.read_text())[0])


def only(root, pattern):
    (path,) = list(root.glob(pattern))
    return path


def test_fixture_validates_with_only_the_expected_tbd_warning(e2e):
    code, data, _ = e2e.run("validate")
    assert code == 0 and data["result"]["summary"] == {"error": 0, "warning": 1, "notice": 0}
    assert [d["code"] for d in data["diagnostics"] if d["severity"] == "warning"] == ["verified-with-unresolved-tbd"]
    before = e2e.snapshot()
    e2e.ok("update-map")
    assert e2e.snapshot() == before  # maps are current


def test_whole_chain_exists_with_proper_ids_locations_and_relationships(e2e):
    r = e2e.root
    files = {"BR-001": "BR", "PR-001": "PR", "US-001": "Stories", "DES-001": "Artifacts/design", "PLAN-001": "Artifacts/plans",
             "RES-001": "Artifacts/research", "TEST-001": "Artifacts/tests"}
    for doc_id, folder in files.items():
        path = only(r / folder, f"{doc_id}-*.md")
        assert meta(path)["id"] == doc_id and (path.parent / "map.md").read_text().count(doc_id) >= 1
    refs = {d["id"]: set() for d in map(lambda i: {"id": i}, files)}
    for doc_id in files:
        _, data, _ = e2e.run("references", doc_id)
        refs[doc_id] = {o["target"]["id"] for o in data["result"]["outgoing"] if o["target"]}
    assert "BR-001" in refs["PR-001"] and "PR-001" in refs["US-001"] and "US-001" in refs["DES-001"]
    assert "RES-001" in refs["DES-001"] | refs["PLAN-001"] | refs["TEST-001"] or "RES-001" in only(r / "Artifacts/design", "DES-001-*.md").read_text()
    assert {"PR-001-R001", "PR-001-R002", "PR-001-R003", "PR-001-R004"} == set(meta(only(r / "Stories", "US-001-*.md"))["covers"])


def test_live_agent_research_artifact_is_real_and_used(e2e):
    res = only(e2e.root / "Artifacts" / "research", "RES-001-*.md")
    text = res.read_text()
    m = meta(res)
    assert m["status"] == "Draft" and m["purpose"] and "## Question" in text and "## Findings" in text and "## Conclusion" in text
    assert "../../Stories/US-001-list-overdue-tasks.md" in text  # Derived From link
    assert re.search(r"TypeError|ValueError", text)  # observed stdlib behaviour recorded, not asserted from memory
    assert "RES-001" in only(e2e.root / "Artifacts" / "design", "DES-001-*.md").read_text()  # the design cites the research
    assert "RES-001" in (e2e.root / "Artifacts" / "research" / "map.md").read_text()


def test_story_reached_verified_only_through_the_recorded_evidence(e2e):
    story = only(e2e.root / "Stories", "US-001-*.md")
    secs = technical.sections(story.read_text())
    assert meta(story)["delivery_status"] == "Verified"
    assert technical.records(secs, "Implementation Record", "IR")[0]
    assert re.search(r"\*\*Verdict:\*\* complete", story.read_text())  # review recorded; it is not what set Verified
    test_doc = only(e2e.root / "Artifacts" / "tests", "TEST-001-*.md")
    runs, bad = technical.records(technical.sections(test_doc.read_text()), "Verification Runs", "VR")
    assert not bad and [(r.id, r.fields["result"], r.fields["exit code"]) for r in runs] == [("VR-1", "passed", "0")]
    assert technical.criteria_of(runs[0]) == list(range(1, 8))
    assert (e2e.root / "Artifacts" / "tests" / "evidence").is_dir() and any((e2e.root / "Artifacts" / "tests" / "evidence").iterdir())
    test_doc.write_text(test_doc.read_text().replace("- **Result:** passed", "- **Result:** failed"))  # tamper with the evidence
    code, data, _ = e2e.run("validate")
    assert code == 1 and e2e.diags(data, "verified-criteria-unproven")  # Verified is only valid while the evidence supports it


def test_implementation_is_a_real_change_whose_tests_pass_when_rerun(tmp_path):
    root = tmp_path / "code"
    shutil.copytree(PROJECT, root)
    store = (root / "tasklog" / "store.py").read_text()
    assert "def overdue_tasks" in store and "due_date" in store and "overdue_tasks" in (root / "tasklog" / "__init__.py").read_text()
    done = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=root, capture_output=True, text=True)
    assert done.returncode == 0 and "12 passed" in done.stdout, done.stdout


def test_status_reports_the_final_state_and_the_tbd_without_mutation(e2e):
    before = e2e.snapshot()
    code, data, _ = e2e.run("status")
    r = data["result"]
    assert code == 0 and e2e.snapshot() == before
    assert [i["id"] for i in r["delivery"]["Verified"]] == ["US-001"] and r["traceability"]["unresolved_tbd"] == ["US-001"]
    assert r["inventory"]["RES"]["total"] == 1 and r["inventory"]["US"]["by_status"]["Approved"] == 1
    assert [a["kind"] for a in r["attention"]] == ["unresolved-acceptance"]


def test_publish_preview_of_the_verified_story_is_faithful_and_makes_no_mutation(e2e):
    before = e2e.snapshot()
    code, data, _ = e2e.run("publish-preview", "US-001")
    s = data["result"]["stories"][0]
    assert code == 0 and data["result"]["repository"] == "acme/widgets" and s["action"] == "create" and data["result"]["mutations"] == 0
    assert "Unresolved Acceptance Behavior (TBD)" in s["issue_body"] and "Implementation Record" not in s["issue_body"]
    assert e2e.snapshot() == before and not list((e2e.root / "Stories").glob("*.tmp"))
    story = only(e2e.root / "Stories", "US-001-*.md")
    assert not publication.parse("x", "US-001", technical.sections(story.read_text()))[0]  # nothing was published live


def test_ledger_shows_no_id_was_allocated_by_the_overlap_run(e2e):
    ledger = (e2e.root / ".sdlc" / "ledger.md").read_text()
    assert "| US-001 |" in ledger and "| US-002 |" not in ledger
    assert not list((e2e.root / "Stories").glob("US-002-*"))


def test_project_instruction_files_use_the_installed_command(e2e):
    for name in ("AGENTS.md", "CLAUDE.md"):
        text = (e2e.root / name).read_text()
        assert "python -m sdlc" not in text and "sdlc validate" in text and "publish-stories" in text


# --- transcripts ----------------------------------------------------------------------------------

def run(name, index=-1):
    return [r for r in RUNS if r["name"] == name][index]


def test_overlap_transcript_shows_the_decision_before_allocation_by_a_real_codex_run():
    first = run("ov-1")
    assert first["agent"] == "codex" and first["fingerprint_before"] == first["fingerprint_after"]
    text = (TRANSCRIPTS / "02-contextual-overlap-codex.md").read_text()
    for marker in ("Conceptual overlaps (my judgement, not CLI-scored)", "revise", "relate", "create a new independent Story",
                   "I haven’t allocated an ID or changed any files", "ledger MD5", "HARNESS FAILURE"):
        assert marker in text, marker
    assert run("ov-2b")["agent"] == "codex" and run("ov-2")["rc"] != 0  # the failed attempt is disclosed, not hidden


def test_status_runs_in_both_agents_left_the_repository_untouched():
    for name, agent in (("st-1", "claude"), ("st-2", "codex"), ("st-3", "claude"), ("st-4", "codex")):
        r = run(name)
        assert r["agent"] == agent and r["rc"] == 0 and r["fingerprint_before"] == r["fingerprint_after"], name
    assert "BEFORE the TBD-detector fix" in (TRANSCRIPTS / "04-status.md").read_text()


def test_publish_confirmation_behaviour_in_both_agents_made_no_changes():
    for name, agent in (("pub-c1", "claude"), ("pub-c2", "claude"), ("pub-x1", "codex"), ("pub-x2", "codex")):
        r = run(name)
        assert r["agent"] == agent and r["rc"] == 0 and r["fingerprint_before"] == r["fingerprint_after"], name
    text = (TRANSCRIPTS / "06-publish-behaviour-stub.md").read_text()
    assert "No live GitHub Issue was created" in text and "explicit confirmation" in text.lower()


def test_both_agents_took_part_at_meaningful_points():
    agents = {}
    for r in RUNS:
        agents.setdefault(r["agent"], set()).add(r["name"])
    assert {"brd-1", "prd-1", "refine-1", "impl-2", "ver-1"} <= agents["claude"]
    assert {"us1-1", "ov-1", "des-1", "plan-1", "rev-1"} <= agents["codex"]


def test_project_instruction_transcripts_show_both_agents_respecting_governance():
    text = (TRANSCRIPTS / "05-project-instructions.md").read_text()
    assert "CLAUDE.md requires" in text and "I used `refine-stories` because the provided `AGENTS.md` requires it" in text
    assert "INCONCLUSIVE" in text  # the weak attempts are disclosed


def test_no_credentials_or_personal_emails_in_m6_fixtures():
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    for path in FIX.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="ignore")
            assert not re.search(r"ghp_|github_pat_|gho_|ghs_|Bearer ", text), path
            assert not [e for e in email.findall(text) if not e.endswith(("example.com", "e.com"))], path
            assert "tomlazelle" not in text and "gmail" not in text, path
