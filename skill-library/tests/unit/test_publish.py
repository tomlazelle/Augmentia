"""R3 `publish-preview` / `publish-apply`: preview, confirmation boundary, duplicates, failures, authority."""

import json
import re
import shutil
from pathlib import Path

import pytest

import fakegh
from conftest import Sandbox
from sdlc import github_provider, publication, publish, technical
from sdlc.project import Project

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "m4"
REPO = "acme/widgets"


# --- helpers ------------------------------------------------------------------------------------

@pytest.fixture
def gh(tmp_path_factory, monkeypatch):
    """Install the stub `gh` (outside the project root); returns an object to configure it and read its calls."""
    outside = tmp_path_factory.mktemp("stubgh")
    state = outside / "state"
    state.mkdir()
    script = outside / "gh"
    script.write_text(fakegh.SCRIPT)
    script.chmod(0o755)
    monkeypatch.setenv("SDLC_GH_COMMAND", str(script))
    monkeypatch.setenv("FAKE_GH_STATE", str(state))

    class Stub:
        def mode(self, **kw):
            (state / "mode.json").write_text(json.dumps(kw))

        def calls(self):
            path = state / "calls.jsonl"
            return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

        def creates(self):
            return [c for c in self.calls() if c["argv"][:2] == ["issue", "create"]]

    return Stub()


def story(sb, sid="US-001", *, title="Register user", covers=None, status="Draft", tbd=0, delivery="Not Started", extra=""):
    lines = ["## Acceptance Criteria", "", "1. **Given** a visitor, **when** they register, **then** an account exists."]
    if tbd:
        lines += ["", "### Unresolved Acceptance Behavior (TBD)", ""] + [f"- **TBD** — open question {i}" for i in range(tbd)]
    body = "\n".join(lines) + extra
    path = sb.doc(f"Stories/{sid}-{title.lower().replace(' ', '-')}.md", sid, title=title, purpose=f"{title} purpose.",
                  status=status, body=body, covers=covers or [], fields={"delivery_status": delivery})
    return path


def configure(sb, repository=REPO, provider="github", extra=""):
    cfg = sb.root / ".sdlc" / "config.md"
    text = cfg.read_text()
    text = text.replace("\n---\n\n#", f"\npublishing:\n  provider: {provider}\n  repository: {repository}\n{extra}---\n\n#", 1)
    cfg.write_text(text)


def preview(sb, *ids):
    return sb.run("publish-preview", *ids)


def apply_(sb, digest, *ids):
    args = ["publish-apply", *ids] + (["--confirm-digest", digest] if digest else [])
    return sb.run(*args)


def digest_of(data):
    return data["result"]["digest"]


@pytest.fixture
def pub(proj, gh):
    story(proj, "US-001", title="Register user")
    story(proj, "US-002", title="Reset password")
    proj.ok("update-map")
    configure(proj)
    return proj


# --- configuration ------------------------------------------------------------------------------

def test_missing_publishing_config_blocks_preview_and_apply(proj, gh):
    story(proj)
    proj.ok("update-map")
    code, data, _ = preview(proj, "US-001")
    assert code == 1 and proj.diags(data, "publishing-config-missing", "error")
    code, data, _ = apply_(proj, "sha256:x", "US-001")
    assert code == 1 and proj.diags(data, "publishing-config-missing")
    assert gh.calls() == []


@pytest.mark.parametrize("provider,repo,code_", [("jira", REPO, "publishing-unsupported-provider"),
                                                  ("github", "not-a-repo", "publishing-config-invalid")])
def test_unsupported_provider_or_bad_repository_blocks(proj, gh, provider, repo, code_):
    story(proj)
    proj.ok("update-map")
    configure(proj, repository=repo, provider=provider)
    code, data, _ = preview(proj, "US-001")
    assert code == 1 and proj.diags(data, code_, "error")
    assert gh.calls() == []


def test_credentials_in_config_are_rejected_by_validate(proj):
    configure(proj, extra="  token: ghp_notarealtoken1234567\n")
    code, data, _ = proj.run("validate")
    assert code == 1 and any("credentials" in d["message"] for d in proj.diags(data, "bad-config", "error"))


# --- selection ----------------------------------------------------------------------------------

