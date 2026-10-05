"""R2 validator rules: Implementation Records, Verification Runs and what `Verified` requires."""

import pytest


def story_body(criteria=2, tbd=0, ir=True, extra=""):
    lines = ["## Acceptance Criteria", ""]
    lines += [f"{i}. **Given** context {i}, **when** action, **then** observable {i}." for i in range(1, criteria + 1)]
    if tbd:
        lines += ["", "### Unresolved Acceptance Behavior (TBD)", ""] + [f"- **TBD** — open question {i}" for i in range(tbd)]
    if ir:
        lines += ["", "## Implementation Record", "", "### IR-1 — 2026-09-29", "- **Summary:** Added the feature.",
                  "- **Files changed:** `app/x.py`, `tests/test_x.py`", "- **Ref:** working tree (uncommitted)",
                  "- **Tests run:** `pytest -q` → exit 0 — 4 passed"]
    return "\n".join(lines) + extra


def run_block(n, story="US-001", result="passed", criteria="AC-1, AC-2", stamp="2026-09-29T10:00:00Z", kind="automated",
              exit_code=None, superseded=False, drop=(), **over):
    fields = {"Story": story, "Kind": kind, "Result": result, "Criteria": criteria,
              "Command": "`python -m pytest -q`", "Exit code": str(0 if result == "passed" else 1) if exit_code is None else str(exit_code),
              "Environment": "Python 3.11.16, Linux", "Performed by": "agent (test)", "Observed": "4 passed",
              "Evidence": "[log](evidence/run.log)"}
    if kind == "manual" or result in ("blocked", "not-run"):
        fields.pop("Command"), fields.pop("Exit code")
    if superseded:
        fields["Superseded"] = "yes — reworked"
    fields.update(over)
    body = "\n".join(f"- **{k}:** {v}" for k, v in fields.items() if k not in drop)
    return f"### VR-{n} — {stamp}\n{body}\n"


def add_story(sb, id="US-001", status="Verified", **kw):
    body = story_body(**kw)
    sb.doc(f"Stories/{id}-thing.md", id, title="Thing", purpose="Thing story.", body=body,
           fields={"delivery_status": status})


def add_test(sb, runs, id="TEST-001", n=1):
    sb.run("create-dir", "--artifact", "tests")
    (sb.root / "Artifacts" / "tests" / "evidence").mkdir(exist_ok=True)
    (sb.root / "Artifacts" / "tests" / "evidence" / "run.log").write_text("log")
    body = "## Verification Runs\n\n" + "\n".join(runs)
    sb.doc(f"Artifacts/tests/{id}-plan.md", id, title="Plan", purpose="Test plan.", body=body,
           derived=[("US-001", "../../Stories/US-001-thing.md")])


def check(sb):
    sb.ok("update-map")
    return sb.run("validate")


def codes(sb, data, severity="error"):
    return {d["code"] for d in data["diagnostics"] if d["severity"] == severity}


def test_fully_evidenced_verified_story_passes(proj):
    add_story(proj)
    add_test(proj, [run_block(1)])
    code, data, _ = check(proj)
    assert code == 0, data["diagnostics"]


def test_per_criterion_runs_combine(proj):
    add_story(proj)
    add_test(proj, [run_block(1, criteria="AC-1"), run_block(2, criteria="AC-2", stamp="2026-09-29T10:05:00Z")])
    assert check(proj)[0] == 0


def test_verified_needs_a_run_for_every_criterion(proj):
    add_story(proj)
    add_test(proj, [run_block(1, criteria="AC-1")])
    code, data, _ = check(proj)
    d = proj.diags(data, "verified-criteria-unproven")
    assert code == 1 and "AC-2 (no current run)" in d[0]["message"] and "AC-1" not in d[0]["message"]


def test_verified_without_any_evidence_is_an_error(proj):
    add_story(proj)
    code, data, _ = check(proj)
    assert code == 1 and "AC-1 (no current run)" in proj.diags(data, "verified-criteria-unproven")[0]["message"]


