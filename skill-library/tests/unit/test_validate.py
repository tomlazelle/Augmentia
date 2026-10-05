def add(sb, rel, id, **kw):
    return sb.doc(rel, id, **kw)


def errors(sb, data=None):
    data = data or sb.run("validate")[1]
    return {(d["code"], d["path"]) for d in data["diagnostics"] if d["severity"] == "error"}


def test_traced_fixture_is_clean_apart_from_notices(traced):
    code, data, _ = traced.run("validate")
    assert code == 0 and data["result"]["summary"]["error"] == 0


def test_broken_link_in_document(traced):
    path = traced.root / "PR" / "PR-001-product-overview.md"
    path.write_text(path.read_text() + "\nSee [gone](../BR/BR-099-gone.md).\n")
    code, data, _ = traced.run("validate")
    d = traced.diags(data, "broken-link")
    assert code == 1 and d[0]["path"] == "PR/PR-001-product-overview.md" and d[0]["line"] and "BR-099" in d[0]["message"]


def test_links_in_code_fences_and_external_links_are_ignored(traced):
    path = traced.root / "PR" / "PR-001-product-overview.md"
    path.write_text(path.read_text() + "\n```\n[x](nope.md)\n```\n[web](https://example.com/a) [mail](mailto:a@b.c) [top](#section)\n`[y](nope2.md)`\n")
    assert traced.run("validate")[0] == 0


def test_broken_link_in_handwritten_map_text(traced):
    path = traced.root / "BR" / "map.md"
    path.write_text(path.read_text().replace("- None yet.", "- See [plan](../Artifacts/plans/missing.md)"))
    assert ("broken-link", "BR/map.md") in errors(traced)


def test_deleted_document_gives_stale_map_not_extra_broken_link(traced):
    (traced.root / "Stories" / "US-001-register-user.md").unlink()
    _, data, _ = traced.run("validate")
    assert not traced.diags(data, "broken-link") and traced.diags(data, "stale-map")


def test_duplicate_ids_after_simulated_merge(traced):
    # Two branches each allocated BR-002 for different documents; merging leaves both files.
    add(traced, "BR/BR-002-from-branch-a.md", "BR-002", title="A", purpose="Branch A.")
    add(traced, "BR/BR-002-from-branch-b.md", "BR-002", title="B", purpose="Branch B.")
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    dups = traced.diags(data, "duplicate-id")
    assert code == 1 and {d["path"] for d in dups} == {"BR/BR-002-from-branch-a.md", "BR/BR-002-from-branch-b.md"}
    assert all(d["id"] == "BR-002" for d in dups)


def test_duplicate_front_matter_id_across_different_filenames(traced):
    add(traced, "BR/BR-002-a.md", "BR-002")
    add(traced, "BR/BR-003-b.md", "BR-003", fields={"id": "BR-002"})
    assert "duplicate-id" in {c for c, _ in errors(traced)}


def test_duplicate_requirement_ids(traced):
    path = traced.root / "BR" / "BR-001-business-overview.md"
    path.write_text(path.read_text() + "\n- **BR-001-R001** — declared twice\n")
    assert "duplicate-requirement" in {c for c, _ in errors(traced)}


def test_ledger_duplicate_and_bad_rows(traced):
    ledger = traced.root / ".sdlc" / "ledger.md"
    ledger.write_text(ledger.read_text() + "| BR-001 | document | Allocated | 2026-09-29 | |\n| ZZ-1 | x | y | z | |\n")
    _, data, _ = traced.run("validate")
    assert traced.diags(data, "duplicate-ledger-id") and traced.diags(data, "bad-ledger-row")


def test_retired_id_still_in_use(traced):
    traced.ok("retire-id", "BR-001")
    _, data, _ = traced.run("validate")
    assert traced.diags(data, "retired-id-in-use")


def test_retired_requirement_marked_retired_is_allowed_but_references_are_not(traced):
    path = traced.root / "PR" / "PR-001-product-overview.md"
    path.write_text(path.read_text().replace("Users can reset a password.", "*Retired* — Users can reset a password."))
    traced.ok("retire-id", "PR-001-R002", "--replaced-by", "PR-001-R001")
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    assert code == 0, data["diagnostics"]
    story = traced.root / "Stories" / "US-001-register-user.md"
    story.write_text(story.read_text().replace("covers: ['PR-001-R001']", "covers: ['PR-001-R002']"))
    code, data, _ = traced.run("validate")
    retired = traced.diags(data, "retired-reference")
    assert code == 1 and retired and "PR-001-R001" in retired[0]["message"]


