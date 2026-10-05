"""Static checks on the Skill sources plus template instantiation through the real CLI."""

import re
from pathlib import Path

import pytest

from sdlc.cli import build_parser
from sdlc.frontmatter import parse, split

ROOT = Path(__file__).resolve().parents[2]
SKILLS = {p.name: p for p in sorted((ROOT / "skills").iterdir()) if p.is_dir()}
CREATING = ["create-brd", "create-prd", "create-stories"]
PATH_TOKEN = re.compile(r"`((?:references/|\.\./\.\./shared/|\.\./\.\./\.\./shared/)[\w./-]+\.md)`")
CMD = re.compile(r"`sdlc ([a-z-]+)([^`]*)`")


def skill_text(name):
    return (SKILLS[name] / "SKILL.md").read_text()


def subparsers():
    parser = build_parser()
    action = next(a for a in parser._actions if a.dest == "command")
    return action.choices


def test_creating_skills_present():
    assert set(CREATING) <= set(SKILLS)
    assert (ROOT / "shared" / "interview.md").is_file()


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_frontmatter_is_valid(name):
    raw, _ = split(skill_text(name))
    meta = parse(raw)
    assert meta["name"] == name and 40 < len(meta["description"]) <= 1024
    assert set(meta) == {"name", "description"}


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_referenced_files_exist(name):
    for token in PATH_TOKEN.findall(skill_text(name)):
        assert (SKILLS[name] / token).resolve().is_file(), token
    for md in (SKILLS[name] / "references").glob("*.md") if (SKILLS[name] / "references").is_dir() else []:
        for token in PATH_TOKEN.findall(md.read_text()):
            assert (md.parent / token).resolve().is_file() or (SKILLS[name] / token).resolve().is_file(), (md, token)


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_only_real_cli_commands_and_flags_are_used(name):
    choices = subparsers()
    for cmd, rest in CMD.findall(skill_text(name)):
        assert cmd in choices, cmd
        known = {opt for a in choices[cmd]._actions for opt in a.option_strings}
        for flag in re.findall(r"--[a-z-]+", rest):
            assert flag in known, f"{name}: {cmd} {flag}"


@pytest.mark.parametrize("name", CREATING)
def test_supporting_files_present(name):
    for f in ("section-catalog.md", "discovery-questions.md", "template.md"):
        assert (SKILLS[name] / "references" / f).is_file()


@pytest.mark.parametrize("name", CREATING)
def test_workflow_order_and_rules(name):
    text = skill_text(name)
    assert text.index("find-overlaps") < text.index("allocate-id --category")
    assert text.index("update-map") < text.rindex("validate")
    assert text.index("shared/interview.md") >= 0
    extra = ["covers"] if name == "create-stories" else ["retire-id", "allocate-id --requirement"]
    for phrase in ["Draft", "In Review", "Approved", "TBD", "coverage notices", *extra]:
        assert phrase in text, phrase
    assert re.search(r"[Nn]ever set `status: Approved` on your own", text)
    assert "ask the user to choose" in text


@pytest.mark.parametrize("name", sorted(SKILLS))
def test_skills_contain_no_reimplemented_algorithms(name):
    text = skill_text(name)
    assert "```" not in text  # no embedded scripts
    assert not re.search(r"highest (existing )?(ID|number)|plus one|max\(|glob\(", text)


def test_stories_skill_forbids_delivery_states_and_invented_ids():
    text = skill_text("create-stories")
    assert "Never set `delivery_status` to `In Progress`, `Implemented` or `Verified`" in text
    assert "Never invent requirement IDs" in text
    assert "standalone" in text and "story-no-coverage" in text and "covers: []" in text


def test_interview_guide_contents():
    text = (ROOT / "shared" / "interview.md").read_text()
    for needle in ("3–5", "Unknown", "TBD", "Not applicable", "Assumption", "Round 1", "Round 2", "before writing", "suggested option"):
        assert needle in text, needle


# ---- templates instantiate into documents the validator accepts --------------------------------