@pytest.mark.parametrize("result", ["failed", "blocked", "not-run"])
def test_non_passed_runs_never_prove_a_criterion(proj, result):
    add_story(proj)
    add_test(proj, [run_block(1, result=result)])
    code, data, _ = check(proj)
    msg = proj.diags(data, "verified-criteria-unproven")[0]["message"]
    assert code == 1 and f"is {result}" in msg


def test_latest_run_wins_and_superseded_runs_are_ignored(proj):
    add_story(proj)
    passed = run_block(1, stamp="2026-09-29T10:00:00Z")
    failed_later = run_block(2, result="failed", stamp="2026-09-29T11:00:00Z")
    add_test(proj, [passed, failed_later])
    code, data, _ = check(proj)
    assert code == 1 and "VR-2" in proj.diags(data, "verified-criteria-unproven")[0]["message"]
    add_test(proj, [passed, run_block(2, result="failed", stamp="2026-09-29T11:00:00Z", superseded=True)])
    assert check(proj)[0] == 0
    add_test(proj, [run_block(1, superseded=True)])  # only superseded evidence: stale
    code, data, _ = check(proj)
    assert code == 1 and proj.diags(data, "verified-criteria-unproven")


def test_runs_across_test_documents_are_ordered_by_timestamp(proj):
    add_story(proj)
    add_test(proj, [run_block(1, stamp="2026-09-29T10:00:00Z")], id="TEST-001")
    add_test(proj, [run_block(1, result="failed", stamp="2026-09-30T09:00:00Z")], id="TEST-002")
    code, data, _ = check(proj)
    assert code == 1
    assert "TEST-002" in proj.diags(data, "verified-criteria-unproven")[0]["message"]


def test_runs_for_other_stories_do_not_count(proj):
    add_story(proj)
    add_story(proj, id="US-002", status="Implemented")
    add_test(proj, [run_block(1, story="US-002")])
    assert check(proj)[0] == 1


def test_implemented_and_verified_require_an_implementation_record(proj):
    add_story(proj, status="Implemented", ir=False)
    code, data, _ = check(proj)
    assert code == 1 and proj.diags(data, "implementation-record-missing")
    add_story(proj, status="Implemented")  # record present, no runs needed for Implemented
    assert check(proj)[0] == 0
    add_story(proj, status="Verified", ir=False)
    add_test(proj, [run_block(1)])
    assert "implementation-record-missing" in codes(proj, check(proj)[1])


@pytest.mark.parametrize("status", ["Not Started", "Ready", "In Progress"])
def test_earlier_states_need_no_record_or_evidence(proj, status):
    add_story(proj, status=status, ir=False)
    code, data, _ = check(proj)
    assert code == 0, data["diagnostics"]


def test_returned_to_ready_keeps_old_records_without_error(proj):
    add_story(proj, status="Ready")  # old IR block remains after invalidation
    add_test(proj, [run_block(1, superseded=True)])
    assert check(proj)[0] == 0


def test_invalid_implementation_records(proj):
    body = story_body(ir=False) + "\n\n## Implementation Record\n\n### IR-1 — yesterday\n- **Summary:** x\n\n### Work\n- **Summary:** y\n"
    proj.doc("Stories/US-001-thing.md", "US-001", title="Thing", purpose="p.", body=body, fields={"delivery_status": "Implemented"})
    _, data, _ = check(proj)
    msgs = " | ".join(d["message"] for d in proj.diags(data, "implementation-record-invalid"))
    assert "date must be" in msgs and "Files Changed" in msgs and "heading must be" in msgs


@pytest.mark.parametrize("drop,code", [(("Result",), "verification-missing-field"), (("Environment",), "verification-missing-field"),
                                       (("Performed by",), "verification-missing-field"), (("Observed",), "verification-missing-field"),
                                       (("Command",), "verification-missing-field"), (("Exit code",), "verification-missing-field"),
                                       (("Criteria",), "verification-missing-field"), (("Story",), "verification-missing-field")])
