"""M6 documentation validation: the user guide must match the released CLI, Skills and generated output."""

import re
from pathlib import Path

import pytest

from sdlc.cli import build_parser

ROOT = Path(__file__).resolve().parents[2]
README = (ROOT / "README.md").read_text()
SKILLS = sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
COMMANDS = sorted(build_parser()._subparsers._group_actions[0].choices)  # noqa: SLF001 (argparse has no public accessor)


def test_every_sdlc_command_in_the_readme_exists():
    mentioned = set(re.findall(r"`sdlc ([a-z][a-z-]+)", README)) | set(re.findall(r"^sdlc ([a-z][a-z-]+)", README, re.M))
    mentioned -= {"command", "install"}  # prose such as "`sdlc command`"
    assert mentioned and mentioned <= set(COMMANDS) | {"--version", "--help"}, mentioned - set(COMMANDS)


def test_readme_lists_the_whole_command_surface():
    for command in COMMANDS:
        assert f"`{command}`" in README or command in README, command


def test_every_skill_is_documented_and_every_documented_skill_exists():
    named = set(re.findall(r"`((?:sdlc-)?[a-z]+-[a-z-]+)`", README)) & set(SKILLS)
    assert named == set(SKILLS), set(SKILLS) - named
    assert f"{len(SKILLS)} Skills" in README


def test_install_commands_and_flags_match_the_adapters():
    for script in ("sdlc-install-claude-code", "sdlc-install-codex"):
        assert script in README
    for flag in ("--scope project", "--project-dir", "--skill", "--force", "--uninstall"):
        assert flag in README
    assert ".claude/skills" in README and ".agents/skills" in README


def test_documented_layout_matches_what_init_generates(proj):
    created = {p.relative_to(proj.root).as_posix() for p in proj.root.rglob("*")}
    for rel in (".sdlc/config.md", ".sdlc/ledger.md", "AGENTS.md", "CLAUDE.md", "map.md", "BR/map.md", "PR/map.md",
                "Stories/map.md", "Artifacts/map.md"):
        assert rel in created and rel.split("/")[-1] in README
    block = re.search(r"```text\n(\.sdlc/config\.md.*?)```", README, re.S).group(1)
    for token in ("BR/", "PR/", "Stories/", "Artifacts/", "AGENTS.md", "CLAUDE.md"):
        assert token in block


def test_publishing_documentation_matches_actual_behavior(pub_ready):
    sb, config_yaml = pub_ready
    assert config_yaml in README  # the documented config block is exactly what the CLI accepts
    code, data, _ = sb.run("publish-preview", "US-001")
    assert code == 0 and data["result"]["digest"].startswith("sha256:")
    code, data, _ = sb.run("publish-apply", "US-001")  # documented: refuses without a confirmed digest
    assert code == 1 and sb.diags(data, "confirmation-missing")
    for phrase in ("--confirm-digest", "Story + provider + repository", "never reads, stores or prints a credential", "one way"):
        assert phrase.lower() in README.lower(), phrase


@pytest.fixture
def pub_ready(proj):
    yaml_block = "publishing:\n     provider: github\n     repository: owner/repository"
    cfg = proj.root / ".sdlc" / "config.md"
    cfg.write_text(cfg.read_text().replace("\n---\n\n#", "\npublishing:\n  provider: github\n  repository: owner/repository\n---\n\n#", 1))
    proj.doc("Stories/US-001-thing.md", "US-001", title="Thing", purpose="A thing.", body="## Acceptance Criteria\n\n1. **Given** a, **when** b, **then** c.")
    proj.ok("update-map")
    assert "publishing:\n     provider: github" in README  # indented 3 spaces inside the numbered step
    return proj, yaml_block