def instantiate(skill, doc_id, title, covers="", derived=None):
    text = (SKILLS[skill] / "references" / "template.md").read_text()
    text = (text.replace("{{ID}}", doc_id).replace("{{TITLE}}", title).replace("{{DATE}}", "2026-09-29")
            .replace("{{ONE_SENTENCE_PURPOSE}}", "A purpose.").replace("{{ONE_SENTENCE_VALUE}}", "A value.")
            .replace("{{REQUIREMENT_IDS_OR_EMPTY}}", covers))
    if derived:
        text = text.replace("### Derived From\n- None identified.", f"### Derived From\n- {derived}")
    return re.sub(r"\{\{[^}]*\}\}", "Placeholder content.", text)


def test_brd_template_yields_valid_document(proj):
    proj.ok("allocate-id", "--category", "BR", "--title", "T")
    proj.ok("allocate-id", "--requirement", "BR-001")
    (proj.root / "BR" / "BR-001-t.md").write_text(instantiate("create-brd", "BR-001", "T"))
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0, data["diagnostics"]
    ids = [r["id"] for r in proj.ok("references", "BR-001-R001")["result"]["incoming"]]
    assert proj.ok("references", "BR-001-R001")["result"]["defined_in"]["id"] == "BR-001" and ids == []


def test_prd_template_valid_with_and_without_brd(proj):
    proj.ok("allocate-id", "--category", "PR", "--title", "P")
    proj.ok("allocate-id", "--requirement", "PR-001")
    (proj.root / "PR" / "PR-001-p.md").write_text(instantiate("create-prd", "PR-001", "P"))
    proj.ok("update-map")
    assert proj.run("validate")[0] == 0
    proj.ok("allocate-id", "--category", "BR", "--title", "B")
    proj.ok("allocate-id", "--requirement", "BR-001")
    (proj.root / "BR" / "BR-001-b.md").write_text(instantiate("create-brd", "BR-001", "B"))
    proj.ok("allocate-id", "--category", "PR", "--title", "Q")
    proj.ok("allocate-id", "--requirement", "PR-002")
    (proj.root / "PR" / "PR-002-q.md").write_text(
        instantiate("create-prd", "PR-002", "Q", derived="[BR-001 — B](../BR/BR-001-b.md) — serves BR-001-R001"))
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0, data["diagnostics"]
    assert "Derived From" in (proj.root / "PR" / "map.md").read_text()


def test_story_template_standalone_and_covering(proj):
    proj.ok("allocate-id", "--category", "PR", "--title", "P")
    proj.ok("allocate-id", "--requirement", "PR-001")
    (proj.root / "PR" / "PR-001-p.md").write_text(instantiate("create-prd", "PR-001", "P"))
    proj.ok("allocate-id", "--category", "US", "--title", "Alone")
    (proj.root / "Stories" / "US-001-alone.md").write_text(instantiate("create-stories", "US-001", "Alone"))
    proj.ok("allocate-id", "--category", "US", "--title", "Linked")
    (proj.root / "Stories" / "US-002-linked.md").write_text(
        instantiate("create-stories", "US-002", "Linked", covers="PR-001-R001", derived="[PR-001 — P](../PR/PR-001-p.md)"))
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0, data["diagnostics"]
    assert {(d["code"], d["id"]) for d in proj.diags(data, severity="notice")} == {("story-no-coverage", "US-001")}


def test_story_covers_without_link_is_rejected(proj):
    proj.ok("allocate-id", "--category", "PR", "--title", "P")
    proj.ok("allocate-id", "--requirement", "PR-001")
    (proj.root / "PR" / "PR-001-p.md").write_text(instantiate("create-prd", "PR-001", "P"))
    proj.ok("allocate-id", "--category", "US", "--title", "Bad")
    (proj.root / "Stories" / "US-001-bad.md").write_text(instantiate("create-stories", "US-001", "Bad", covers="PR-001-R001"))
    proj.ok("update-map")
    assert proj.diags(proj.run("validate")[1], "covers-source-not-linked")


# ---- M3 correction pass: recap, verbatim overlap, TBD vs verifiable, project instructions ----------