def test_nothing_is_selected_by_default(pub, gh):
    code, data, _ = preview(pub)
    assert code == 2 and pub.diags(data, "no-selection")
    code, data, _ = apply_(pub, "sha256:x")
    assert code == 2 and gh.calls() == []


def test_only_named_stories_are_published(pub, gh):
    _, data, _ = preview(pub, "US-001")
    assert [s["id"] for s in data["result"]["stories"]] == ["US-001"]
    apply_(pub, digest_of(data), "US-001")
    assert len(gh.creates()) == 1
    assert "Publication" not in (pub.root / "Stories" / "US-002-reset-password.md").read_text()


def test_non_story_and_unknown_ids_are_rejected(pub, gh):
    code, data, _ = preview(pub, "PR-001")
    assert code == 2 and pub.diags(data, "bad-selection")
    code, data, _ = preview(pub, "US-099")
    assert code == 1 and pub.diags(data, "story-not-found") and data["result"]["can_apply"] is False


# --- preview ------------------------------------------------------------------------------------

def test_preview_makes_no_external_call_and_no_local_change(pub, gh):
    before = pub.snapshot()
    code, data, _ = preview(pub, "US-001", "US-002")
    assert code == 0 and data["result"]["mutations"] == 0 and data["result"]["can_apply"] is True
    assert gh.calls() == []  # preview is offline: not even a read-only provider call
    assert pub.snapshot() == before


def test_preview_is_faithful_to_the_story(pub):
    story(pub, "US-003", title="Add widget", covers=[], tbd=1, extra="\n\n## Open Questions\n\n- Who owns it?")
    pub.ok("update-map")
    _, data, _ = preview(pub, "US-003")
    s = data["result"]["stories"][0]
    assert data["result"]["repository"] == REPO and s["action"] == "create" and s["labels"] == []
    assert s["issue_title"] == "[US-003] Add widget"
    body = s["issue_body"]
    assert "US-003" in body and "authoritative" in body and "Stories/US-003-add-widget.md" in body
    assert "**Purpose:** Add widget purpose." in body
    assert "none — standalone Story" in body
    assert "1. **Given** a visitor, **when** they register, **then** an account exists." in body
    assert "### Unresolved Acceptance Behavior (TBD)" in body and "- **TBD** — open question 0" in body  # TBD stays visible
    assert "## Open Questions" in body and "Who owns it?" in body
    assert not body.lstrip().startswith("# ")  # the H1 is the Issue title, not repeated
    assert "## References" not in body  # relative links do not resolve on GitHub


def test_preview_covers_and_references_are_listed_as_ids(traced):
    configure(traced)
    _, data, _ = preview(traced, "US-001")
    body = data["result"]["stories"][0]["issue_body"]
    assert "**Covers:** `PR-001-R001`" in body and "**Derived From:** PR-001" in body


def test_operational_records_are_not_published(pub):
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text() + "\n## Implementation Record\n\n### IR-1 — 2026-09-29\n- **Summary:** done\n"
                    "- **Files changed:** `a.py`\n\n## Review Record\n\n### RV-1 — 2026-09-29\n- **Verdict:** complete\n")
    path.write_text(path.read_text().replace("delivery_status: Not Started", "delivery_status: Implemented"))
    pub.ok("update-map")
    _, data, _ = preview(pub, "US-001")
    body = data["result"]["stories"][0]["issue_body"]
    assert "Implementation Record" not in body and "IR-1" not in body and "Review Record" not in body


def test_real_fixture_preview(tmp_path, capsys, monkeypatch, gh):
    root = tmp_path / "fx"
    shutil.copytree(FIXTURES / "us001-chain-verified", root)
    sb = Sandbox(root, capsys, monkeypatch)
    cfg = root / ".sdlc" / "config.md"
    cfg.write_text(cfg.read_text().replace("\n---\n\n#", "\npublishing:\n  provider: github\n  repository: acme/widgets\n---\n\n#", 1))
    before = sb.snapshot()
    code, data, _ = sb.run("publish-preview", "US-001", "US-002")
    assert code == 0
    by_id = {s["id"]: s for s in data["result"]["stories"]}
    assert "Unresolved Acceptance Behavior (TBD)" in by_id["US-001"]["issue_body"]  # TBD visible
    assert "Implementation Record" not in by_id["US-001"]["issue_body"]
    assert "none — standalone Story" in by_id["US-002"]["issue_body"]  # standalone covers: [] is publishable
    assert {d["code"] for d in data["diagnostics"]} >= {"unresolved-acceptance", "story-no-coverage", "story-not-approved"}
    assert sb.snapshot() == before and gh.calls() == []


