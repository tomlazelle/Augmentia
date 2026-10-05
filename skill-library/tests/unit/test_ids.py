def alloc(sb, cat, title="Thing"):
    return sb.ok("allocate-id", "--category", cat, "--title", title)["result"]


def test_allocation_is_sequential_per_category(proj):
    assert alloc(proj, "BR")["id"] == "BR-001"
    assert alloc(proj, "BR")["id"] == "BR-002"
    assert alloc(proj, "PR")["id"] == "PR-001"
    assert alloc(proj, "US")["id"] == "US-001"
    for cat, first in (("DES", "DES-001"), ("PLAN", "PLAN-001"), ("RES", "RES-001"), ("TEST", "TEST-001")):
        assert alloc(proj, cat)["id"] == first


def test_allocate_returns_path_from_title(proj):
    r = alloc(proj, "US", "Register a New User!")
    assert r["path"] == "Stories/US-001-register-a-new-user.md"
    r = alloc(proj, "DES", "Auth")
    assert r["path"] == "Artifacts/design/DES-001-auth.md"
    r = proj.ok("allocate-id", "--category", "BR")["result"]
    assert r["path"] is None and r["directory"] == "BR"


def test_title_without_usable_characters_is_usage_error(proj):
    code, data, _ = proj.run("allocate-id", "--category", "BR", "--title", "!!!")
    assert code == 2


def test_deleting_highest_document_does_not_recycle_its_id(proj):
    alloc(proj, "BR")
    alloc(proj, "BR")
    path = proj.doc("BR/BR-002-thing.md", "BR-002")
    path.unlink()
    assert alloc(proj, "BR")["id"] == "BR-003"


def test_disk_documents_count_even_without_ledger(proj):
    proj.doc("BR/BR-007-imported.md", "BR-007")
    assert alloc(proj, "BR")["id"] == "BR-008"


def test_retire_document_then_allocate_never_reuses(proj):
    alloc(proj, "PR")
    alloc(proj, "PR")
    data = proj.ok("retire-id", "PR-002", "--note", "dropped")
    assert data["result"]["state"] == "Retired"
    assert alloc(proj, "PR")["id"] == "PR-003"
    assert "| PR-002 | document | Retired |" in (proj.root / ".sdlc" / "ledger.md").read_text()


def test_requirement_allocation_is_document_scoped_and_monotonic(proj):
    alloc(proj, "PR")
    alloc(proj, "PR")
    ids = [proj.ok("allocate-id", "--requirement", "PR-001")["result"]["id"] for _ in range(3)]
    assert ids == ["PR-001-R001", "PR-001-R002", "PR-001-R003"]
    assert proj.ok("allocate-id", "--requirement", "PR-002")["result"]["id"] == "PR-002-R001"


def test_requirement_ids_are_not_reused_after_retire_or_removal(proj):
    alloc(proj, "PR")
    proj.doc("PR/PR-001-thing.md", "PR-001", body="- **PR-001-R001** — one\n- **PR-001-R002** — two")
    assert proj.ok("allocate-id", "--requirement", "PR-001")["result"]["id"] == "PR-001-R003"
    proj.ok("retire-id", "PR-001-R003")
    assert proj.ok("allocate-id", "--requirement", "PR-001")["result"]["id"] == "PR-001-R004"


def test_requirement_allocation_needs_existing_document(proj):
    code, data, _ = proj.run("allocate-id", "--requirement", "PR-009")
    assert code == 1 and proj.diags(data, "unknown-id")
    alloc(proj, "PR")
    proj.ok("retire-id", "PR-001")
    code, data, _ = proj.run("allocate-id", "--requirement", "PR-001")
    assert code == 1 and proj.diags(data, "retired-id")
    code, _, _ = proj.run("allocate-id", "--requirement", "nonsense")
    assert code == 2


def test_retire_with_replacement_and_errors(proj):
    alloc(proj, "PR")
    alloc(proj, "PR")
    proj.ok("retire-id", "PR-001", "--replaced-by", "PR-002")
    ledger = (proj.root / ".sdlc" / "ledger.md").read_text()
    assert "Replaced by PR-002." in ledger
    code, data, _ = proj.run("retire-id", "PR-001")
    assert code == 1 and proj.diags(data, "already-retired")
    code, _, _ = proj.run("retire-id", "PR-002", "--replaced-by", "PR-002-R001")
    assert code == 2
    code, data, _ = proj.run("retire-id", "PR-099")
    assert code == 1 and proj.diags(data, "unknown-id")
    code, _, _ = proj.run("retire-id", "bad")
    assert code == 2


def test_retiring_document_that_still_exists_warns(proj):
    alloc(proj, "BR")
    proj.doc("BR/BR-001-thing.md", "BR-001")
    code, data, _ = proj.run("retire-id", "BR-001")
    assert code == 0 and proj.diags(data, "retired-still-present", "warning")


def test_ledger_notes_survive_pipes_and_roundtrip(proj):
    alloc(proj, "BR")
    proj.ok("retire-id", "BR-001", "--note", "a | b")
    proj.ok("allocate-id", "--category", "BR", "--title", "next")
    ledger = (proj.root / ".sdlc" / "ledger.md").read_text()
    assert "a \\| b" in ledger
    code, data, _ = proj.run("validate")
    assert not proj.diags(data, "bad-ledger-row")


def test_ledger_rows_sorted_and_stable(proj):
    alloc(proj, "PR")
    alloc(proj, "BR")
    rows = [l for l in (proj.root / ".sdlc" / "ledger.md").read_text().splitlines() if l.startswith("| BR") or l.startswith("| PR")]
    assert rows[0].startswith("| BR-001") and rows[1].startswith("| PR-001")


def test_corrupt_ledger_blocks_allocation(proj):
    (proj.root / ".sdlc" / "ledger.md").write_text("# nothing\n")
    code, data, _ = proj.run("allocate-id", "--category", "BR")
    assert code == 1