@pytest.mark.parametrize("name", CREATING)
def test_overlap_candidates_are_presented_verbatim(name):
    text = skill_text(name)
    assert "exactly as the CLI returned them" in text
    assert "Do not paraphrase, round, reorder, summarize or invent any ID, score or reason" in text
    assert text.index("exactly as the CLI returned them") < text.index("allocate-id --category")


@pytest.mark.parametrize("name", CREATING)
def test_recap_is_mandatory_in_every_creating_skill(name):
    assert "mandatory recap" in skill_text(name)


def test_interview_guide_makes_recap_a_mandatory_boundary():
    text = (ROOT / "shared" / "interview.md").read_text()
    assert "Mandatory recap between rounds" in text and "Recap so far" in text
    assert "Skipping it is not allowed" in text
    assert "Recap before Round 2 (mandatory)" in text
    assert "Move from one question round to the next without the recap" in text


def test_unresolved_acceptance_is_tbd_not_an_executable_criterion():
    stories = skill_text("create-stories")
    assert "not** an acceptance criterion" in stories and "Unresolved Acceptance Behavior (TBD)" in stories
    template = (SKILLS["create-stories"] / "references" / "template.md").read_text()
    assert "### Unresolved Acceptance Behavior (TBD)" in template and "- **TBD** —" in template
    catalog = (SKILLS["create-stories"] / "references" / "section-catalog.md").read_text()
    assert "Verifiable versus unresolved" in catalog and "decided, observable" in catalog
    prd = (SKILLS["create-prd"] / "references" / "section-catalog.md").read_text()
    assert "duplicate detection" in prd and "`- **TBD** — <question>`" in prd
    assert "TBD" in skill_text("create-brd") and "never as an assertion" in skill_text("create-brd")


def test_story_template_with_unresolved_section_still_validates(proj):
    proj.ok("allocate-id", "--category", "US", "--title", "Alone")
    (proj.root / "Stories" / "US-001-alone.md").write_text(instantiate("create-stories", "US-001", "Alone"))
    proj.ok("update-map")
    assert proj.run("validate")[0] == 0


INSTRUCTIONS = ROOT / "sdlc" / "templates"


@pytest.mark.parametrize("filename", ["AGENTS.md", "CLAUDE.md"])
def test_project_instruction_templates_are_narrow_workflow_guidance(filename):
    text = (INSTRUCTIONS / filename).read_text()
    for needle in ("create-brd", "create-prd", "create-stories", "refine-stories", "create-design", "plan-implementation",
                   "create-test-plan", "implement-story", "review-implementation", "verify-story",
                   "Approved", "In Review", "revision rules", "SKILL.md", "actually run and recorded"):
        assert needle in text, needle
    assert not re.search(r"(?i)\bhash|checksum|daemon|database", text)  # guidance only: no new mechanism
    assert len(text.splitlines()) < 40


def test_agents_and_claude_templates_are_identical():
    assert (INSTRUCTIONS / "AGENTS.md").read_text() == (INSTRUCTIONS / "CLAUDE.md").read_text()


# ---- post-M3 hardening: contextual overlap review ---------------------------------------------

@pytest.mark.parametrize("name,cat,mapfile", [("create-brd", "BR", "BR/map.md"), ("create-prd", "PR", "PR/map.md"),
                                              ("create-stories", "US", "Stories/map.md")])
def test_contextual_overlap_review_follows_cli_check_and_precedes_allocation(name, cat, mapfile):
    text = skill_text(name)
    cli = text.index("exactly as the CLI returned them")
    review = text.index("Contextual overlap review")
    alloc = text.index("allocate-id --category")
    assert text.index("find-overlaps") < cli < review < alloc
    assert f"sdlc list --category {cat}" in text and mapfile in text
    assert "Conceptual overlaps (my judgement, not CLI-scored)" in text
    assert "separately" in text
    assert "Never attach a score, percentage or level" in text and "never invent a similarity value" in text
    assert "No conceptual overlaps found." in text and "even when the CLI returned no candidates" in text
    for choice in ("**revise**", "**relate**", "**create new**"):
        assert choice in text
    assert "Do not allocate an ID until they choose" in text
    assert "Related To" in text


