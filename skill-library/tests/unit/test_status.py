"""R3 `status`: a read-only, structured project snapshot derived from current files."""

import shutil
from pathlib import Path

import pytest

from conftest import Sandbox

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "m4"
IR = ("\n\n## Implementation Record\n\n### IR-1 — 2026-09-29\n- **Summary:** Added the feature.\n"
      "- **Files changed:** `app/x.py`\n- **Ref:** working tree (uncommitted)\n- **Tests run:** `pytest -q` → exit 0 — 4 passed")


def add_story(sb, sid, delivery, *, status="Draft", tbd=0, ir=None, covers=None, derived=()):
    lines = ["## Acceptance Criteria", "", "1. **Given** a, **when** b, **then** c."]
    if tbd:
        lines += ["", "### Unresolved Acceptance Behavior (TBD)", "", "- **TBD** — open"]
    body = "\n".join(lines) + (IR if (ir if ir is not None else delivery in ("Implemented", "Verified")) else "")
    return sb.doc(f"Stories/{sid}-thing-{sid[-1]}.md", sid, title=f"Thing {sid[-1]}", purpose="A thing.", status=status,
                  body=body, covers=covers or [], derived=derived, fields={"delivery_status": delivery})


def add_test_run(sb, story, result, *, tid="TEST-001", n=1):
    sb.run("create-dir", "--artifact", "tests")
    fields = {"Story": story, "Kind": "automated", "Result": result, "Criteria": "AC-1", "Command": "`pytest -q`",
              "Exit code": "0" if result == "passed" else "1", "Environment": "Py", "Performed by": "agent (test)",
              "Observed": "obs"}
    block = f"### VR-{n} — 2026-09-29T10:00:00Z\n" + "\n".join(f"- **{k}:** {v}" for k, v in fields.items())
    sb.doc(f"Artifacts/tests/{tid}-plan.md", tid, title="Plan", purpose="Plan.", body="## Verification Runs\n\n" + block,
           derived=[(story, f"../../Stories/{story}-thing-{story[-1]}.md")])


def status(sb):
    code, data, _ = sb.run("status")
    assert code == 0, data
    return data["result"]


def kinds(r, kind):
    return [a for a in r["attention"] if a["kind"] == kind]


def test_empty_initialized_project_yields_a_useful_report(proj):
    r = status(proj)
    assert r["empty"] is True and r["health"]["ok"] is True and r["health"]["documents"] == 0
    assert set(r["inventory"]) == {"BR", "PR", "US", "DES", "PLAN", "RES", "TEST"}
    assert all(v["total"] == 0 for v in r["inventory"].values())
    assert all(items == [] for items in r["delivery"].values()) and set(r["delivery"]) == {
        "Not Started", "Ready", "In Progress", "Implemented", "Verified"}
    assert r["attention"] == []
    _, text, _ = proj.run("status", json_out=False)
    for heading in ("## Project health", "## Document inventory", "## Story delivery", "## Traceability", "## Needs attention"):
        assert heading in text
    assert "No documents yet" in text


def test_uninitialised_directory_is_a_usage_error(sb):
    code, data, _ = sb.run("status")
    assert code == 2 and sb.diags(data, "no-project")


def test_inventory_and_all_five_delivery_states_are_distinguished(traced):
    add_story(traced, "US-002", "Not Started")
    add_story(traced, "US-003", "Ready")
    add_story(traced, "US-004", "In Progress")
    add_story(traced, "US-005", "Implemented")
    add_story(traced, "US-006", "Verified")
    add_test_run(traced, "US-006", "passed")
    traced.ok("update-map")
    r = status(traced)
    inv = r["inventory"]
    assert inv["BR"]["by_status"]["Draft"] == 1 and inv["PR"]["total"] == 1 and inv["US"]["total"] == 6 and inv["TEST"]["total"] == 1
    assert inv["DES"]["total"] == 0
    ids = {state: [i["id"] for i in items] for state, items in r["delivery"].items()}
    assert ids == {"Not Started": ["US-001", "US-002"], "Ready": ["US-003"], "In Progress": ["US-004"],
                   "Implemented": ["US-005"], "Verified": ["US-006"]}
    assert r["health"]["ok"] is True