def test_verification_run_required_fields(proj, drop, code):
    add_story(proj, status="Implemented")
    add_test(proj, [run_block(1, drop=drop)])
    _, data, _ = check(proj)
    assert code in codes(proj, data)


@pytest.mark.parametrize("over,code", [
    ({"Result": "success"}, "verification-bad-value"), ({"Kind": "magic"}, "verification-bad-value"),
    ({"Exit code": "0", "Result": "failed"}, "verification-inconsistent"),
    ({"Exit code": "2"}, "verification-inconsistent"), ({"Exit code": "zero"}, "verification-bad-value"),
    ({"Criteria": "AC-9"}, "verification-bad-criteria"), ({"Criteria": "first"}, "verification-bad-criteria"),
    ({"Story": "US-099"}, "verification-unknown-story")])
def test_verification_run_value_checks(proj, over, code):
    add_story(proj, status="Implemented")
    add_test(proj, [run_block(1, **over)])
    assert code in codes(proj, check(proj)[1])


def test_verification_headings_and_duplicates(proj):
    add_story(proj, status="Implemented")
    add_test(proj, [run_block(1), run_block(1), "### Run one\n- **Story:** US-001\n", run_block(3, stamp="last-tuesday")])
    _, data, _ = check(proj)
    assert len(proj.diags(data, "verification-bad-heading")) == 3


def test_manual_and_blocked_runs_do_not_need_command_or_exit_code(proj):
    add_story(proj, status="Implemented")
    add_test(proj, [run_block(1, kind="manual", **{"Performed by": "Jane Doe", "Observed": "screen shows the message"}),
                    run_block(2, result="blocked", **{"Observed": "docker unavailable"}),
                    run_block(3, result="not-run", **{"Observed": "not run: no browser"})])
    code, data, _ = check(proj)
    assert code == 0, data["diagnostics"]


def test_evidence_links_must_resolve_and_the_evidence_directory_is_allowed(proj):
    add_story(proj)
    add_test(proj, [run_block(1)])
    _, data, _ = check(proj)
    assert not proj.diags(data, "unexpected-directory") and not proj.diags(data, "broken-link")
    (proj.root / "Artifacts" / "tests" / "evidence" / "run.log").unlink()
    assert proj.diags(check(proj)[1], "broken-link")


def test_criteria_warnings(proj):
    add_story(proj, status="Ready", criteria=0, ir=False)
    code, data, _ = check(proj)
    assert code == 0 and proj.diags(data, "ready-without-criteria", "warning")
    add_story(proj, status="Verified", criteria=0)
    code, data, _ = check(proj)
    assert code == 1 and proj.diags(data, "verified-no-criteria")


def test_unresolved_tbd_on_verified_story_is_a_warning_not_an_error(proj):
    add_story(proj, tbd=2)
    add_test(proj, [run_block(1)])
    code, data, _ = check(proj)
    assert code == 0 and proj.diags(data, "verified-with-unresolved-tbd", "warning")


def test_criteria_count_ignores_unresolved_and_later_sections(proj):
    add_story(proj, status="Verified", criteria=1, tbd=3)
    add_test(proj, [run_block(1, criteria="AC-1")])
    assert check(proj)[0] == 0
    add_test(proj, [run_block(1, criteria="AC-2")])
    assert "verification-bad-criteria" in codes(proj, check(proj)[1])


def test_r1_documents_are_unaffected(traced):
    code, data, _ = traced.run("validate")
    assert code == 0 and not [d for d in data["diagnostics"] if d["severity"] != "notice"]


def test_supporting_runs_may_declare_no_criteria(proj):
    add_story(proj)
    add_test(proj, [run_block(1), run_block(2, criteria="none", stamp="2026-09-29T10:01:00Z")])
    code, data, _ = check(proj)
    assert code == 0, data["diagnostics"]
    add_test(proj, [run_block(1, criteria="none")])  # a run that proves nothing cannot support Verified
    assert "verified-criteria-unproven" in codes(proj, check(proj)[1])