def test_stories_review_also_considers_covered_requirements():
    assert "which requirement IDs existing Stories already cover" in skill_text("create-stories")


def test_cli_contract_documents_lexical_limit_and_instruction_files():
    text = (ROOT / "shared" / "cli-contract.md").read_text()
    assert "contextual overlap review" in text and "Scoring is lexical" in text
    assert "create-if-missing" in text and "AGENTS.md" in text and "CLAUDE.md" in text


# ---- M4: technical Skills ---------------------------------------------------------------------

TECH = ["refine-stories", "create-design", "plan-implementation", "implement-story", "review-implementation",
        "create-test-plan", "verify-story"]
TECH_CREATING = {"create-design": ("DES", "design"), "plan-implementation": ("PLAN", "plans"), "create-test-plan": ("TEST", "tests")}


def test_seven_technical_skills_and_shared_conventions_present():
    assert set(TECH) <= set(SKILLS)
    text = (ROOT / "shared" / "technical-conventions.md").read_text()
    for needle in ("Two separate states", "delivery_status` transitions", "Rework and invalidation", "Implementation Record",
                   "Verification Runs", "Review Record", "passed", "blocked", "not-run", "Superseded", "Inspect before proposing"):
        assert needle in text, needle


@pytest.mark.parametrize("name", sorted(TECH_CREATING))
def test_technical_creating_skills_follow_r1_workflow(name):
    cat, sub = TECH_CREATING[name]
    text = skill_text(name)
    for f in ("section-catalog.md", "discovery-questions.md", "template.md"):
        assert (SKILLS[name] / "references" / f).is_file()
    cli = text.index("exactly as the CLI returned them")
    review = text.index("Contextual overlap review")
    create = text.index(f"create-dir --artifact {sub}")
    alloc = text.index(f"allocate-id --category {cat}")
    assert text.index("find-overlaps") < cli < review < create < alloc
    assert f"find-overlaps --category {cat}" in text and f"list --category {cat}" in text
    for phrase in ("mandatory recap", "Conceptual overlaps (my judgement, not CLI-scored)", "**revise**", "**relate**", "**create new**",
                   "Do not allocate an ID until they choose", "Inspect the repository", "In Review", "Never change a Story's `delivery_status`",
                   "Never set `status: Approved` on your own", "Derived From", "coverage notices"):
        assert phrase in text, phrase
    assert text.index("update-map") < text.rindex("validate")


def test_design_and_plan_are_optional_and_research_is_optional():
    design = skill_text("create-design")
    assert "optional Research" in design or "optional Research note" in design
    assert "never required" in design or "not required" in design.lower() or "never required for a Story" in design
    assert "with or without a Design" in skill_text("plan-implementation") or "without a Design" in skill_text("plan-implementation")
    assert (SKILLS["create-design"] / "references" / "research-template.md").is_file()


def test_refine_stories_never_sets_state_on_its_own():
    text = skill_text("refine-stories")
    assert "Never set `delivery_status: Ready` because you think the Story is ready" in text
    assert "you never set `In Progress`, `Implemented` or `Verified`" in text
    assert "Invalidation" in text and "`Ready`" in text
    assert "Superseded:** yes — Story changed" in text
    assert "never `then … TBD`" in text
    assert (SKILLS["refine-stories"] / "references" / "readiness-checklist.md").is_file()


def test_implement_story_contract():
    text = skill_text("implement-story")
    for phrase in ("Only this Skill sets `Implemented`", "you never set `Verified`", "you never set `Ready`", "explicit go-ahead",
                   "Implementation Record", "Tests run", "Never claim completion from generated code alone", "never invent a pass",
                   "`Not Started`", "Superseded", "In Progress"):
        assert phrase in text, phrase
    assert "reserved for `verify-story`" in text
    assert "Superseded:** yes — new implementation pass" in text
    assert text.index("Get authorization") < text.index("Set `delivery_status: In Progress`") < text.index("Run the tests for real")


