import json


def test_list_filters_and_is_sorted(traced):
    traced.doc("PR/PR-002-approved.md", "PR-002", title="Approved one", status="Approved")
    data = traced.ok("list")["result"]
    assert [d["id"] for d in data["documents"]] == ["BR-001", "PR-001", "PR-002", "US-001"]
    assert data["count"] == 4
    assert [d["id"] for d in traced.ok("list", "--category", "PR")["result"]["documents"]] == ["PR-001", "PR-002"]
    assert [d["id"] for d in traced.ok("list", "--status", "Approved")["result"]["documents"]] == ["PR-002"]
    story = traced.ok("list", "--category", "US")["result"]["documents"][0]
    assert story["delivery_status"] == "Not Started" and story["path"] == "Stories/US-001-register-user.md"


def test_list_is_deterministic_and_human_readable(traced):
    a = traced.run("list")[1]
    b = traced.run("list")[1]
    assert a == b
    code, out, _ = traced.run("list", json_out=False)
    assert "BR-001" in out and "3 document(s)" in out


def test_list_skips_invalid_documents_with_warning(traced):
    (traced.root / "BR" / "BR-005-broken.md").write_text("---\nid: BR-005\n---\n")
    _, data, _ = traced.run("list")
    assert data["result"]["count"] == 3 and traced.diags(data, "skipped-invalid", "warning")


def test_references_for_document_outgoing_and_incoming(traced):
    r = traced.ok("references", "PR-001")["result"]
    assert r["kind"] == "document" and r["path"] == "PR/PR-001-product-overview.md"
    assert [(o["relationship"], o["target"]["id"]) for o in r["outgoing"] if o["target"]] == [("Derived From", "BR-001")]
    incoming = {(i["relationship"], i["source"]["id"]): i["requirements"] for i in r["incoming"]}
    assert incoming == {("Covers", "US-001"): ["PR-001-R001"], ("Derived From", "US-001"): []}
    incoming_br = traced.ok("references", "BR-001")["result"]["incoming"]
    assert [(i["relationship"], i["source"]["id"]) for i in incoming_br] == [("Derived From", "PR-001")]


def test_references_for_story_includes_covers(traced):
    r = traced.ok("references", "US-001")["result"]
    assert {"relationship": "Covers", "requirements": ["PR-001-R001"], "href": None, "target": None} in r["outgoing"]


def test_references_for_requirement(traced):
    r = traced.ok("references", "PR-001-R001")["result"]
    assert r["kind"] == "requirement" and r["defined_in"]["id"] == "PR-001"
    assert [(i["relationship"], i["source"]["id"]) for i in r["incoming"]] == [("Covers", "US-001")]
    assert traced.ok("references", "PR-001-R002")["result"]["incoming"] == []


def test_references_retired_and_unknown(traced):
    traced.ok("retire-id", "PR-001-R002", "--replaced-by", "PR-001-R001")
    r = traced.ok("references", "PR-001-R002")["result"]
    assert r["state"] == "Retired" and r["replaced_by"] == "PR-001-R001"
    code, data, _ = traced.run("references", "PR-777")
    assert code == 1 and traced.diags(data, "unknown-id")
    assert traced.run("references", "junk")[0] == 2


def test_references_human_output(traced):
    code, out, _ = traced.run("references", "PR-001", json_out=False)
    assert code == 0 and "outgoing:" in out and "incoming:" in out and "US-001" in out


def overlaps(sb, *args):
    return sb.ok("find-overlaps", *args)["result"]


def test_overlap_same_title_is_likely_even_with_different_case_and_plural(traced):
    r = overlaps(traced, "--category", "US", "--title", "register USERS!")
    assert r["action"] == "ask-human"
    c = r["candidates"][0]
    assert c["id"] == "US-001" and c["level"] == "likely" and "same normalized title" in c["reasons"]


def test_overlap_only_same_category(traced):
    r = overlaps(traced, "--category", "BR", "--title", "Register user")
    assert r["candidates"] == [] and r["action"] == "none"


def test_overlap_possible_from_partial_title_and_purpose(traced):
    r = overlaps(traced, "--category", "US", "--title", "Register new user account",
                 "--purpose", "Let a visitor create an account")
    c = r["candidates"][0]
    assert c["id"] == "US-001" and c["level"] in ("possible", "likely") and 0.4 <= c["score"] <= 1
    assert any(x.startswith("purpose similarity") for x in c["reasons"])


def test_overlap_uses_requirement_references(traced):
    traced.doc("Stories/US-002-signup-flow.md", "US-002", title="Signup flow", purpose="Onboarding path.",
               covers=["PR-001-R002"], derived=[("PR-001", "../PR/PR-001-product-overview.md")])
    unrelated = overlaps(traced, "--category", "US", "--title", "Signup flow", "--covers", "PR-001-R001")
    assert unrelated["candidates"][0]["id"] == "US-002"  # same title dominates
    r = overlaps(traced, "--category", "US", "--title", "Completely different wording", "--covers", "PR-001-R001")
    assert r["candidates"] == []  # a shared requirement alone is not enough
    r = overlaps(traced, "--category", "US", "--title", "Register person", "--purpose", "Let a visitor create an account",
                 "--covers", "PR-001-R001")
    assert r["candidates"][0]["id"] == "US-001" and any("shares references" in x for x in r["candidates"][0]["reasons"])


def test_overlap_source_document_ids_match_derived_from(traced):
    r = overlaps(traced, "--category", "PR", "--title", "Product overview", "--covers", "BR-001")
    assert r["candidates"][0]["id"] == "PR-001"
    assert "shares references: BR-001" in r["candidates"][0]["reasons"]


def test_overlap_ignores_superseded_and_never_writes(traced):
    traced.doc("PR/PR-002-old.md", "PR-002", title="Product Overview", status="Superseded")
    before = traced.snapshot()
    r = overlaps(traced, "--category", "PR", "--title", "Product overview")
    assert [c["id"] for c in r["candidates"]] == ["PR-001"]
    assert traced.snapshot() == before


def test_overlap_output_is_deterministic_and_documented_shape(traced):
    args = ("--category", "US", "--title", "Register user")
    assert traced.run("find-overlaps", *args)[1] == traced.run("find-overlaps", *args)[1]
    c = overlaps(traced, *args)["candidates"][0]
    assert set(c) == {"id", "title", "category", "status", "path", "purpose", "delivery_status", "score", "level", "reasons"}
    code, out, _ = traced.run("find-overlaps", *args, json_out=False)
    assert "likely" in out and "Ask the user" in out


def test_overlap_rejects_bad_covers(traced):
    assert traced.run("find-overlaps", "--category", "US", "--title", "x", "--covers", "nope")[0] == 2