def test_document_status_is_counted_separately_from_delivery(traced):
    add_story(traced, "US-002", "Verified", status="Approved")
    add_test_run(traced, "US-002", "passed")
    traced.ok("update-map")
    r = status(traced)
    assert r["inventory"]["US"]["by_status"] == {"Draft": 1, "In Review": 0, "Approved": 1, "Superseded": 0}
    assert [i["id"] for i in r["delivery"]["Verified"]] == ["US-002"]


def test_coverage_gaps_are_notices_not_failures(traced):
    add_story(traced, "US-002", "Not Started")  # standalone
    traced.ok("update-map")
    code, data, _ = traced.run("status")
    r = data["result"]
    assert code == 0 and data["ok"] is True and r["health"]["ok"] is True
    assert r["traceability"]["uncovered_requirements"] == ["PR-001-R002"]
    assert r["traceability"]["standalone_stories"] == ["US-002"]
    assert r["health"]["summary"]["notice"] == 2 and r["health"]["errors"] == []
    assert not [a for a in r["attention"] if a["kind"] == "validation-error"]


def test_errors_stale_maps_and_broken_references_are_surfaced(traced):
    story = traced.root / "Stories" / "US-001-register-user.md"
    story.write_text(story.read_text() + "\n- [gone](nowhere.md)\n- needs PR-001-R404\n")
    (traced.root / "PR" / "PR-001-product-overview.md").write_text(
        (traced.root / "PR" / "PR-001-product-overview.md").read_text().replace("Core product expectations.", "Changed purpose."))
    code, data, _ = traced.run("status")
    r = data["result"]
    assert code == 0 and r["health"]["ok"] is False and r["health"]["summary"]["error"] >= 2
    assert "PR/map.md" in r["health"]["stale_maps"] or "map.md" in r["health"]["stale_maps"]
    msgs = " ".join(b["message"] for b in r["health"]["broken_references"])
    assert "nowhere.md" in msgs
    assert {a["kind"] for a in r["attention"]} >= {"validation-error"}
    assert r["attention"][0]["kind"] == "validation-error"  # errors come first
    _, text, _ = traced.run("status", json_out=False)
    assert "ERRORS" in text and "Stale or missing maps" in text and "Broken reference" in text


def test_next_actions_distinguish_ready_in_progress_awaiting_verification_and_verified(traced):
    add_story(traced, "US-002", "Ready")
    add_story(traced, "US-003", "In Progress")
    add_story(traced, "US-004", "Implemented")
    add_story(traced, "US-005", "Verified")
    add_test_run(traced, "US-005", "passed")
    traced.ok("update-map")
    r = status(traced)
    assert [a["id"] for a in kinds(r, "ready-to-implement")] == ["US-002"]
    assert [a["id"] for a in kinds(r, "in-progress")] == ["US-003"]
    assert [a["id"] for a in kinds(r, "awaiting-verification")] == ["US-004"]
    assert not any(a["id"] == "US-005" for a in r["attention"])  # Verified needs nothing
    assert "implement-story" in kinds(r, "ready-to-implement")[0]["message"] and "verify-story" in kinds(r, "awaiting-verification")[0]["message"]


@pytest.mark.parametrize("result", ["failed", "blocked", "not-run"])
def test_failed_blocked_or_unrun_verification_evidence_is_flagged(traced, result):
    add_story(traced, "US-002", "Implemented")
    add_test_run(traced, "US-002", result)
    traced.ok("update-map")
    r = status(traced)
    problem = kinds(r, "verification-problem")
    assert [a["id"] for a in problem] == ["US-002"] and f"VR-1 {result}" in problem[0]["message"]
    assert kinds(r, "awaiting-verification")  # still awaiting; it is not Verified
    assert r["attention"].index(problem[0]) < r["attention"].index(kinds(r, "awaiting-verification")[0])


