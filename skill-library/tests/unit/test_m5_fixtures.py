"""Acceptance checks on projects produced by real Claude Code and Codex runs of `sdlc-status` / `publish-stories`.

Fixtures (tests/fixtures/m5) are snapshots of throwaway repositories seeded from the M4 `us001-chain-verified`
fixture, driven through a *stub* `gh` (tests/unit/fakegh.py): no real GitHub call was made. Provider call logs and
transcripts are in tests/fixtures/m5/transcripts. See docs/SDLC-M5-EVIDENCE.md for the disclosed setup.
"""

import json
import re
import shutil
from pathlib import Path

import pytest

from conftest import Sandbox
from sdlc import frontmatter, publication, publish, technical
from sdlc.project import Project, scan_documents

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "m5"
M4 = Path(__file__).resolve().parents[1] / "fixtures" / "m4" / "us001-chain-verified"
TRANSCRIPTS = FIXTURES / "transcripts"
NAMES = sorted(p.name for p in FIXTURES.iterdir() if p.is_dir() and p.name != "transcripts")
PUBLISHED = {"published-claude-us001-us002": ("cc-pub", ["US-001", "US-002"]), "published-codex-us002": ("cx-pub", ["US-002"])}


@pytest.fixture
def fx(tmp_path, capsys, monkeypatch):
    def open_(name):
        root = tmp_path / name
        shutil.copytree(FIXTURES / name, root)
        return Sandbox(root, capsys, monkeypatch)
    return open_


def meta(path):
    return frontmatter.parse(frontmatter.split(path.read_text())[0])


def story(root, sid):
    return next((root / "Stories").glob(f"{sid}-*.md"))


def calls(label):
    path = TRANSCRIPTS / f"{label}-gh-calls.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.mark.parametrize("name", NAMES)
def test_every_fixture_validates_and_maps_are_current(fx, name):
    sb = fx(name)
    code, data, _ = sb.run("validate")
    assert code == 0 and data["result"]["summary"]["error"] == 0, sb.diags(data, severity="error")
    assert not sb.diags(data, "stale-map") and not sb.diags(data, "publication-invalid")
    before = sb.snapshot()
    sb.ok("update-map")
    assert sb.snapshot() == before


@pytest.mark.parametrize("name", NAMES)
def test_status_on_each_fixture_is_read_only_and_accurate(fx, name):
    sb = fx(name)
    before = sb.snapshot()
    code, data, _ = sb.run("status")
    r = data["result"]
    assert code == 0 and r["health"]["ok"] is True and sb.snapshot() == before
    assert [i["id"] for i in r["delivery"]["Verified"]] == ["US-001"] and [i["id"] for i in r["delivery"]["Ready"]] == ["US-002"]


@pytest.mark.parametrize("name", PUBLISHED)
def test_published_story_matches_exactly_what_the_stub_provider_received(fx, name):
    label, ids = PUBLISHED[name]
    sb = fx(name)
    docs = {d.id: d for d in scan_documents(Project.open(sb.root))[0]}
    creates = [c for c in calls(label) if c["argv"][:2] == ["issue", "create"]]
    assert len(creates) == len(ids)
    for sid, call in zip(ids, creates):
        title, body = publish.render_issue(docs[sid])
        argv = call["argv"]
        assert argv[argv.index("--title") + 1] == title and argv[argv.index("--repo") + 1] == "acme/widgets"
        assert call["stdin"] == body  # the agent-run publication is byte-identical to today's rendering of the Story
        pubs, diags = publication.parse("x", sid, technical.sections(docs[sid].text))
        assert not diags and len(pubs) == 1 and pubs[0].repository == "acme/widgets" and pubs[0].provider == "github"
        assert pubs[0].url == f"https://github.com/acme/widgets/issues/{pubs[0].number}"


