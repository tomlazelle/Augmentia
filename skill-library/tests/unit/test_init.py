import os
from importlib import resources

from sdlc import frontmatter


def test_empty_repo_init_creates_structure_and_validates(sb):
    data = sb.init()
    created = set(data["result"]["created"])
    for p in ["map.md", "BR/map.md", "PR/map.md", "Stories/map.md", "Artifacts/map.md",
              ".sdlc/config.md", ".sdlc/ledger.md"]:
        assert p in created and (sb.root / p).is_file()
    assert not (sb.root / ".sdlc" / "map.md").exists()
    assert not (sb.root / "Artifacts" / "design").exists()
    code, out, _ = sb.run("validate")
    assert code == 0 and out["result"]["summary"] == {"error": 0, "warning": 0, "notice": 0}


def test_repeat_init_changes_nothing(sb):
    sb.init()
    before = sb.snapshot()
    mtimes = {p: os.stat(sb.root / p).st_mtime_ns for p in before}
    data = sb.ok("init")
    assert data["result"]["created"] == []
    assert sb.snapshot() == before
    assert {p: os.stat(sb.root / p).st_mtime_ns for p in before} == mtimes


def test_repeat_init_preserves_custom_content(proj):
    map_path = proj.root / "BR" / "map.md"
    map_path.write_text(map_path.read_text().replace("- None yet.", "- Who signs off?"))
    proj.ok("allocate-id", "--category", "BR", "--title", "x")
    proj.doc("BR/BR-002-existing.md", "BR-002")
    cfg = proj.root / ".sdlc" / "config.md"
    cfg.write_text(cfg.read_text().replace("Demo", "Renamed"))
    before = proj.snapshot()
    proj.ok("init", "--project-name", "Other")
    assert proj.snapshot() == before
    assert "Who signs off?" in map_path.read_text()


def test_init_populates_maps_for_preexisting_documents(sb):
    sb.doc("BR/BR-001-first.md", "BR-001", title="First", purpose="Existing before init.")
    sb.init()
    assert "Existing before init." in (sb.root / "BR" / "map.md").read_text()


def test_init_uses_project_name_and_default_dirs(sb):
    sb.init()
    raw, _ = frontmatter.split((sb.root / ".sdlc" / "config.md").read_text())
    cfg = frontmatter.parse(raw)
    assert cfg["project_name"] == "Demo" and cfg["schema_version"] == 1
    assert cfg["directories"] == {"BR": "BR", "PR": "PR", "Stories": "Stories", "Artifacts": "Artifacts"}


def test_create_dir_first_use_creates_map_and_links_it(proj):
    data = proj.ok("create-dir", "--artifact", "design")
    assert data["result"]["directory_created"] is True
    assert (proj.root / "Artifacts" / "design" / "map.md").is_file()
    assert "(design/map.md)" in (proj.root / "Artifacts" / "map.md").read_text()
    code, out, _ = proj.run("validate")
    assert code == 0, out
    again = proj.ok("create-dir", "--artifact", "design")
    assert again["result"]["directory_created"] is False


def test_create_dir_other_kinds_and_bad_kind(proj):
    for kind in ("plans", "research", "tests"):
        proj.ok("create-dir", "--artifact", kind)
    text = (proj.root / "Artifacts" / "map.md").read_text()
    assert all(f"({k}/map.md)" in text for k in ("plans", "research", "tests"))


def test_create_dir_requires_initialised_project(sb):
    code, data, _ = sb.run("create-dir", "--artifact", "design")
    assert code == 2


def test_config_schema_is_validated(proj):
    cfg = proj.root / ".sdlc" / "config.md"
    cfg.write_text("---\nproject_name: ''\nschema_version: 2\ndirectories: [BR]\n---\n")
    _, data, _ = proj.run("validate")
    assert len(proj.diags(data, "bad-config")) == 3


def test_config_publishing_optional_and_checked(proj):
    cfg = proj.root / ".sdlc" / "config.md"
    text = cfg.read_text()
    cfg.write_text(text.replace("---\n\n#", "publishing:\n  github: {repo: o/r}\n---\n\n#", 1))
    code, _, _ = proj.run("validate")
    assert code == 0
    cfg.write_text(text.replace("---\n\n#", "publishing: nope\n---\n\n#", 1))
    code, data, _ = proj.run("validate")
    assert code == 1 and proj.diags(data, "bad-config")