def test_warnings_do_not_block(pub):
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text() + "\nSee [other](../PR/map.md) for details.\n")
    _, data, _ = preview(pub, "US-001")
    assert data["result"]["can_apply"] is True
    assert pub.diags(data, "relative-links", "warning") and pub.diags(data, "story-not-approved", "warning")


def test_story_with_validation_errors_is_blocked(pub, gh):
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text() + "\n- [gone](missing.md)\n")
    code, data, _ = preview(pub, "US-001", "US-002")
    assert code == 1 and data["result"]["blocked"] == ["US-001"] and data["result"]["can_apply"] is False
    assert pub.diags(data, "story-invalid", "error")
    code, data, _ = apply_(pub, digest_of(preview(pub, "US-002")[1]), "US-001", "US-002")
    assert code == 1 and gh.calls() == []


# --- confirmation boundary ----------------------------------------------------------------------

def test_apply_without_confirmation_publishes_nothing_and_leaks_no_digest(pub, gh):
    before = pub.snapshot()
    code, data, _ = apply_(pub, None, "US-001")
    assert code == 1 and pub.diags(data, "confirmation-missing", "error")
    assert data["result"]["mutations"] == 0 and "digest" not in data["result"] and "stories" in data["result"]
    assert gh.calls() == [] and pub.snapshot() == before
    _, human, _ = pub.run("publish-apply", "US-001", json_out=False)
    assert "sha256:" not in human


def test_wrong_digest_publishes_nothing_and_leaks_no_digest(pub, gh):
    good = digest_of(preview(pub, "US-001")[1])
    code, data, err = apply_(pub, "sha256:" + "0" * 64, "US-001")
    assert code == 1 and pub.diags(data, "preview-stale", "error")
    assert good not in json.dumps(data) and gh.calls() == []


def test_digest_is_bound_to_the_selection(pub, gh):
    d = digest_of(preview(pub, "US-001")[1])
    code, data, _ = apply_(pub, d, "US-001", "US-002")
    assert code == 1 and pub.diags(data, "preview-stale") and gh.calls() == []


def test_changed_content_after_preview_invalidates_confirmation(pub, gh):
    d = digest_of(preview(pub, "US-001")[1])
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text().replace("an account exists", "an account exists and a welcome email is sent"))
    code, data, _ = apply_(pub, d, "US-001")
    assert code == 1 and pub.diags(data, "preview-stale") and gh.calls() == []
    assert "Publication" not in path.read_text()
    # a fresh preview + confirmation publishes the NEW content
    new = digest_of(preview(pub, "US-001")[1])
    assert new != d
    code, data, _ = apply_(pub, new, "US-001")
    assert code == 0 and "welcome email" in gh.creates()[0]["stdin"]


def test_changed_publication_state_or_config_invalidates_confirmation(pub, gh):
    d = digest_of(preview(pub, "US-001")[1])
    configure_cfg = pub.root / ".sdlc" / "config.md"
    configure_cfg.write_text(configure_cfg.read_text().replace(REPO, "acme/other"))
    code, data, _ = apply_(pub, d, "US-001")
    assert code == 1 and pub.diags(data, "preview-stale") and gh.calls() == []


# --- publishing ---------------------------------------------------------------------------------

def test_confirmed_publication_uses_exactly_the_previewed_content(pub, gh):
    _, data, _ = preview(pub, "US-001", "US-002")
    code, out, _ = apply_(pub, digest_of(data), "US-001", "US-002")
    assert code == 0 and out["result"]["mutations"] == 2 and out["result"]["published"] == 2
    created = gh.creates()
    assert len(created) == 2
    for call, s in zip(created, data["result"]["stories"]):
        argv = call["argv"]
        assert argv[argv.index("--repo") + 1] == REPO
        assert argv[argv.index("--title") + 1] == s["issue_title"]
        assert call["stdin"] == s["issue_body"]
        assert "--label" not in argv and "--assignee" not in argv and "--milestone" not in argv and "--project" not in argv
    assert [(o["id"], o["outcome"], o["issue"]) for o in out["result"]["outcomes"]] == [("US-001", "published", "#7"), ("US-002", "published", "#8")]


