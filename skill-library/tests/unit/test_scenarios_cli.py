"""Deterministic CLI halves of the M3 revision scenarios (what the Skills delegate to the CLI)."""


def test_overlap_is_visible_before_any_allocation(traced):
    before = traced.snapshot()
    r = traced.ok("find-overlaps", "--category", "PR", "--title", "Product overview")["result"]
    assert r["candidates"][0]["id"] == "PR-001" and r["action"] == "ask-human"
    assert traced.snapshot() == before  # nothing allocated or written while the human decides
    # user chooses "new": allocation then proceeds and continues the sequence
    assert traced.ok("allocate-id", "--category", "PR", "--title", "Product overview v2")["result"]["id"] == "PR-002"


def test_removed_requirement_tombstone_and_retired_reference_report(traced):
    traced.ok("retire-id", "PR-001-R001", "--note", "dropped by product")
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    ids = {(d["code"], d["id"]) for d in data["diagnostics"] if d["severity"] == "error"}
    assert code == 1 and ("retired-reference", "PR-001-R001") in ids
    assert ("retired-id-in-use", "PR-001-R001") in ids  # still declared unmarked in the PRD
    # Skill follow-up: mark the text Retired, repoint the Story
    prd = traced.root / "PR" / "PR-001-product-overview.md"
    prd.write_text(prd.read_text().replace("Users can register.", "*Retired* — Users can register."))
    story = traced.root / "Stories" / "US-001-register-user.md"
    story.write_text(story.read_text().replace("covers: ['PR-001-R001']", "covers: ['PR-001-R002']"))
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    assert code == 0, data["diagnostics"]
    assert traced.ok("allocate-id", "--requirement", "PR-001")["result"]["id"] == "PR-001-R003"


def test_requirement_move_follows_reconciliation(traced):
    traced.ok("allocate-id", "--category", "PR", "--title", "Second")
    new = traced.ok("allocate-id", "--requirement", "PR-002")["result"]["id"]
    assert new == "PR-002-R001"
    traced.ok("retire-id", "PR-001-R001", "--replaced-by", new)
    traced.doc("PR/PR-002-second.md", "PR-002", title="Second", purpose="Second doc.",
               body=f"- **{new}** — Users can register.")
    prd = traced.root / "PR" / "PR-001-product-overview.md"
    prd.write_text(prd.read_text().replace("- **PR-001-R001** — Users can register.", "- **PR-001-R001** — *Retired* (moved to PR-002-R001)."))
    story = traced.root / "Stories" / "US-001-register-user.md"
    text = story.read_text().replace("covers: ['PR-001-R001']", f"covers: ['{new}']")
    story.write_text(text.replace("(../PR/PR-001-product-overview.md)", "(../PR/PR-002-second.md)"))
    traced.ok("update-map")
    code, data, _ = traced.run("validate")
    assert code == 0, data["diagnostics"]
    # before repointing, the CLI names the replacement
    story.write_text(text.replace(new, "PR-001-R001"))
    _, data, _ = traced.run("validate")
    assert any(f"replaced by {new}" in d["message"] for d in data["diagnostics"] if d["code"] == "retired-reference")


def test_revision_keeps_document_id_and_updates_map(traced):
    prd = traced.root / "PR" / "PR-001-product-overview.md"
    prd.write_text(prd.read_text().replace("purpose: Core product expectations.", "purpose: Revised product expectations."))
    assert traced.diags(traced.run("validate")[1], "stale-map")
    traced.ok("update-map")
    assert "Revised product expectations." in (traced.root / "PR" / "map.md").read_text()
    assert traced.run("validate")[0] == 0
    assert traced.ok("allocate-id", "--category", "PR")["result"]["id"] == "PR-002"