def test_retired_requirement_still_declared_without_marker_is_error(traced):
    traced.ok("retire-id", "PR-001-R002")
    assert "retired-id-in-use" in {c for c, _ in errors(traced)}


def test_covers_unknown_requirement(traced):
    story = traced.root / "Stories" / "US-001-register-user.md"
    story.write_text(story.read_text().replace("PR-001-R001", "PR-001-R099"))
    _, data, _ = traced.run("validate")
    d = traced.diags(data, "covers-unknown")
    assert d and d[0]["id"] == "PR-001-R099"


def test_covers_without_source_link(traced):
    add(traced, "Stories/US-002-orphan.md", "US-002", title="Orphan", purpose="No link.", covers=["PR-001-R001"])
    traced.ok("update-map")
    _, data, _ = traced.run("validate")
    d = traced.diags(data, "covers-source-not-linked")
    assert d and d[0]["path"] == "Stories/US-002-orphan.md"


def test_unknown_requirement_in_reference_list(traced):
    path = traced.root / "PR" / "PR-001-product-overview.md"
    path.write_text(path.read_text().replace(
        "- [BR-001 — Business Overview](../BR/BR-001-business-overview.md)",
        "- [BR-001 — Business Overview](../BR/BR-001-business-overview.md) (BR-001-R042)"))
    assert "unknown-requirement" in {c for c, _ in errors(traced)}


def test_coverage_notices_do_not_change_exit_code(traced):
    add(traced, "Stories/US-002-standalone.md", "US-002", title="Standalone", purpose="No requirement.", covers=[])
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    notices = {(d["code"], d["id"]) for d in traced.diags(data, severity="notice")}
    assert code == 0
    assert ("story-no-coverage", "US-002") in notices
    assert ("requirement-uncovered", "PR-001-R002") in notices
    assert ("requirement-uncovered", "BR-001-R001") not in notices  # R1: only PR requirements
    assert ("requirement-uncovered", "PR-001-R001") not in notices
    assert data["result"]["summary"]["error"] == 0 and data["result"]["summary"]["notice"] == 2


def test_notices_are_reported_separately_from_errors_in_human_output(traced):
    add(traced, "Stories/US-002-standalone.md", "US-002", title="Standalone", purpose="No requirement.", covers=[])
    traced.ok("update-map")
    code, out, _ = traced.run("validate", json_out=False)
    assert code == 0 and "notice:" in out and "error:" not in out


def test_missing_required_directory_and_root_map(traced):
    import shutil
    shutil.rmtree(traced.root / "Stories")
    (traced.root / "map.md").unlink()
    got = errors(traced)
    assert ("missing-directory", "Stories") in got and ("missing-map", "map.md") in got


def test_ledger_warnings_are_not_errors(traced):
    traced.ok("allocate-id", "--category", "BR", "--title", "never written")
    add(traced, "BR/BR-009-imported.md", "BR-009")
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    assert code == 0
    assert {(d["code"], d["id"]) for d in traced.diags(data, severity="warning")} == {
        ("allocated-not-found", "BR-002"), ("not-in-ledger", "BR-009")}


def test_diagnostics_carry_path_id_reason_and_severity(traced):
    story = traced.root / "Stories" / "US-001-register-user.md"
    story.write_text(story.read_text().replace("PR-001-R001", "PR-001-R099"))
    _, data, _ = traced.run("validate")
    d = traced.diags(data, "covers-unknown")[0]
    assert d["severity"] == "error" and d["path"] == "Stories/US-001-register-user.md" and d["id"] == "PR-001-R099" and d["message"]
    _, out, _ = traced.run("validate", json_out=False)
    assert "Stories/US-001-register-user.md" in out and "PR-001-R099" in out and "error:" in out


def test_validate_reports_multiple_seeded_faults_together(traced):
    (traced.root / "PR" / "PR-001-product-overview.md").write_text("no front matter")
    add(traced, "BR/BR-002-a.md", "BR-002")
    add(traced, "BR/BR-002-b.md", "BR-002")
    codes = {c for c, _ in errors(traced)}
    assert {"bad-front-matter", "duplicate-id", "stale-map"} <= codes