def test_verify_story_contract():
    text = skill_text("verify-story")
    for phrase in ("Only this Skill sets `Verified`", "`passed`", "`failed`", "`blocked`", "`not-run`", "exit code", "date -u",
                   "Artifacts/tests/evidence/", "never edit or delete earlier runs", "every numbered decided criterion",
                   "Unresolved TBD behavior is **not** verified", "Review Record", "Never claim an unrun command passed",
                   "Criteria: none", "never a personal email address"):
        assert phrase in text, phrase
    assert "Set `delivery_status: Verified`" in text and "only if" in text


def test_review_implementation_is_read_only_and_not_verification():
    text = skill_text("review-implementation")
    for phrase in ("read-only", "not verification", "blocker", "major", "minor", "nit", "verified observation", "potential concern",
                   "complete", "requires-rework", "blocked", "Never set or imply `Verified`"):
        assert phrase in text, phrase
    assert "Suggest; do not apply" in text


@pytest.mark.parametrize("name", TECH)
def test_technical_skills_reference_shared_conventions(name):
    assert "technical-conventions.md" in skill_text(name)


def test_only_the_right_skills_may_set_terminal_states():
    for name in TECH:
        text = skill_text(name)
        if name != "verify-story":
            assert not re.search(r"(?<!never )(?<!Never )[Ss]et `delivery_status: Verified`", text.replace("never set `Verified`", "")), name
    assert "Set `delivery_status: Implemented`" in skill_text("implement-story")
    assert "Set `delivery_status: Implemented`" not in skill_text("verify-story")


def instantiate_tech(skill, doc_id, title, derived, template="template.md"):
    text = (SKILLS[skill] / "references" / template).read_text()
    text = (text.replace("{{ID}}", doc_id).replace("{{TITLE}}", title).replace("{{DATE}}", "2026-09-29")
            .replace("{{ONE_SENTENCE_PURPOSE}}", "A purpose.").replace("{{SOURCE_STORY_LINK_AND_REQUIREMENT_IDS}}", derived)
            .replace("{{SOURCE_STORY_OR_DESIGN_LINK}}", derived))
    return re.sub(r"\{\{[^}]*\}\}", "Placeholder content.", text)


def test_technical_templates_instantiate_into_valid_linked_documents(proj):
    proj.ok("allocate-id", "--category", "PR", "--title", "P")
    proj.ok("allocate-id", "--requirement", "PR-001")
    (proj.root / "PR" / "PR-001-p.md").write_text(instantiate("create-prd", "PR-001", "P"))
    proj.ok("allocate-id", "--category", "US", "--title", "S")
    (proj.root / "Stories" / "US-001-s.md").write_text(instantiate(
        "create-stories", "US-001", "S", covers="PR-001-R001", derived="[PR-001 — P](../PR/PR-001-p.md)"))
    link = "[US-001 — S](../../Stories/US-001-s.md) — serves PR-001-R001"
    for skill, cat, sub, tmpl in (("create-design", "DES", "design", "template.md"), ("create-design", "RES", "research", "research-template.md"),
                                  ("plan-implementation", "PLAN", "plans", "template.md"), ("create-test-plan", "TEST", "tests", "template.md")):
        proj.ok("create-dir", "--artifact", sub)
        new_id = proj.ok("allocate-id", "--category", cat, "--title", "Thing")["result"]["id"]
        (proj.root / "Artifacts" / sub / f"{new_id}-thing.md").write_text(instantiate_tech(skill, new_id, "Thing", link, tmpl))
    proj.ok("update-map")
    code, data, _ = proj.run("validate")
    assert code == 0, data["diagnostics"]
    for sub, prefix in (("design", "DES"), ("plans", "PLAN"), ("research", "RES"), ("tests", "TEST")):
        assert f"{prefix}-001" in (proj.root / "Artifacts" / sub / "map.md").read_text()
    refs = proj.ok("references", "US-001")["result"]["incoming"]
    assert {i["source"]["id"] for i in refs} == {"DES-001", "RES-001", "PLAN-001", "TEST-001"}