def test_only_read_only_preflight_and_create_calls_are_made(pub, gh):
    _, data, _ = preview(pub, "US-001")
    apply_(pub, digest_of(data), "US-001")
    kinds = [tuple(c["argv"][:2]) for c in gh.calls()]
    assert kinds == [("auth", "status"), ("repo", "view"), ("issue", "create")]  # no list/view/edit/close: nothing is imported


def test_success_is_recorded_non_materially_and_nothing_else_changes(pub, gh):
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text().replace("status: Draft", "status: Approved"))
    pub.ok("update-map")
    before = pub.snapshot()
    _, data, _ = preview(pub, "US-001")
    code, out, _ = apply_(pub, digest_of(data), "US-001")
    assert code == 0
    after = pub.snapshot()
    assert [p for p in after if after[p] != before.get(p)] == ["Stories/US-001-register-user.md"]
    text = path.read_text()
    meta_before = before["Stories/US-001-register-user.md"].decode()
    assert "status: Approved" in text and "delivery_status: Not Started" in text and "covers: []" in text
    assert "updated: 2026-09-29" in text and "updated: 2026-09-01" in meta_before
    assert text.split("## Publication")[0].replace("updated: 2026-09-29", "updated: 2026-09-01").rstrip() == meta_before.rstrip()
    recs, diags = publication.parse("x", "US-001", technical.sections(text))
    assert not diags and [(r.provider, r.repository, r.issue, r.url) for r in recs] == [
        ("github", REPO, "#7", f"https://github.com/{REPO}/issues/7")]
    code, v, _ = pub.run("validate")
    assert code == 0 and not pub.diags(v, severity="error")  # the Approved Story is still valid, maps still fresh
    assert out["result"]["outcomes"][0]["record"] == "PUB-1"


def test_failure_never_records_success(pub, gh):
    gh.mode(fail_titles=["[US-001]"])
    before = pub.snapshot()
    _, data, _ = preview(pub, "US-001")
    code, out, _ = apply_(pub, digest_of(data), "US-001")
    assert code == 1 and out["result"]["outcomes"][0]["outcome"] == "failed" and out["result"]["published"] == 0
    assert out["result"]["mutations"] == 0 and pub.diags(out, "provider-failed", "error")
    assert pub.snapshot() == before


def test_partial_success_is_reported_per_story(pub, gh):
    gh.mode(fail_titles=["[US-002]"])
    _, data, _ = preview(pub, "US-001", "US-002")
    code, out, _ = apply_(pub, digest_of(data), "US-001", "US-002")
    assert code == 1
    assert {o["id"]: o["outcome"] for o in out["result"]["outcomes"]} == {"US-001": "published", "US-002": "failed"}
    assert out["result"]["published"] == 1 and out["result"]["mutations"] == 1
    assert "PUB-1" in (pub.root / "Stories" / "US-001-register-user.md").read_text()
    assert "Publication" not in (pub.root / "Stories" / "US-002-reset-password.md").read_text()
    # retrying later: US-001 is known (skipped), only US-002 would be created
    gh.mode()
    _, again, _ = preview(pub, "US-001", "US-002")
    assert {s["id"]: s["action"] for s in again["result"]["stories"]} == {"US-001": "skip", "US-002": "create"}


@pytest.mark.parametrize("mode,code_", [({"unauthenticated": True}, "provider-auth"), ({"repo_missing": True}, "repository-not-found"),
                                         ({"issues_disabled": True}, "issues-disabled")])
def test_access_problems_block_before_any_creation(pub, gh, mode, code_):
    gh.mode(**mode)
    before = pub.snapshot()
    _, data, _ = preview(pub, "US-001")
    code, out, _ = apply_(pub, digest_of(data), "US-001")
    assert code == 1 and pub.diags(out, code_, "error") and gh.creates() == []
    assert out["result"]["mutations"] == 0 and pub.snapshot() == before


def test_missing_gh_executable_is_reported_not_success(pub, monkeypatch, tmp_path):
    monkeypatch.setenv("SDLC_GH_COMMAND", str(tmp_path / "no-such-gh"))
    _, data, _ = preview(pub, "US-001")
    code, out, _ = apply_(pub, digest_of(data), "US-001")
    assert code == 1 and pub.diags(out, "provider-unavailable", "error") and out["result"]["mutations"] == 0