@pytest.mark.parametrize("name", PUBLISHED)
def test_publication_was_non_material(fx, name):
    _, ids = PUBLISHED[name]
    sb = fx(name)
    for sid in ids:
        now = meta(story(sb.root, sid))
        was = meta(story(M4, sid))
        assert {k: v for k, v in now.items() if k != "updated"} == {k: v for k, v in was.items() if k != "updated"}
        assert now["updated"] > was["updated"]  # only the date moved
        text = story(sb.root, sid).read_text()
        original = story(M4, sid).read_text()
        assert text.split("\n## Publication")[0].replace(f"updated: {now['updated']}", f"updated: {was['updated']}").rstrip() == original.rstrip()


@pytest.mark.parametrize("name", PUBLISHED)
def test_republishing_a_published_story_is_skipped_not_duplicated(fx, name):
    _, ids = PUBLISHED[name]
    sb = fx(name)
    code, data, _ = sb.run("publish-preview", *ids)
    assert code == 0 and data["result"]["will_create"] == [] and data["result"]["can_apply"] is False
    assert {s["id"]: s["action"] for s in data["result"]["stories"]} == {sid: "skip" for sid in ids}


@pytest.mark.parametrize("label,expected", [("cc-pub", ["auth status", "repo view", "issue create", "issue create"]),
                                             ("cx-pub", ["auth status", "repo view", "issue create"])])
def test_provider_call_logs_show_only_preflight_and_creation(label, expected):
    assert [" ".join(c["argv"][:2]) for c in calls(label)] == expected  # no list/view/edit/close: nothing imported


def test_unpublished_fixture_after_a_post_preview_edit_has_no_publication_and_a_new_digest(fx):
    sb = fx("edited-after-preview-unpublished")
    assert "## Publication" not in story(sb.root, "US-002").read_text()
    assert "only whitespace also returns 0)" in story(sb.root, "US-002").read_text()
    assert not (TRANSCRIPTS / "cc-stale-gh-calls.jsonl").exists()  # the stale confirmation made no provider call at all
    _, data, _ = sb.run("publish-preview", "US-002")
    assert data["result"]["stories"][0]["action"] == "create" and "(a text of only whitespace also returns 0)" in data["result"]["stories"][0]["issue_body"]


TRANSCRIPT_MARKERS = {
    "cc-status.md": ["sdlc-status", "before=91ea4f509cb4623c after=91ea4f509cb4623c", "Fix anything that looks stale"],
    "cx-status.md": ["sdlc-status", "before=91ea4f509cb4623c after=91ea4f509cb4623c", "Fix anything that looks stale"],
    "cc-publish.md": ["publish-stories", "NOT a confirmation", "explicit confirmation", "no gh call"],
    "cx-publish.md": ["publish-stories", "NOT a confirmation", "explicit confirmation", "zero `gh` calls"],
    "cc-publish-stale.md": ["OLD preview", "`gh` call log empty"],
}


@pytest.mark.parametrize("name", TRANSCRIPT_MARKERS)
def test_each_r3_skill_has_a_real_transcript_for_both_agents(name):
    text = (TRANSCRIPTS / name).read_text()
    for marker in TRANSCRIPT_MARKERS[name]:
        assert marker in text, marker
    assert "stub" in text and "### USER" in text and "### AGENT" in text


def test_no_credentials_or_personal_emails_in_fixtures_or_transcripts():
    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    for path in FIXTURES.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="ignore")
            assert not re.search(r"ghp_|github_pat_|gho_|ghs_|Bearer ", text), path
            found = [e for e in email.findall(text) if not e.endswith("example.com")]
            assert not found, (path, found)
            assert "tomlazelle" not in text and "gmail" not in text, path


def test_fixture_config_holds_no_credentials():
    for name in NAMES:
        cfg = frontmatter.parse(frontmatter.split((FIXTURES / name / ".sdlc" / "config.md").read_text())[0])
        assert cfg["publishing"] == {"provider": "github", "repository": "acme/widgets"}