def test_test_plan_template_has_no_runs_and_requires_no_evidence(proj):
    text = (SKILLS["create-test-plan"] / "references" / "template.md").read_text()
    assert "## Repository Context" in text and "### Inspected" in text
    assert "## Verification Runs\n\nNone recorded." in text and "### Unresolved Acceptance Behavior" not in text
    assert "## Unresolved Acceptance Behavior (TBD)" in text and "TS-1" in text and "AC-1" in text


# --- R3: sdlc-status and publish-stories --------------------------------------------------------

R3 = ["sdlc-status", "publish-stories"]


def _skill_text(name):
    return (SKILLS[name] / "SKILL.md").read_text()


def test_r3_skills_and_shared_conventions_present():
    for name in R3:
        assert name in SKILLS and (SKILLS[name] / "SKILL.md").is_file()
    assert (ROOT / "shared" / "publishing-conventions.md").is_file()
    for name in R3:
        assert "../../shared/publishing-conventions.md" in _skill_text(name)


def test_sdlc_status_is_read_only_and_derives_state_from_files():
    text = _skill_text("sdlc-status")
    assert "sdlc status" in text and "Read-only" in text
    assert "conversation memory" in text and "informational" in text and "not a defect" in text
    for forbidden in ("sdlc update-map`,", "sdlc allocate-id`,"):
        assert forbidden not in text.split("## Rules")[0]
    assert "Never run `init`, `allocate-id`, `retire-id`, `create-dir` or `update-map`" in text


def test_publish_stories_enforces_preview_then_explicit_confirmation():
    text = _skill_text("publish-stories")
    flow = text.split("## Workflow")[1].split("## Rules")[0]
    assert flow.index("publish-preview") < flow.index("Ask for explicit confirmation") < flow.index("publish-apply")
    for required in ("verbatim", "complete body", "not** confirmation", "--confirm-digest", "Never create an Issue yourself",
                     "never one printed by a refused apply", "No external mutation before a shown preview", "preview-stale",
                     "Never print or store credentials"):
        assert required in text, required
    assert "gh issue create" in text and text.count("gh issue create") == 1  # only mentioned to forbid it


def test_publish_stories_forbids_scope_creep_and_authority_leaks():
    text = _skill_text("publish-stories")
    for required in ("never changes requirements, acceptance criteria, `status` or `delivery_status`",
                     "Do not update, close, label or edit existing Issues", "do not import anything from GitHub",
                     "open or closed Issue says nothing about `delivery_status`", "do not create PRs, branches",
                     "you have not read it", "gained a `## Publication` record and a new `updated` date, and nothing else"):
        assert required in text, required


def test_publishing_conventions_pin_the_contract():
    text = (ROOT / "shared" / "publishing-conventions.md").read_text()
    for required in ("Local Markdown is authoritative", "preview-stale", "## Publication", "PUB-1", "Non-material metadata",
                     "never matched to a Story by its title", "GH_TOKEN", "published-unrecorded", "unconfirmed"):
        assert required in text, required
    assert "publishing:\n  provider: github\n  repository: owner/repository" in text


def test_instruction_templates_route_publishing_through_the_skill():
    for filename in ("AGENTS.md", "CLAUDE.md"):
        text = (ROOT / "sdlc" / "templates" / filename).read_text()
        assert "publish-stories" in text and "explicit confirmation" in text and "sdlc-status" in text


def test_cli_contract_documents_r3_commands_and_rules():
    text = (ROOT / "shared" / "cli-contract.md").read_text()
    for required in ("### `status`", "### `publish-preview", "### `publish-apply", "publication-invalid", "preview-stale",
                     "confirmation-missing", "SDLC_GH_COMMAND", "publishing-config-missing"):
        assert required in text, required


def test_review_skill_names_the_exact_review_record_heading():
    """Regression (M6 defect 3): a real run wrote `### RR-1` instead of the contract's `### RV-n`."""
    text = _skill_text("review-implementation")
    assert "### RV-<n> — <YYYY-MM-DD>" in text and "RV, not RR" in text
    assert "### RV-1 — " in (ROOT / "shared" / "technical-conventions.md").read_text()