def test_unresolved_tbd_and_in_review_documents_are_reported(traced):
    add_story(traced, "US-002", "Not Started", tbd=1)
    br = traced.root / "BR" / "BR-001-business-overview.md"
    br.write_text(br.read_text().replace("status: Draft", "status: In Review"))
    traced.ok("update-map")
    r = status(traced)
    assert r["traceability"]["unresolved_tbd"] == ["US-002"] and kinds(r, "unresolved-acceptance")[0]["id"] == "US-002"
    assert [a["id"] for a in kinds(r, "in-review")] == ["BR-001"] and r["inventory"]["BR"]["by_status"]["In Review"] == 1


def test_missing_optional_technical_artifacts_are_not_a_defect(traced):
    add_story(traced, "US-002", "Ready")
    traced.ok("update-map")
    r = status(traced)
    assert r["health"]["ok"] is True and r["health"]["errors"] == []
    assert [w for w in r["health"]["warnings"] if w["code"] != "not-in-ledger"] == []  # (helper stories skip allocate-id)
    assert all(r["inventory"][c]["total"] == 0 for c in ("DES", "PLAN", "RES", "TEST"))
    assert not any(w in a["message"] for a in r["attention"] for w in ("design", "plan", "research", "test plan"))


def test_status_never_mutates_the_repository(traced):
    add_story(traced, "US-002", "Implemented")
    traced.ok("update-map")
    (traced.root / "stray.txt").write_text("x")
    before = traced.snapshot()
    ledger = (traced.root / ".sdlc" / "ledger.md").stat().st_mtime_ns
    for _ in range(2):
        traced.run("status")
        traced.run("status", json_out=False)
    assert traced.snapshot() == before
    assert (traced.root / ".sdlc" / "ledger.md").stat().st_mtime_ns == ledger


def test_status_reflects_current_files_not_memory(traced):
    assert status(traced)["delivery"]["Ready"] == []
    story = traced.root / "Stories" / "US-001-register-user.md"
    story.write_text(story.read_text().replace("delivery_status: Not Started", "delivery_status: Ready"))
    r = status(traced)
    assert [i["id"] for i in r["delivery"]["Ready"]] == ["US-001"] and r["delivery"]["Not Started"] == []
    story.unlink()
    assert status(traced)["inventory"]["US"]["total"] == 0


def test_invalid_documents_are_counted_not_silently_dropped(traced):
    (traced.root / "Stories" / "US-002-broken.md").write_text("no front matter here\n")
    r = status(traced)
    assert r["inventory"]["US"]["invalid"] == 1 and r["health"]["ok"] is False


def test_real_fixture_snapshot(tmp_path, capsys, monkeypatch):
    root = tmp_path / "fx"
    shutil.copytree(FIXTURES / "us001-chain-verified", root)
    sb = Sandbox(root, capsys, monkeypatch)
    before = sb.snapshot()
    r = status(sb)
    assert [i["id"] for i in r["delivery"]["Verified"]] == ["US-001"] and [i["id"] for i in r["delivery"]["Ready"]] == ["US-002"]
    assert r["traceability"]["standalone_stories"] == ["US-002"] and r["traceability"]["unresolved_tbd"] == ["US-001"]
    assert sb.snapshot() == before


def test_unresolved_tbd_is_found_whether_its_heading_is_level_two_or_three(traced):
    """Regression (M6 defect 4): a real Codex-authored Story used `##` instead of the template's `###`, and status hid the TBD."""
    for level, sid in (("###", "US-002"), ("##", "US-003")):
        body = ("## Acceptance Criteria\n\n1. **Given** a, **when** b, **then** c.\n\n"
                f"{level} Unresolved Acceptance Behavior (TBD)\n\n- **TBD** — open question\n\n## Open Questions\n\n- Same question.")
        traced.doc(f"Stories/{sid}-tbd-{level.count('#')}.md", sid, title=f"Tbd {sid}", purpose="Has a TBD.", body=body,
                   fields={"delivery_status": "Ready"})
    traced.ok("update-map")
    r = status(traced)
    assert r["traceability"]["unresolved_tbd"] == ["US-002", "US-003"]
    assert [a["id"] for a in kinds(r, "unresolved-acceptance")] == ["US-002", "US-003"]