def test_issue_without_url_is_unconfirmed_and_stops(pub, gh):
    gh.mode(nourl_titles=["[US-001]"])
    _, data, _ = preview(pub, "US-001", "US-002")
    code, out, _ = apply_(pub, digest_of(data), "US-001", "US-002")
    assert code == 1
    assert {o["id"]: o["outcome"] for o in out["result"]["outcomes"]} == {"US-001": "unconfirmed", "US-002": "not-attempted"}
    assert pub.diags(out, "provider-ambiguous", "error") and len(gh.creates()) == 1  # no blind retry, no second Issue
    assert "Publication" not in (pub.root / "Stories" / "US-001-register-user.md").read_text()


def test_recording_failure_is_reported_prominently_and_never_retried(pub, gh, monkeypatch):
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(publication, "append_record", boom)
    _, data, _ = preview(pub, "US-001", "US-002")
    code, out, _ = apply_(pub, digest_of(data), "US-001", "US-002")
    assert code == 1
    assert {o["id"]: o["outcome"] for o in out["result"]["outcomes"]} == {"US-001": "published-unrecorded", "US-002": "not-attempted"}
    msg = pub.diags(out, "record-failed", "error")[0]["message"]
    assert "INCONSISTENCY" in msg and "WAS published" in msg and "issues/7" in msg and "do not publish this Story again" in msg
    assert len(gh.creates()) == 1


# --- duplicates ---------------------------------------------------------------------------------

def test_known_publication_prevents_silent_duplicates(pub, gh):
    _, data, _ = preview(pub, "US-001")
    apply_(pub, digest_of(data), "US-001")
    assert len(gh.creates()) == 1
    code, again, _ = preview(pub, "US-001")
    s = again["result"]["stories"][0]
    assert code == 0 and s["action"] == "skip" and s["known_publication"]["issue"] == "#7"
    assert again["result"]["will_create"] == [] and again["result"]["can_apply"] is False
    assert pub.diags(again, "already-published", "notice")
    code, out, _ = apply_(pub, digest_of(again), "US-001")
    assert code == 0 and out["result"]["outcomes"][0]["outcome"] == "skipped" and out["result"]["mutations"] == 0
    assert len(gh.creates()) == 1  # still exactly one Issue; a preflight is not even needed when nothing is created
    assert [c["argv"][:2] for c in gh.calls()].count(["auth", "status"]) == 1


def test_identity_is_the_record_not_the_title(pub, gh):
    story(pub, "US-003", title="Register user")  # same title as US-001's Issue title would differ by ID, so use a record
    path = pub.root / "Stories" / "US-003-register-user.md"
    path.write_text(path.read_text() + f"\n## Publication\n\n### PUB-1 — 2026-09-30\n- **Provider:** github\n- **Repository:** {REPO}\n- **Issue:** #99\n")
    pub.ok("update-map")
    _, data, _ = preview(pub, "US-001", "US-003")
    assert {s["id"]: s["action"] for s in data["result"]["stories"]} == {"US-001": "create", "US-003": "skip"}
    assert all(c["argv"][0] not in ("search", "api") for c in gh.calls())


def test_malformed_publication_record_blocks_rather_than_risking_a_duplicate(pub, gh):
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text() + "\n## Publication\n\n### PUB-1 — 2026-09-30\n- **Provider:** github\n- **Issue:** seven\n")
    code, v, _ = pub.run("validate")
    assert code == 1 and pub.diags(v, "publication-invalid", "error")
    code, data, _ = preview(pub, "US-001")
    assert code == 1 and data["result"]["blocked"] == ["US-001"]


@pytest.mark.parametrize("field,value", [("Provider", "jira"), ("Repository", "nonsense"), ("Issue", "42")])
def test_publication_record_fields_are_validated(pub, field, value):
    fields = {"Provider": "github", "Repository": REPO, "Issue": "#5", field: value}
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text() + "\n## Publication\n\n### PUB-1 — 2026-09-30\n" + "".join(f"- **{k}:** {v}\n" for k, v in fields.items()))
    code, v, _ = pub.run("validate")
    assert code == 1 and any(field in d["message"] for d in pub.diags(v, "publication-invalid"))


