"""Command-line interface: sdlc <command> [--root DIR] [--json]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, ids, init_cmd, maps, publish, query, status, validate
from .model import ARTIFACT_SUBDIRS, DOC_CATEGORIES, DOC_STATUSES, Diagnostic, Outcome
from .project import Project, find_root

JSON_SCHEMA_VERSION = 1


def _common() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--root", metavar="DIR", help="project root (default: nearest ancestor containing .sdlc/)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return p


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sdlc", description="Deterministic helper CLI for the SDLC Skill library.")
    parser.add_argument("--version", action="version", version=f"sdlc {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    common = _common()

    p = sub.add_parser("init", parents=[common], help="idempotently create the standard project structure (and AGENTS.md/CLAUDE.md if missing)")
    p.add_argument("--project-name", help="project name for a new .sdlc/config.md (default: directory name)")

    p = sub.add_parser("allocate-id", parents=[common], help="reserve the next document or requirement ID")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--category", choices=DOC_CATEGORIES)
    g.add_argument("--requirement", metavar="DOC-ID", help="allocate the next requirement ID in this document")
    p.add_argument("--title", help="document title (used to compute the target path)")

    p = sub.add_parser("retire-id", parents=[common], help="tombstone a document or requirement ID")
    p.add_argument("id")
    p.add_argument("--replaced-by", metavar="ID")
    p.add_argument("--note")

    p = sub.add_parser("create-dir", parents=[common], help="create an Artifacts subdirectory and its map on first use")
    p.add_argument("--artifact", required=True, choices=sorted(ARTIFACT_SUBDIRS))

    p = sub.add_parser("update-map", parents=[common], help="regenerate the generated region of map.md files")
    p.add_argument("directory", nargs="?", help="managed directory (default: every map)")

    p = sub.add_parser("list", parents=[common], help="list documents with their metadata")
    p.add_argument("--category", choices=DOC_CATEGORIES)
    p.add_argument("--status", choices=DOC_STATUSES)

    p = sub.add_parser("references", parents=[common], help="outgoing and incoming references for an ID")
    p.add_argument("id")

    p = sub.add_parser("find-overlaps", parents=[common], help="rank existing documents that may overlap a proposed one")
    p.add_argument("--category", required=True, choices=DOC_CATEGORIES)
    p.add_argument("--title", required=True)
    p.add_argument("--purpose")
    p.add_argument("--covers", nargs="+", default=[], metavar="ID", help="search hint: requirement or document IDs the new document relates to (Story front matter covers is requirement IDs only)")

    sub.add_parser("status", parents=[common], help="read-only progress snapshot: health, inventory, delivery, traceability, attention")

    p = sub.add_parser("publish-preview", parents=[common],
                       help="render the exact GitHub Issue(s) that would be created for the named Stories (offline; never mutates)")
    p.add_argument("stories", nargs="*", metavar="STORY-ID", help="Stories to publish (none are selected by default)")

    p = sub.add_parser("publish-apply", parents=[common],
                       help="create the previewed GitHub Issue(s); refuses unless --confirm-digest matches a fresh preview")
    p.add_argument("stories", nargs="*", metavar="STORY-ID")
    p.add_argument("--confirm-digest", metavar="DIGEST", help="the digest shown by publish-preview, supplied only after explicit human confirmation")

    sub.add_parser("validate", parents=[common], help="check structure, metadata, IDs, links, maps and traceability")
    return parser


def _envelope(command: str, out: Outcome) -> dict:
    return {
        "schema_version": JSON_SCHEMA_VERSION,
        "command": command,
        "ok": out.exit_code == 0,
        "exit_code": out.exit_code,
        "result": out.result,
        "diagnostics": [d.to_dict() for d in out.diagnostics],
    }


def _human(command: str, out: Outcome) -> str:
    r = out.result
    lines: list[str] = []
    if command == "init":
        if "root" in r:
            lines.append(f"Initialized SDLC project at {r['root']}")
            lines += [f"  created:  {p}" for p in r["created"]] + [f"  existing: {p}" for p in r["existing"]]
    elif command == "allocate-id" and r:
        lines.append(r["id"])
        if r.get("path"):
            lines.append(f"path: {r['path']}")
        elif r.get("directory"):
            lines.append(f"directory: {r['directory']}")
    elif command == "retire-id" and r:
        lines.append(f"Retired {r['id']}" + (f" (replaced by {r['replaced_by']})" if r.get("replaced_by") else ""))
    elif command == "create-dir" and r:
        lines.append(f"{'Created' if r['directory_created'] else 'Found'} {r['directory']}/")
        lines += [f"  {k}: {v}" for k, v in r.items() if k.endswith("_map")]
    elif command == "update-map":
        for state in ("created", "updated", "unchanged", "blocked"):
            lines += [f"{state}: {p}" for p in r.get(state, [])]
    elif command == "list":
        for d in r.get("documents", []):
            extra = f"  [{d['delivery_status']}]" if d.get("delivery_status") else ""
            lines.append(f"{d['id']:<10} {d['status']:<11} {d['title']}{extra}  ({d['path']})")
        lines.append(f"{r.get('count', 0)} document(s)")
    elif command == "references" and r:
        lines.append(f"{r['id']} ({r['kind']}, {r['state']})" + (f" — {r['title']}" if r.get("title") else ""))
        if r.get("defined_in"):
            lines.append(f"defined in: {r['defined_in']['id']} ({r['defined_in']['path']})")
        lines.append("outgoing:")
        for o in r["outgoing"]:
            tgt = (o["target"] or {}).get("id") or (o["target"] or {}).get("path") or ", ".join(o["requirements"])
            lines.append(f"  {o['relationship']}: {tgt}")
        lines.append("incoming:")
        for i in r["incoming"]:
            reqs = f" ({', '.join(i['requirements'])})" if i["requirements"] else ""
            lines.append(f"  {i['relationship']}: {i['source']['id']}{reqs}")
    elif command == "find-overlaps" and r:
        if not r["candidates"]:
            lines.append("No plausible overlaps found.")
        for c in r["candidates"]:
            lines.append(f"{c['level']:<8} {c['score']:.2f}  {c['id']} {c['title']}  ({c['path']})")
            lines += [f"           - {reason}" for reason in c["reasons"]]
        if r["candidates"]:
            lines.append("Ask the user whether to revise/extend an existing document or create a new one.")
    elif command == "status" and r:
        lines += _human_status(r)
    elif command in ("publish-preview", "publish-apply") and r:
        lines += _human_publish(command, r)
    elif command == "validate" and r:
        s = r["summary"]
        lines.append(f"{r['documents']} document(s): {s['error']} error(s), {s['warning']} warning(s), {s['notice']} notice(s)")
    return "\n".join(lines)


def _human_status(r: dict) -> list[str]:
    h = r["health"]
    s = h["summary"]
    lines = ["# Project status", "", "## Project health",
             f"- Validation: {'OK' if h['ok'] else 'ERRORS'} — {s['error']} error(s), {s['warning']} warning(s), {s['notice']} notice(s) "
             f"across {h['documents']} document(s)"]
    if h["stale_maps"]:
        lines.append(f"- Stale or missing maps: {', '.join(h['stale_maps'])}")
    lines += [f"- Broken reference: {b['message']} ({b['path']})" for b in h["broken_references"]]
    lines += ["", "## Document inventory"]
    for cat, row in r["inventory"].items():
        if row["total"]:
            parts = [f"{n} {name}" for name, n in row["by_status"].items() if n] + ([f"{row['invalid']} invalid"] if row["invalid"] else [])
            lines.append(f"- {cat}: {row['total']} ({', '.join(parts)})")
        else:
            lines.append(f"- {cat}: none")
    lines += ["", "## Story delivery"]
    for name, items in r["delivery"].items():
        lines.append(f"- {name}: {len(items)}" + (f" ({', '.join(i['id'] for i in items)})" if items else ""))
    t = r["traceability"]
    lines += ["", "## Traceability",
              f"- Uncovered PR requirements (notice): {', '.join(t['uncovered_requirements']) or 'none'}",
              f"- Standalone Stories, covers [] (notice): {', '.join(t['standalone_stories']) or 'none'}",
              f"- Invalid references: {len(t['invalid_references']) or 'none'}",
              f"- Unresolved acceptance behavior (TBD): {', '.join(t['unresolved_tbd']) or 'none'}",
              "", "## Needs attention / next actions"]
    lines += [f"- [{a['kind']}] {a['id'] or ''} {a['message']}".replace("  ", " ") for a in r["attention"]] or ["- Nothing needs attention."]
    if r["empty"]:
        lines += ["", "No documents yet: start with create-brd, create-prd or create-stories."]
    return lines


def _human_publish(command: str, r: dict) -> list[str]:
    lines = [f"Target: {r['provider']} {r['repository']}   (access is checked only when applying)"]
    for s in r["stories"]:
        lines += ["", f"=== {s['id']} — {s['action'].upper()} ==="]
        if s["action"] == "blocked":
            lines.append(f"blocked: {', '.join(s['blockers'])}")
            continue
        lines += [f"Title: {s['issue_title']}", "Labels: none", "Body:", ""] + [f"    {ln}" for ln in s["issue_body"].rstrip("\n").split("\n")]
        if s["known_publication"]:
            k = s["known_publication"]
            lines.append(f"Known publication: {k['repository']}{k['issue']} {k.get('url') or ''}".rstrip())
        for o in s.get("other_publications", []):
            lines.append(f"Also published elsewhere: {o['provider']}:{o['repository']}{o['issue']} (does not block this repository)")
    lines += ["", f"Will create: {', '.join(r['will_create']) or 'nothing'}"]
    if r.get("digest"):
        lines.append(f"Digest: {r['digest']}")
    if command == "publish-preview":
        lines.append("Preview only — no external mutation was made. Publish only after explicit human confirmation.")
    else:
        for o in r.get("outcomes", []):
            detail = o.get("url") or o.get("issue") or o.get("reason") or o.get("error") or ""
            lines.append(f"{o['id']}: {o['outcome']} {detail}".rstrip())
        lines.append(f"External mutations: {r['mutations']}")
    return lines


def _emit(command: str, out: Outcome, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_envelope(command, out), indent=2, ensure_ascii=False))
        return
    body = _human(command, out)
    if command == "validate":
        for d in out.diagnostics:
            print(d.human())
        print(body)
        return
    if body:
        print(body)
    for d in out.diagnostics:
        print(d.human(), file=sys.stderr)


def _resolve_root(args) -> tuple[Path | None, Diagnostic | None]:
    if args.root:
        root = Path(args.root).resolve()
        if args.command == "init":
            return root, None
        if not (root / ".sdlc").is_dir():
            return None, Diagnostic("error", "no-project", f"{root} is not an SDLC project (no .sdlc/); run 'sdlc init'")
        return root, None
    found = find_root(Path.cwd())
    if found:
        return found, None
    if args.command == "init":
        return Path.cwd(), None
    return None, Diagnostic("error", "no-project", "no .sdlc/ found in this or any parent directory; run 'sdlc init'")


def _update_map(project: Project, directory: str | None) -> Outcome:
    only = None
    if directory is not None:
        target = Path(directory)
        target = (target if target.is_absolute() else Path.cwd() / target).resolve()
        only = next((s for s in maps.specs(project) if s.directory.resolve() == target), None)
        if only is None:
            return Outcome(2, diagnostics=[Diagnostic("error", "bad-directory", f"{directory} is not a managed directory with a map")])
    result, diags = maps.update_maps(project, only)
    return Outcome(1 if diags else 0, result, diags)


def run(args) -> Outcome:
    root, problem = _resolve_root(args)
    if problem:
        return Outcome(2, diagnostics=[problem])
    if args.command == "init":
        return init_cmd.init_project(root, args.project_name)
    project = Project.open(root)
    if args.command == "allocate-id":
        if args.requirement:
            return ids.allocate_requirement(project, args.requirement)
        return ids.allocate_document(project, args.category, args.title)
    if args.command == "retire-id":
        return ids.retire(project, args.id, args.replaced_by, args.note)
    if args.command == "create-dir":
        return init_cmd.create_artifact_dir(project, args.artifact)
    if args.command == "update-map":
        return _update_map(project, args.directory)
    if args.command == "list":
        return query.list_documents(project, args.category, args.status)
    if args.command == "references":
        return query.references(project, args.id)
    if args.command == "find-overlaps":
        return query.find_overlaps(project, args.category, args.title, args.purpose, args.covers)
    if args.command == "status":
        return status.build_status(project)
    if args.command == "publish-preview":
        return publish.build_preview(project, args.stories)
    if args.command == "publish-apply":
        return publish.apply_publication(project, args.stories, args.confirm_digest)
    return validate.validate(project)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out = run(args)
    _emit(args.command, out, args.json)
    return out.exit_code
