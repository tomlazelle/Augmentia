#!/usr/bin/env python3
"""Generate parity/yaml-expectations.json from the PYTHON ORACLE (sdlc.frontmatter / PyYAML). A frozen M7 asset: the Node
YAML layer must reproduce these results; it is never regenerated from Node."""

import datetime
import json
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LIB))
from sdlc import frontmatter  # noqa: E402
from sdlc.project import DEFAULT_DIRECTORIES, SCHEMA_VERSION  # noqa: E402

PARSE_INPUTS = [
    "", "   ", "# only a comment", "~", "null", "a: 1", "a:", "a: ~", "a: null", "a: ''", 'a: ""', "a: yes", "a: no", "a: on", "a: off",
    "a: Yes", "a: NO", "a: y", "a: n", "a: true", "a: True", "a: FALSE", "a: 0", "a: 007", "a: 0o17", "a: 0x1f", "a: 0b101", "a: 1_000",
    "a: 1:30", "a: 1:30:15", "a: +5", "a: -5", "a: 08", "a: 09", "a: 1.5", "a: 1e3", "a: 1.0e+3", "a: 1.0E-3", "a: .5", "a: 5.", "a: .inf", "a: -.inf",
    "a: 2026-09-29", "a: 2026-9-9", "a: 2026-09-29 10:00:00", "a: 2026-09-29T10:00:00Z", "a: 2026-09-29T10:00:00.5+02:00", "a: 2026-09-29 10:00:00 -5",
    "a: 2026-02-30", "a: 2026-13-01", "a: 0000-01-01", "a: 2026-09-29T25:00:00Z", "a: '2026-09-29'", 'a: "2026-09-29"',
    "a: hello world", "a: 'it''s'", 'a: "a\\nb"', 'a: "tab\\there"', "a: a: b", "a: b: c", "a: [1, 2, three]", "a: [", "a: {k: v, n: 1}", "a: {k: v", "a: [x, [y, z]]",
    "a: |\n  line1\n  line2\n", "a: >\n  folded\n  text\n", "a: multi\n  line plain\n  scalar", "a: |-\n  strip\n", "a: |+\n  keep\n\n",
    "- a\n- b", "just a scalar", "- a: 1\n  b: 2", "a: &x {k: v}\nb: *x", "base: &b {x: 1, y: 2}\nd:\n  <<: *b\n  y: 3", "m:\n  <<: [{a: 1}, {a: 2, b: 3}]\n  c: 4",
    "a: <<", "a: =", "a: 1\na: 2", "1: x\n2: y", "true: x", "~: x", "2026-09-29: x", "? complex\n: v", "? [a, b]\n: v",
    "a: !!str 123", "a: !!int '7'", "a: !!float 1", "a: !!bool yes", "a: !!null x", "a: !foo bar", "a: !!python/object:os.system x", "a: !!binary aGk=", "a: !!set {x, y}",
    "a: \"unterminated", "a: 'unterminated", "a:\tb", "\ta: b", "a: b\n c: d", "a: [1, 2\nb: 3", "key: value\n  bad indent: 1", "a: *undefined", "a: &x 1\nb: *x",
    "id: US-001\ntitle: \"Hello: world\"\npurpose: One line.\nstatus: Draft\ncreated: 2026-09-01\nupdated: 2026-09-29\ndelivery_status: Not Started\ncovers: [PR-001-R001, PR-001-R002]",
    "id: BR-001\ncovers: []\nnotes: {}\nempty:\nflag: yes\ncount: 3", "title: 日本語 café\npurpose: naïve ünï", "publishing:\n  provider: github\n  repository: owner/name",
    "a: 'x'\nb: \"y\"\nc: z # trailing comment", "a: x #notcomment", "a: [a,b,]", "a: {a: 1,}", "a: \"\\u00e9\"", "a: '\u00a0'", "a: b\u2028c",
    "a: b\tc", "a: 'x\ty'", 'a: "x\ty"', "a: x # c\td", "k:\n\t- x", "k:\n  - x\n  -\ty", "- \tx", "a: |\n  x:\ty\n", "a:\t", "a: [1,\t2]", "a: {k:\tv}", "a:\n  b:\tc",
    "a: b\x85c", 'a: "x\u2028y"', "a: x\n\u2028b: 1", "a: x\u2029y", "a: |\n  x\u2028y\n", "a: x\u2028 y", "a: 'x\u2028y'",
]

NAMES = [
    "Demo", "my-project", "my_project", "tasklog", "123", "007", "1.5", "0x10", "1e3", "true", "True", "yes", "No", "null", "Null", "~", "", "=", "<<", "2026-01-01", "2026-01-01 10:00:00",
    "Hello World", "hello  two  spaces", "a: b", "a:b", "a #b", "a# b", "#hash", "x,y", "x, y", "{a}", "[a]", "a{b}", "- x", "-x", "- ", "-", "?x", "? x", ":x", ": x", "!x", "&x", "*x", "|x", ">x", "%x", "@x", "`x", "'", "''", '"',
    "it's", "O'Reilly's", 'say "hi"', "both ' and \"", "back\\slash", "caf\u00e9", "\u65e5\u672c\u8a9e", "emoji \U0001F600 here", "nbsp\u00a0here", "\u00a0lead", " lead", "trail ", "  both  ", "tab\there", "line\nbreak", "two\n\nbreaks", "\nlead", "trail\n",
    "---", "--- x", "...", "...x", "x" * 100, ("word " * 30).strip(), ("ab " * 40).strip(), "a" * 79, "a" * 80 + " b", ("long name with spaces " * 8).strip(), "a\x07b", "a\u0085b", "a\ufeffb", "\x00", "a\u2028b",
    "project.name", "project/name", "project name", "UPPER", "MiXeD-1", "name: with colon and spaces", "name with # hash", "[bracket start", "{brace start", "name]", "key: [x]",
]


def py_value(v):
    if isinstance(v, datetime.datetime):
        return {"$datetime": repr(v)}
    if isinstance(v, datetime.date):
        return {"$date": v.isoformat()}
    if isinstance(v, float):
        return {"$float": "nan" if v != v else ("inf" if v == float("inf") else "-inf" if v == float("-inf") else repr(v))}
    if isinstance(v, bytes):
        return {"$bytes": v.hex()}
    if isinstance(v, (set, frozenset)):
        return {"$set": sorted(str(x) for x in v)}
    if isinstance(v, dict):
        return {str(k): py_value(x) for k, x in v.items()}
    if isinstance(v, list):
        return [py_value(x) for x in v]
    return v


def main() -> None:
    parses = []
    for raw in PARSE_INPUTS:
        try:
            parses.append({"input": raw, "ok": py_value(frontmatter.parse(raw))})
        except ValueError as exc:
            parses.append({"input": raw, "error": str(exc)})
    dumps = []
    for name in NAMES:
        data = {"project_name": name, "schema_version": SCHEMA_VERSION, "directories": dict(DEFAULT_DIRECTORIES)}
        dumps.append({"name": name, "text": frontmatter.dump(data)})
    out = {"source": "python-1.0.0rc1 sdlc.frontmatter / PyYAML", "parse": parses, "dump": dumps}
    (LIB / "parity" / "yaml-expectations.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(parses)} parse cases ({sum('error' in p for p in parses)} errors), {len(dumps)} dump cases")


if __name__ == "__main__":
    main()