def test_second_publication_record_is_numbered_sequentially(pub):
    path = pub.root / "Stories" / "US-001-register-user.md"
    publication.append_record(path, "2026-10-04", "github", REPO, 1, None)
    assert publication.append_record(path, "2026-10-05", "github", "acme/other", 2, "https://github.com/acme/other/issues/2") == "PUB-2"
    text = path.read_text()
    assert text.count("## Publication") == 1 and "### PUB-1 — 2026-10-04" in text and "### PUB-2 — 2026-10-05" in text
    code, v, _ = pub.run("validate")
    assert code == 0


def test_none_recorded_placeholder_is_replaced(pub):
    path = pub.root / "Stories" / "US-001-register-user.md"
    path.write_text(path.read_text() + "\n## Publication\n\nNone recorded.\n\n## Notes\n\nKeep me.\n")
    publication.append_record(path, "2026-10-04", "github", REPO, 3, None)
    text = path.read_text()
    assert "None recorded." not in text and "### PUB-1" in text and text.index("### PUB-1") < text.index("## Notes")
    assert "Keep me." in text


# --- local authority, credentials ---------------------------------------------------------------

def test_github_state_is_never_imported(pub, gh):
    _, data, _ = preview(pub, "US-001")
    apply_(pub, digest_of(data), "US-001")
    before = pub.snapshot()
    gh.mode(closed_issues=[7], edited=True)  # GitHub "changes" after publication
    _, status, _ = pub.run("status")
    pub.run("validate")
    assert pub.snapshot() == before
    assert status["result"]["delivery"]["Not Started"][0]["id"] in ("US-001", "US-002")  # local state only
    assert len(gh.calls()) == 3  # no further provider calls from status/validate


def test_credentials_never_reach_artifacts_or_output(pub, gh, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "ghp_FAKESECRETTOKEN0123456789")
    gh.mode(unauthenticated=True)
    _, data, _ = preview(pub, "US-001")
    code, out, _ = apply_(pub, digest_of(data), "US-001")
    assert code == 1
    assert "ghp_SECRETSECRET123456" not in json.dumps(out) and "[redacted]" in json.dumps(out)  # provider output is scrubbed
    gh.mode()
    apply_(pub, digest_of(preview(pub, "US-002")[1]), "US-002")
    for p in pub.root.rglob("*"):
        if p.is_file():
            assert "ghp_" not in p.read_text(errors="ignore"), p


def test_redact_removes_token_shapes():
    for secret in ("ghp_abcdefgh12345678", "github_pat_abcdefgh12345678", "Bearer abc.def"):
        assert secret.split()[-1] not in github_provider.redact(f"error with {secret} inside")


# --- provider boundary --------------------------------------------------------------------------

class FakeProvider:
    def __init__(self):
        self.created, self.checked = [], []

    def check_access(self, repository):
        self.checked.append(repository)

    def create_issue(self, repository, title, body):
        self.created.append((repository, title, body))
        return github_provider.IssueRef(41 + len(self.created), None)


def test_apply_accepts_an_injected_provider_and_records_without_url(pub):
    _, data, _ = preview(pub, "US-001")
    project = Project.open(pub.root)
    fake = FakeProvider()
    out = publish.apply_publication(project, ["US-001"], digest_of(data), provider=fake)
    assert out.exit_code == 0 and fake.checked == [REPO] and fake.created[0][1] == "[US-001] Register user"
    text = (pub.root / "Stories" / "US-001-register-user.md").read_text()
    assert "- **Issue:** #42" in text and "- **URL:**" not in text


def test_unexpected_provider_exception_is_never_success(pub):
    class Exploding(FakeProvider):
        def create_issue(self, *a):
            raise RuntimeError("boom ghp_abcdefgh12345678")
    _, data, _ = preview(pub, "US-001")
    out = publish.apply_publication(Project.open(pub.root), ["US-001"], digest_of(data), provider=Exploding())
    assert out.exit_code == 1 and out.result["outcomes"][0]["outcome"] == "failed"
    assert "ghp_" not in json.dumps(out.result)
    assert "Publication" not in (pub.root / "Stories" / "US-001-register-user.md").read_text()