def test_sdlc_directory_is_exempt_from_map_and_metadata_rules(proj):
    (proj.root / ".sdlc" / "notes.md").write_text("internal, no front matter")
    code, data, _ = proj.run("validate")
    assert code == 0 and data["result"]["summary"]["error"] == 0
    proj.run("update-map")
    assert not (proj.root / ".sdlc" / "map.md").exists()
    assert "sdlc" not in (proj.root / "map.md").read_text().lower().replace("sdlc:generated", "")


def template(name):
    return resources.files("sdlc").joinpath("templates", name).read_text(encoding="utf-8")


def test_init_installs_instruction_templates_in_project_root(sb):
    data = sb.init()
    for name in ("AGENTS.md", "CLAUDE.md"):
        assert name in data["result"]["created"]
        assert (sb.root / name).read_text() == template(name)
    text = (sb.root / "CLAUDE.md").read_text()
    assert "create-brd" in text and "In Review" in text
    assert template("AGENTS.md") == template("CLAUDE.md")


def test_instruction_files_are_not_documents_and_do_not_disturb_validation(sb):
    sb.init()
    code, data, _ = sb.run("validate")
    assert code == 0 and data["result"]["summary"] == {"error": 0, "warning": 0, "notice": 0}
    assert "AGENTS" not in (sb.root / "map.md").read_text() and "CLAUDE" not in (sb.root / "map.md").read_text()


def test_init_never_overwrites_existing_instructions(sb):
    (sb.root / "AGENTS.md").write_text("# My own rules\nNo SDLC talk here.\n")
    (sb.root / "CLAUDE.md").write_bytes(b"custom \xe2\x9c\x93 claude instructions")
    before = {n: (sb.root / n).read_bytes() for n in ("AGENTS.md", "CLAUDE.md")}
    data = sb.init()
    assert {"AGENTS.md", "CLAUDE.md"} <= set(data["result"]["existing"])
    assert not {"AGENTS.md", "CLAUDE.md"} & set(data["result"]["created"])
    assert {n: (sb.root / n).read_bytes() for n in before} == before


def test_init_creates_only_the_missing_instruction_file(sb):
    (sb.root / "AGENTS.md").write_text("mine")
    data = sb.init()
    assert "CLAUDE.md" in data["result"]["created"] and "AGENTS.md" in data["result"]["existing"]
    assert (sb.root / "AGENTS.md").read_text() == "mine" and (sb.root / "CLAUDE.md").read_text() == template("CLAUDE.md")


def test_init_leaves_symlinked_and_dangling_instruction_paths_alone(sb):
    (sb.root / "real.md").write_text("shared instructions")
    (sb.root / "AGENTS.md").symlink_to("real.md")
    (sb.root / "CLAUDE.md").symlink_to("does-not-exist.md")
    data = sb.init()
    assert {"AGENTS.md", "CLAUDE.md"} <= set(data["result"]["existing"])
    assert (sb.root / "AGENTS.md").is_symlink() and (sb.root / "CLAUDE.md").is_symlink()
    assert (sb.root / "real.md").read_text() == "shared instructions"
    assert not (sb.root / "does-not-exist.md").exists()


def test_repeat_init_is_idempotent_with_instruction_files(sb):
    sb.init()
    (sb.root / "CLAUDE.md").write_text((sb.root / "CLAUDE.md").read_text() + "\nProject-specific addition.\n")
    before = sb.snapshot()
    mtimes = {p: os.stat(sb.root / p).st_mtime_ns for p in before}
    data = sb.ok("init")
    assert data["result"]["created"] == [] and {"AGENTS.md", "CLAUDE.md"} <= set(data["result"]["existing"])
    assert sb.snapshot() == before
    assert {p: os.stat(sb.root / p).st_mtime_ns for p in before} == mtimes


def test_deleted_instruction_file_is_recreated_but_others_untouched(sb):
    sb.init()
    (sb.root / "AGENTS.md").unlink()
    (sb.root / "CLAUDE.md").write_text("edited")
    data = sb.ok("init")
    assert data["result"]["created"] == ["AGENTS.md"]
    assert (sb.root / "CLAUDE.md").read_text() == "edited"


def test_init_from_nested_directory_uses_project_root_for_instructions(sb, monkeypatch):
    sb.init()
    (sb.root / "AGENTS.md").unlink()
    monkeypatch.chdir(sb.root / "BR")
    sb.ok("init")
    assert (sb.root / "AGENTS.md").is_file() and not (sb.root / "BR" / "AGENTS.md").exists()


def test_templates_ship_as_package_data():
    import tomllib
    from pathlib import Path
    cfg = tomllib.loads((Path(__file__).resolve().parents[2] / "pyproject.toml").read_text())
    assert cfg["tool"]["setuptools"]["package-data"]["sdlc"] == ["templates/*.md"]
