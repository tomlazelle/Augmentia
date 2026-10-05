"""Deterministic CLI-level R2 scenarios: technical artifact IDs, links, maps and seeded faults."""

from test_skills import instantiate, instantiate_tech

LINK = "[US-001 — S](../../Stories/US-001-s.md) — serves PR-001-R001"


def seed(proj):
    proj.ok("allocate-id", "--category", "PR", "--title", "P")
    proj.ok("allocate-id", "--requirement", "PR-001")
    (proj.root / "PR" / "PR-001-p.md").write_text(instantiate("create-prd", "PR-001", "P"))
    proj.ok("allocate-id", "--category", "US", "--title", "S")
    (proj.root / "Stories" / "US-001-s.md").write_text(instantiate(
        "create-stories", "US-001", "S", covers="PR-001-R001", derived="[PR-001 — P](../PR/PR-001-p.md)"))


def add_artifact(proj, skill, cat, sub, title="Thing", template="template.md", link=LINK):
    proj.ok("create-dir", "--artifact", sub)
    new_id = proj.ok("allocate-id", "--category", cat, "--title", title)["result"]["id"]
    path = proj.root / "Artifacts" / sub / f"{new_id}-{title.lower().replace(' ', '-')}.md"
    path.write_text(instantiate_tech(skill, new_id, title, link, template))
    return new_id, path


def test_each_technical_category_has_its_own_monotonic_sequence(proj):
    seed(proj)
    ids = {cat: [add_artifact(proj, s, cat, sub, f"T{i}", t)[0] for i in range(2)]
           for s, cat, sub, t in (("create-design", "DES", "design", "template.md"), ("plan-implementation", "PLAN", "plans", "template.md"),
                                  ("create-test-plan", "TEST", "tests", "template.md"), ("create-design", "RES", "research", "research-template.md"))}
    assert ids == {"DES": ["DES-001", "DES-002"], "PLAN": ["PLAN-001", "PLAN-002"], "TEST": ["TEST-001", "TEST-002"],
                   "RES": ["RES-001", "RES-002"]}
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0, data["diagnostics"]
    proj.ok("retire-id", "PLAN-002")
    (proj.root / "Artifacts" / "plans" / "PLAN-002-t1.md").unlink()
    assert proj.ok("allocate-id", "--category", "PLAN", "--title", "Next")["result"]["id"] == "PLAN-003"


def test_update_map_is_a_no_op_on_current_technical_fixtures_and_maps_list_them(proj):
    seed(proj)
    for s, cat, sub in (("create-design", "DES", "design"), ("plan-implementation", "PLAN", "plans"), ("create-test-plan", "TEST", "tests")):
        add_artifact(proj, s, cat, sub)
    proj.ok("update-map")
    before = proj.snapshot()
    assert proj.ok("update-map")["result"]["updated"] == [] and proj.snapshot() == before
    text = (proj.root / "Artifacts" / "design" / "map.md").read_text()
    assert "DES-001" in text and "../../Stories/US-001-s.md" in text and "Derived From" in text


def test_seeded_broken_link_is_detected(proj):
    seed(proj)
    add_artifact(proj, "plan-implementation", "PLAN", "plans", link="[US-009 — Gone](../../Stories/US-009-gone.md)")
    proj.ok("update-map")
    d = proj.diags(proj.run("validate")[1], "broken-link")
    assert d and d[0]["path"].startswith("Artifacts/plans/PLAN-001") and "US-009" in d[0]["message"]


def test_seeded_duplicate_technical_ids_are_detected(proj):
    seed(proj)
    _, path = add_artifact(proj, "create-test-plan", "TEST", "tests")
    (proj.root / "Artifacts" / "tests" / "TEST-001-other.md").write_text(path.read_text())
    proj.ok("update-map")
    dups = proj.diags(proj.run("validate")[1], "duplicate-id")
    assert {d["path"] for d in dups} == {"Artifacts/tests/TEST-001-thing.md", "Artifacts/tests/TEST-001-other.md"}


def test_seeded_stale_technical_map_is_detected_and_repaired(proj):
    seed(proj)
    add_artifact(proj, "create-design", "DES", "design")
    proj.ok("update-map")
    add_artifact(proj, "create-design", "DES", "design", title="Second")
    _, data, _ = proj.run("validate")
    assert "Artifacts/design/map.md" in {d["path"] for d in proj.diags(data, "stale-map")}
    proj.ok("update-map")
    assert proj.run("validate")[0] == 0


def test_seeded_misplaced_and_malformed_technical_documents_are_detected(proj):
    seed(proj)
    _, path = add_artifact(proj, "plan-implementation", "PLAN", "plans")
    proj.ok("create-dir", "--artifact", "tests")
    (proj.root / "Artifacts" / "tests" / path.name).write_text(path.read_text())  # PLAN document in the tests folder
    (proj.root / "Artifacts" / "plans" / "PLAN-9-bad-name.md").write_text("---\nid: PLAN-9\n---\n")
    codes = {d["code"] for d in proj.run("validate")[1]["diagnostics"] if d["severity"] == "error"}
    assert {"wrong-directory", "duplicate-id", "bad-filename"} <= codes


def test_story_referencing_unknown_requirement_or_artifact_is_reported_through_artifacts_too(proj):
    seed(proj)
    add_artifact(proj, "create-design", "DES", "design", link="[US-001 — S](../../Stories/US-001-s.md) — serves PR-001-R042")
    proj.ok("update-map")
    assert proj.diags(proj.run("validate")[1], "unknown-requirement")


def test_references_and_overlap_work_for_technical_artifacts(proj):
    seed(proj)
    add_artifact(proj, "create-design", "DES", "design", title="Slug design")
    add_artifact(proj, "plan-implementation", "PLAN", "plans", title="Slug plan")
    inc = {(i["relationship"], i["source"]["id"]) for i in proj.ok("references", "US-001")["result"]["incoming"]}
    assert {("Derived From", "DES-001"), ("Derived From", "PLAN-001")} <= inc
    assert [d["id"] for d in proj.ok("list", "--category", "DES")["result"]["documents"]] == ["DES-001"]
    r = proj.ok("find-overlaps", "--category", "DES", "--title", "Slug design", "--covers", "US-001")["result"]
    assert r["candidates"][0]["id"] == "DES-001" and r["action"] == "ask-human"
    assert proj.ok("find-overlaps", "--category", "PLAN", "--title", "Unrelated database migration")["result"]["candidates"] == []


def test_delivery_status_values_remain_schema_checked(proj):
    seed(proj)
    path = proj.root / "Stories" / "US-001-s.md"
    path.write_text(path.read_text().replace("delivery_status: Not Started", "delivery_status: Done"))
    assert proj.diags(proj.run("validate")[1], "invalid-delivery-status")