def test_cli_human_output_shows_target_title_body_and_digest(pub):
    _, text, _ = pub.run("publish-preview", "US-001", json_out=False)
    assert f"Target: github {REPO}" in text and "Title: [US-001] Register user" in text
    assert "Preview only — no external mutation was made" in text and re.search(r"Digest: sha256:[0-9a-f]{64}", text)
    assert "an account exists" in text


def test_digest_is_stable_and_order_independent(pub):
    a = digest_of(preview(pub, "US-001", "US-002")[1])
    b = digest_of(preview(pub, "US-002", "US-001", "US-001")[1])
    assert a == b and a == digest_of(preview(pub, "US-001", "US-002")[1])


# --- identity = Story + provider + repository ---------------------------------------------------

def _record(path, repo, issue, n=1):
    path.write_text(path.read_text() + f"\n## Publication\n\n### PUB-{n} — 2026-09-30\n- **Provider:** github\n"
                    f"- **Repository:** {repo}\n- **Issue:** #{issue}\n" if "## Publication" not in path.read_text() else
                    path.read_text() + f"\n### PUB-{n} — 2026-09-30\n- **Provider:** github\n- **Repository:** {repo}\n- **Issue:** #{issue}\n")


def test_same_repository_publication_is_still_skipped(pub, gh):
    path = pub.root / "Stories" / "US-001-register-user.md"
    _record(path, REPO, 42)
    _, data, _ = preview(pub, "US-001")
    s = data["result"]["stories"][0]
    assert s["action"] == "skip" and s["known_publication"]["repository"] == REPO and s["other_publications"] == []
    out = apply_(pub, digest_of(data), "US-001")[1]
    assert out["result"]["outcomes"][0]["outcome"] == "skipped" and gh.calls() == []


def test_publication_in_another_repository_does_not_block_this_one(pub, gh):
    path = pub.root / "Stories" / "US-001-register-user.md"
    _record(path, "org/repo-a", 42)
    code, data, _ = preview(pub, "US-001")  # configured repository is acme/widgets
    s = data["result"]["stories"][0]
    assert code == 0 and s["action"] == "create" and s["known_publication"] is None
    assert [(o["repository"], o["issue"]) for o in s["other_publications"]] == [("org/repo-a", "#42")]
    assert pub.diags(data, "published-elsewhere", "notice") and data["result"]["can_apply"] is True
    _, human, _ = pub.run("publish-preview", "US-001", json_out=False)
    assert "Also published elsewhere: github:org/repo-a#42" in human
    # still gated: no digest, nothing happens; with the confirmed digest the second repository gets its own Issue and record
    assert apply_(pub, None, "US-001")[0] == 1 and gh.calls() == []
    code, out, _ = apply_(pub, digest_of(data), "US-001")
    assert code == 0 and out["result"]["outcomes"][0]["outcome"] == "published" and len(gh.creates()) == 1
    assert gh.creates()[0]["argv"][gh.creates()[0]["argv"].index("--repo") + 1] == REPO
    recs, diags = publication.parse("x", "US-001", technical.sections(path.read_text()))
    assert not diags and [(r.id, r.repository, r.issue) for r in recs] == [("PUB-1", "org/repo-a", "#42"), ("PUB-2", REPO, "#7")]
    # now both repositories are known; a repeat in either is skipped, and switching back to repo-a is also a skip
    again = preview(pub, "US-001")[1]
    assert again["result"]["stories"][0]["action"] == "skip" and again["result"]["stories"][0]["known_publication"]["issue"] == "#7"
    cfg = pub.root / ".sdlc" / "config.md"
    cfg.write_text(cfg.read_text().replace(REPO, "org/repo-a"))
    back = preview(pub, "US-001")[1]
    assert back["result"]["stories"][0]["action"] == "skip" and back["result"]["stories"][0]["known_publication"]["issue"] == "#42"


def test_repository_is_part_of_the_confirmed_digest(pub, gh):
    path = pub.root / "Stories" / "US-001-register-user.md"
    _record(path, "org/repo-a", 42)
    d = digest_of(preview(pub, "US-001")[1])
    cfg = pub.root / ".sdlc" / "config.md"
    cfg.write_text(cfg.read_text().replace(REPO, "org/repo-b"))  # a confirmation for acme/widgets cannot publish to org/repo-b
    code, out, _ = apply_(pub, d, "US-001")
    assert code == 1 and pub.diags(out, "preview-stale") and gh.calls() == []
