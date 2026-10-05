import pytest


def codes(sb, path_part=None):
    _, data, _ = sb.run("validate")
    return {d["code"] for d in data["diagnostics"] if path_part is None or (d["path"] or "").endswith(path_part)}, data


def test_valid_document_passes(proj):
    proj.doc("BR/BR-001-good.md", "BR-001", title="Good")
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0 and not proj.diags(data, severity="error")


@pytest.mark.parametrize("field", ["id", "title", "purpose", "status", "created", "updated"])
def test_missing_required_field_reported(proj, field):
    proj.doc("BR/BR-001-x.md", "BR-001", fields={field: None})
    c, data = codes(proj, "BR-001-x.md")
    assert "missing-field" in c
    assert any(field in d["message"] for d in proj.diags(data, "missing-field"))


@pytest.mark.parametrize("fields,code", [
    ({"status": "Done"}, "invalid-status"),
    ({"created": "09/29/2026"}, "invalid-date"),
    ({"updated": "'2026-13-45'"}, "invalid-date"),
    ({"updated": "2026-13-45"}, "bad-front-matter"),
    ({"id": "BR-002"}, "id-filename-mismatch"),
    ({"id": "nope"}, "invalid-id"),
    ({"purpose": '"line one\\nline two"'}, "invalid-purpose"),
])
def test_invalid_field_values_reported(proj, fields, code):
    proj.doc("BR/BR-001-x.md", "BR-001", fields=fields)
    c, _ = codes(proj)
    assert code in c


def test_unquoted_yaml_dates_are_accepted(proj):
    proj.doc("BR/BR-001-x.md", "BR-001", created="2026-09-01")
    c, _ = codes(proj, "BR-001-x.md")
    assert not c & {"invalid-date", "missing-field"}


def test_updated_before_created_is_warning_only(proj):
    proj.doc("BR/BR-001-x.md", "BR-001", created="2026-09-10", updated="2026-09-01")
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0 and proj.diags(data, "date-order", "warning")


def test_bad_or_missing_front_matter(proj):
    (proj.root / "BR" / "BR-001-nofm.md").write_text("# no front matter\n")
    (proj.root / "BR" / "BR-002-bad.md").write_text("---\nid: [unclosed\n---\n# x\n")
    (proj.root / "BR" / "BR-003-list.md").write_text("---\n- a\n- b\n---\n# x\n")
    _, data, _ = proj.run("validate")
    assert len(proj.diags(data, "bad-front-matter")) == 3


@pytest.mark.parametrize("name", ["notes.md", "BR-1-short.md", "BR-001-Bad_Case.md", "BR-001.md", "XX-001-a.md"])
def test_filename_must_follow_convention(proj, name):
    (proj.root / "BR" / name).write_text("---\nid: BR-001\n---\n")
    c, _ = codes(proj, name)
    assert "bad-filename" in c


def test_document_in_wrong_directory(proj):
    proj.doc("PR/BR-001-misplaced.md", "BR-001")
    c, _ = codes(proj)
    assert "wrong-directory" in c


def test_artifact_categories_live_in_their_subdirectories(proj):
    proj.ok("create-dir", "--artifact", "design")
    proj.doc("Artifacts/design/DES-001-auth.md", "DES-001", title="Auth")
    proj.doc("Artifacts/design/PLAN-001-wrong.md", "PLAN-001")
    proj.doc("Artifacts/DES-002-loose.md", "DES-002")
    proj.ok("update-map")
    _, data, _ = proj.run("validate")
    wrong = {d["path"] for d in proj.diags(data, "wrong-directory")}
    assert wrong == {"Artifacts/design/PLAN-001-wrong.md", "Artifacts/DES-002-loose.md"}


def test_unknown_artifacts_subdirectory_is_warning(proj):
    (proj.root / "Artifacts" / "misc").mkdir()
    code, data, _ = proj.run("validate")
    assert code == 0 and proj.diags(data, "unexpected-directory", "warning")


def test_story_requires_delivery_status_and_covers_key(proj):
    proj.doc("Stories/US-001-a.md", "US-001", fields={"delivery_status": None, "covers": None})
    c, _ = codes(proj)
    assert {"missing-field", "missing-covers"} <= c


def test_story_field_validation(proj):
    proj.doc("Stories/US-001-a.md", "US-001", fields={"delivery_status": "Finished", "covers": "'PR-001-R001'"})
    proj.doc("Stories/US-002-b.md", "US-002", fields={"covers": ["bogus"]})
    c, _ = codes(proj)
    assert {"invalid-delivery-status", "invalid-covers"} <= c


def test_story_may_have_empty_covers(proj):
    proj.doc("Stories/US-001-a.md", "US-001", covers=[])
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0


def test_malformed_requirement_declarations(proj):
    body = "\n".join([
        "- PR-001-R001 — not bold",
        "- **PR-001-R2** — bad number",
        "- **PR-001-R003** - hyphen instead of em dash",
        "- **PR-001-R004** —",
        "- **PR-001-R005** — fine",
    ])
    proj.doc("PR/PR-001-x.md", "PR-001", body=body)
    _, data, _ = proj.run("validate")
    bad = proj.diags(data, "malformed-requirement")
    assert [d["line"] for d in bad] and len(bad) == 4
    assert not any("R005" in d["message"] for d in bad)


def test_requirement_declared_in_wrong_document(proj):
    proj.doc("PR/PR-001-x.md", "PR-001", body="- **BR-001-R001** — belongs elsewhere")
    c, _ = codes(proj)
    assert "requirement-wrong-document" in c


def test_requirement_heading_form_and_code_fences_ignored(proj):
    body = "### **PR-001-R001** — heading form\n\n```\n- PR-001-R009 — inside a fence\n```\n"
    proj.doc("PR/PR-001-x.md", "PR-001", body=body)
    proj.ok("update-map")
    _, data, _ = proj.run("validate")
    assert not proj.diags(data, "malformed-requirement")
    assert any(d["id"] == "PR-001-R001" for d in data["diagnostics"] if d["code"] == "requirement-uncovered")
