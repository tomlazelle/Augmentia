def read(sb, rel):
    return (sb.root / rel).read_text()


def test_map_rows_copy_metadata_verbatim(traced):
    text = read(traced, "PR/map.md")
    assert "| PR-001 | [Product Overview](PR-001-product-overview.md) | Core product expectations. | Draft |" in text


def test_story_map_shows_delivery_status(traced):
    text = read(traced, "Stories/map.md")
    assert "| ID | Document | Purpose | Status | Delivery |" in text
    assert "Let a visitor create an account." in text and "Not Started" in text


def test_relationships_derived_from_references(traced):
    assert "| [PR-001](PR-001-product-overview.md) | Derived From | [BR-001](../BR/BR-001-business-overview.md) |" in read(traced, "PR/map.md")
    assert "| [US-001](US-001-register-user.md) | Derived From | [PR-001](../PR/PR-001-product-overview.md) |" in read(traced, "Stories/map.md")


def test_regeneration_preserves_hand_written_text(traced):
    path = traced.root / "PR" / "map.md"
    text = path.read_text()
    path.write_text(text.replace("- None yet.", "- Is pricing in scope?").replace(
        "Product capabilities", "Hand edited intro. Product capabilities"))
    traced.doc("PR/PR-002-second.md", "PR-002", title="Second", purpose="Second doc.")
    traced.ok("update-map")
    new = path.read_text()
    assert "Is pricing in scope?" in new and "Hand edited intro." in new and "PR-002" in new


def test_update_map_is_idempotent(traced):
    before = traced.snapshot()
    data = traced.ok("update-map")
    assert data["result"]["updated"] == [] and traced.snapshot() == before


def test_staleness_detected_after_adding_and_editing_documents(traced):
    traced.doc("PR/PR-002-second.md", "PR-002", title="Second", purpose="Second doc.")
    code, data, _ = traced.run("validate")
    assert code == 1 and "PR/map.md" in {d["path"] for d in traced.diags(data, "stale-map")}
    traced.ok("update-map")
    assert traced.run("validate")[0] == 0
    path = traced.root / "PR" / "PR-002-second.md"
    path.write_text(path.read_text().replace("Second doc.", "Changed purpose."))
    code, data, _ = traced.run("validate")
    assert code == 1 and traced.diags(data, "stale-map")


def test_hand_tampering_inside_generated_region_is_stale(traced):
    path = traced.root / "BR" / "map.md"
    path.write_text(path.read_text().replace("Draft", "Approved"))
    code, data, _ = traced.run("validate")
    assert traced.diags(data, "stale-map")


def test_update_map_single_directory(traced):
    traced.doc("PR/PR-002-second.md", "PR-002", title="Second", purpose="Second doc.")
    traced.doc("BR/BR-002-second.md", "BR-002", title="Second", purpose="Second br.")
    data = traced.ok("update-map", "PR")
    assert data["result"]["updated"] == ["PR/map.md"]
    code, out, _ = traced.run("validate")
    assert {d["path"] for d in traced.diags(out, "stale-map")} == {"BR/map.md"}


def test_update_map_rejects_unmanaged_directory(traced):
    code, data, _ = traced.run("update-map", "nowhere")
    assert code == 2


def test_missing_markers_block_regeneration_and_fail_validation(traced):
    path = traced.root / "BR" / "map.md"
    path.write_text("# Business\n\nno markers here\n")
    code, data, _ = traced.run("update-map")
    assert code == 1 and traced.diags(data, "map-markers")
    assert path.read_text() == "# Business\n\nno markers here\n"
    assert traced.diags(traced.run("validate")[1], "map-markers")


def test_missing_map_reported_and_recreated(traced):
    (traced.root / "PR" / "map.md").unlink()
    _, data, _ = traced.run("validate")
    assert traced.diags(data, "missing-map")
    traced.ok("update-map")
    assert traced.run("validate")[0] == 0


def test_artifact_subdirectory_maps(traced):
    traced.ok("create-dir", "--artifact", "research")
    traced.ok("allocate-id", "--category", "RES", "--title", "Providers")
    traced.doc("Artifacts/research/RES-001-providers.md", "RES-001", title="Providers", purpose="OAuth providers compared.")
    traced.ok("update-map")
    assert "OAuth providers compared." in read(traced, "Artifacts/research/map.md")
    (traced.root / "Artifacts" / "research" / "map.md").unlink()
    assert traced.diags(traced.run("validate")[1], "missing-map")


def test_pipes_in_purpose_are_escaped(proj):
    proj.doc("BR/BR-001-x.md", "BR-001", purpose="Either A | B.")
    proj.ok("update-map")
    assert "Either A \\| B." in read(proj, "BR/map.md")
    assert proj.run("validate")[0] == 0


def test_documents_with_metadata_errors_are_left_out_of_maps(proj):
    proj.doc("BR/BR-001-x.md", "BR-001", fields={"status": "Bogus"})
    proj.ok("update-map")
    assert "BR-001" not in read(proj, "BR/map.md")
